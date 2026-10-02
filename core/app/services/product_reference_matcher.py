"""
Deterministic Product Reference Matcher Service.

Performs deterministic multi-tier matching of product titles and attributes
against the Core-owned reference catalog (product_reference_models & aliases).

Match Tiers:
- Tier 1: Exact unique normalized alias (confidence = 1.00)
- Tier 2: Brand + exact model token (confidence >= 0.95, no ambiguity)
- Tier 3: Canonical normalized signature (confidence >= 0.90)

Ambiguity Safety:
- Longest / specific model wins (e.g. 1320n over 1320, P2040dn over P2040)
- Token boundaries strictly respected
- Multi-candidate ambiguity -> NO AUTO MATCH (status: needs_review)
- Bundles listing multiple models -> NO AUTO MATCH
- Spare parts / consumables matching full device -> NO AUTO MATCH
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app import models


# Part / Consumable indicators that must prevent a full device reference model match
PART_KEYWORDS = {
    "тонер", "картридж", "печка", "термоблок", "фьюзер", "чип",
    "крышка", "шарниры", "редуктор", "плата", "лазер", "ролик",
    "вал", "узел", "шлейф", "донор", "запчасти", "разбор",
    "корпус", "кулер", "вентилятор", "петли", "матрица",
    "чернила", "краска", "адаптер", "блок питания", "лоток"
}

RE_PART_KEYWORDS = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in PART_KEYWORDS) + r")\b",
    re.IGNORECASE
)


# Common brand synonyms / normalization
BRAND_SYNONYMS: Dict[str, str] = {
    "hp": "hp",
    "hewlett-packard": "hp",
    "hewlett packard": "hp",
    "xerox": "xerox",
    "canon": "canon",
    "samsung": "samsung",
    "kyocera": "kyocera",
    "lenovo": "lenovo",
    "asus": "asus",
    "acer": "acer",
    "dell": "dell",
    "brother": "brother",
    "pantum": "pantum",
    "epson": "epson",
    "seagate": "seagate",
    "western digital": "western digital",
    "wd": "western digital",
    "toshiba": "toshiba",
    "kingston": "kingston",
    "gigabyte": "gigabyte",
    "msi": "msi",
    "apple": "apple",
}


def normalize_for_matching(text: Optional[str]) -> str:
    """
    Normalize text for robust deterministic matching:
    - Unicode NFKC normalization
    - casefold (case-insensitive)
    - replace ё with е
    - normalize quotes, brackets, slashes, hyphens
    - collapse multiple spaces
    - preserve significant alphanumeric model tokens
    """
    if not text:
        return ""
    t = str(text)
    t = unicodedata.normalize("NFKC", t).casefold()
    t = t.replace("ё", "е")
    # Replace common separators/punctuation with spaces, preserving hyphens within tokens
    t = re.sub(r"[\.,;:!\?\"\'`«»\(\)\[\]\{\}<>|+=_\*~#@]", " ", t)
    # Replace slashes with spaces to isolate model tokens (e.g. 1018/1160/1320 -> 1018 1160 1320)
    t = re.sub(r"[/\\&]", " ", t)
    # Collapse multiple hyphens or spaces
    t = re.sub(r"-+", "-", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def extract_tokens(text: Optional[str]) -> List[str]:
    """Extract individual alphanumeric tokens from normalized text."""
    norm = normalize_for_matching(text)
    if not norm:
        return []
    # Split on whitespace and hyphens
    raw_tokens = re.findall(r"[a-z0-9\u0400-\u04ff-]+", norm)
    tokens = []
    for tok in raw_tokens:
        tok_clean = tok.strip("-")
        if tok_clean:
            tokens.append(tok_clean)
            # Also add parts of hyphenated token if present (e.g. "p2040-dn" -> "p2040", "dn")
            if "-" in tok_clean:
                parts = [p for p in tok_clean.split("-") if p]
                tokens.extend(parts)
    return tokens


def generate_stable_key(brand: str, model: str) -> str:
    """
    Generate a stable unique key for a reference model:
    Format: {brand}|{normalized_model}
    Example: hp|laserjet-1320, xerox|versalink-b405
    """
    b_norm = normalize_for_matching(brand).replace(" ", "-")
    m_norm = normalize_for_matching(model).replace(" ", "-")
    b_norm = re.sub(r"[^a-z0-9\u0400-\u04ff-]", "", b_norm)
    m_norm = re.sub(r"[^a-z0-9\u0400-\u04ff-]", "", m_norm)
    return f"{b_norm}|{m_norm}".strip("-|")


def has_token_boundary_phrase(phrase: str, text: str) -> bool:
    """
    Check if a normalized multi-word phrase occurs in normalized text
    with strict word/token boundaries.
    """
    p_norm = normalize_for_matching(phrase)
    t_norm = normalize_for_matching(text)
    if not p_norm or not t_norm:
        return False
    # Use word boundaries around escaped phrase
    pattern = r"(?<![a-z0-9\u0400-\u04ff])" + re.escape(p_norm) + r"(?![a-z0-9\u0400-\u04ff])"
    return bool(re.search(pattern, t_norm))


DEVICE_KEYWORDS = {
    "принтер", "мфу", "ноутбук", "моноблок", "системный блок", "монитор"
}


def is_part_or_consumable(text: Optional[str]) -> bool:
    """Check if title or text indicates a part, spare, or consumable rather than the full device."""
    if not text:
        return False
    norm = normalize_for_matching(text)
    has_part = bool(RE_PART_KEYWORDS.search(norm))
    if not has_part:
        return False

    # Check if primary subject is an explicit whole device
    has_whole_device = any(re.search(r"\b" + re.escape(dk) + r"\b", norm) for dk in DEVICE_KEYWORDS)
    if has_whole_device:
        # If it starts with part keyword or has "для принтера", it's a part/consumable
        part_prefix_match = re.search(r"^\s*(тонер|картридж|печка|термоблок|фьюзер|чип|крышка|шарниры|редуктор|плата|лазер|ролик|вал|узел|шлейф|туба|петли|матрица|чернила|краска)\b", norm)
        if part_prefix_match:
            return True
        if re.search(r"\bдля\s+(принтера|мфу|ноутбука|монитора)\b", norm):
            return True

        # Whole device sold for parts/restoration (e.g. "Лазерный принтер ... на запчасти") is still a device
        return False

    return True


RE_BUNDLE_PATTERN = re.compile(
    r"(\b(партия|партии|партией|комплект|комплекты|комплектом|оптом|набором|несколько\s+штук|лот)\b|"
    r"(\b\d{3,5}\s*/\s*\d{3,5}\b)|"
    r"\b(принтеры|ноутбуки|мониторы|компьютеры|мфу)\b\s*(оптом|\d+\s*шт|[,\+]))",
    re.IGNORECASE
)


def is_bundle_title(text: Optional[str]) -> bool:
    """Check if title indicates a bundle, lot, or multi-device batch."""
    if not text:
        return False
    # Check normalized text preserving slashes and punctuation
    t = unicodedata.normalize("NFKC", str(text)).casefold().replace("ё", "е")
    return bool(RE_BUNDLE_PATTERN.search(t))



def extract_model_roots(model_str: str) -> List[str]:
    """Extract root numeric/alphanumeric tokens, stripping variant suffixes like dn, dw, s, n, d."""
    roots = []
    tokens = extract_tokens(model_str)
    for tok in tokens:
        # e.g. p2040dn -> p2040, t480s -> t480, 1320n -> 1320
        m = re.match(r"^([a-z]*\d+)[a-z]+$", tok)
        if m:
            roots.append(m.group(1))
    return roots


@dataclass
class MatchCandidate:
    reference_model_id: int
    canonical_name: str
    brand: str
    model: str
    tier: str
    confidence: float
    matched_term: str
    score: float
    specificity: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_model_id": self.reference_model_id,
            "canonical_name": self.canonical_name,
            "brand": self.brand,
            "model": self.model,
            "tier": self.tier,
            "confidence": round(self.confidence, 4),
            "matched_term": self.matched_term,
            "score": round(self.score, 4),
        }


@dataclass
class MatchResult:
    matched: bool
    reference_model_id: Optional[int] = None
    canonical_name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    method: Optional[str] = None
    confidence: Optional[float] = None
    status: str = "ok"  # "matched", "needs_review", "no_match"
    reason: Optional[str] = None
    reference_model: Optional[Any] = None
    candidates: List[MatchCandidate] = field(default_factory=list)
    would_fill: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched": self.matched,
            "reference_model_id": self.reference_model_id,
            "canonical_name": self.canonical_name,
            "brand": self.brand,
            "model": self.model,
            "method": self.method,
            "confidence": round(self.confidence, 4) if self.confidence is not None else None,
            "status": self.status,
            "reason": self.reason,
            "candidates": [c.to_dict() for c in self.candidates],
            "would_fill": self.would_fill,
        }


def find_reference_candidates(
    db: Session,
    title: str,
    brand_hint: Optional[str] = None,
    model_hint: Optional[str] = None,
    active_only: bool = True,
) -> List[MatchCandidate]:
    """
    Search reference models and aliases for potential matches across all 3 tiers.
    """
    title_norm = normalize_for_matching(title)
    if not title_norm:
        return []

    tokens = extract_tokens(title_norm)
    token_set = set(tokens)

    # Fetch active reference models with their aliases
    q = db.query(models.ProductReferenceModel)
    if active_only:
        q = q.filter(models.ProductReferenceModel.active == True)
    ref_models = q.all()

    candidates: List[MatchCandidate] = []
    seen_model_ids: Set[int] = set()

    for ref in ref_models:
        ref_b_norm = normalize_for_matching(ref.brand)
        ref_m_norm = normalize_for_matching(ref.model)
        ref_canon_norm = normalize_for_matching(ref.canonical_name)

        # -------------------------------------------------------------
        # Tier 1: Exact alias matching
        # -------------------------------------------------------------
        best_alias_match: Optional[Tuple[str, int]] = None
        for alias_obj in ref.aliases:
            if active_only and not alias_obj.active:
                continue
            a_norm = alias_obj.normalized_alias or normalize_for_matching(alias_obj.alias)
            if not a_norm:
                continue
            if has_token_boundary_phrase(a_norm, title_norm):
                # Longer alias = higher specificity
                alias_len = len(a_norm)
                if best_alias_match is None or alias_len > best_alias_match[1]:
                    best_alias_match = (alias_obj.alias, alias_len)

        if best_alias_match:
            cand = MatchCandidate(
                reference_model_id=ref.id,
                canonical_name=ref.canonical_name,
                brand=ref.brand,
                model=ref.model,
                tier="tier1_exact_alias",
                confidence=1.00,
                matched_term=best_alias_match[0],
                score=100.0 + best_alias_match[1],
                specificity=best_alias_match[1],
            )
            candidates.append(cand)
            seen_model_ids.add(ref.id)
            continue

        # -------------------------------------------------------------
        # Tier 3: Canonical signature phrase matching
        # -------------------------------------------------------------
        if has_token_boundary_phrase(ref_canon_norm, title_norm):
            cand = MatchCandidate(
                reference_model_id=ref.id,
                canonical_name=ref.canonical_name,
                brand=ref.brand,
                model=ref.model,
                tier="tier3_canonical_signature",
                confidence=0.92,
                matched_term=ref.canonical_name,
                score=90.0 + len(ref_canon_norm),
                specificity=len(ref_canon_norm),
            )
            candidates.append(cand)
            seen_model_ids.add(ref.id)
            continue

        # -------------------------------------------------------------
        # Tier 2: Brand + exact model token
        # -------------------------------------------------------------
        # Brand check: brand_hint or brand in title
        brand_match = False
        if brand_hint and normalize_for_matching(brand_hint) == ref_b_norm:
            brand_match = True
        elif has_token_boundary_phrase(ref_b_norm, title_norm):
            brand_match = True
        elif ref_b_norm in BRAND_SYNONYMS:
            canon_syn = BRAND_SYNONYMS[ref_b_norm]
            if has_token_boundary_phrase(canon_syn, title_norm):
                brand_match = True

        if brand_match:
            # Model token check
            model_tokens = extract_tokens(ref.model)
            # A model token is significant if it contains digits or is a distinct model identifier
            # e.g. "1320", "p2040dn", "t480", "b405", "1020"
            if has_token_boundary_phrase(ref_m_norm, title_norm):
                cand = MatchCandidate(
                    reference_model_id=ref.id,
                    canonical_name=ref.canonical_name,
                    brand=ref.brand,
                    model=ref.model,
                    tier="tier2_brand_model_exact",
                    confidence=0.98,
                    matched_term=f"{ref.brand} {ref.model}",
                    score=95.0 + len(ref_m_norm),
                    specificity=len(ref_m_norm),
                )
                candidates.append(cand)
                seen_model_ids.add(ref.id)
            else:
                # Check if all significant model tokens (length >= 3 or containing digits) are present
                sig_tokens = [t for t in model_tokens if len(t) >= 3 or any(c.isdigit() for c in t)]
                if sig_tokens and all(tok in token_set for tok in sig_tokens):
                    cand = MatchCandidate(
                        reference_model_id=ref.id,
                        canonical_name=ref.canonical_name,
                        brand=ref.brand,
                        model=ref.model,
                        tier="tier2_brand_model_tokens",
                        confidence=0.95,
                        matched_term=f"{ref.brand} {' '.join(sig_tokens)}",
                        score=92.0 + len(" ".join(sig_tokens)),
                        specificity=len(" ".join(sig_tokens)),
                    )
                    candidates.append(cand)
                    seen_model_ids.add(ref.id)
                else:
                    # Check base model roots (e.g. p2040 from p2040dn or t480 from t480s)
                    roots = extract_model_roots(ref.model)
                    matched_roots = [r for r in roots if r in token_set]
                    if matched_roots:
                        cand = MatchCandidate(
                            reference_model_id=ref.id,
                            canonical_name=ref.canonical_name,
                            brand=ref.brand,
                            model=ref.model,
                            tier="tier2_base_model_partial",
                            confidence=0.85,
                            matched_term=f"{ref.brand} {matched_roots[0]}",
                            score=80.0 + len(matched_roots[0]),
                            specificity=len(matched_roots[0]),
                        )
                        candidates.append(cand)
                        seen_model_ids.add(ref.id)

    # Sort candidates by score descending
    candidates.sort(key=lambda c: (c.confidence, c.specificity, c.score), reverse=True)
    return candidates


def match_product(
    db: Session,
    title: str,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    description: Optional[str] = None,
    existing_category_name: Optional[str] = None,
    active_only: bool = True,
) -> MatchResult:
    """
    Main entry point for deterministic product matching against reference catalog.
    Evaluates candidates, enforces ambiguity and part safety, and returns MatchResult.
    """
    if not title or not str(title).strip():
        return MatchResult(
            matched=False,
            status="no_match",
            reason="empty_title"
        )

    # Check Part/Consumable Safety:
    # If the product title explicitly describes a spare part, cartridge, or consumable:
    # do NOT auto-match a device reference model!
    if is_part_or_consumable(title):
        return MatchResult(
            matched=False,
            status="needs_review",
            reason="part_or_consumable_not_whole_device"
        )

    # Check Bundle Title:
    # Titles describing multi-device bundles or batches must not auto-match a single reference model
    if is_bundle_title(title):
        return MatchResult(
            matched=False,
            status="needs_review",
            reason="bundle_title_detected"
        )

    candidates = find_reference_candidates(
        db=db,
        title=title,
        brand_hint=brand,
        model_hint=model,
        active_only=active_only,
    )

    if not candidates:
        return MatchResult(
            matched=False,
            status="no_match",
            reason="no_candidates_found"
        )

    # Check Ambiguous Base Model Variants (e.g. "Kyocera P2040" when both P2040dn and P2040dw exist)
    if len(candidates) >= 2 and all(c.tier == "tier2_base_model_partial" for c in candidates):
        return MatchResult(
            matched=False,
            status="needs_review",
            reason="ambiguous_candidates_missing_variant_suffix",
            candidates=candidates,
        )


    # Ambiguity check 1: Multiple competing candidates with equal top tier & high score
    top_candidate = candidates[0]

    # Filter candidates with the same or very close top confidence
    competing = [
        c for c in candidates
        if c.reference_model_id != top_candidate.reference_model_id
        and abs(c.confidence - top_candidate.confidence) < 0.02
        and abs(c.specificity - top_candidate.specificity) <= 1
    ]

    if competing:
        # Check if one is strictly a longer/more specific model variant
        # e.g., "Kyocera Ecosys P2040dn" vs "Kyocera Ecosys P2040"
        top_name_norm = normalize_for_matching(top_candidate.model)
        comp_name_norm = normalize_for_matching(competing[0].model)
        if top_name_norm in comp_name_norm or comp_name_norm in top_name_norm:
            # Check if title strictly contains the longer one
            if len(comp_name_norm) > len(top_name_norm) and has_token_boundary_phrase(comp_name_norm, title):
                top_candidate = competing[0]
                competing = [c for c in candidates if c.reference_model_id != top_candidate.reference_model_id and c.confidence == top_candidate.confidence]
            elif len(top_name_norm) > len(comp_name_norm) and has_token_boundary_phrase(top_name_norm, title):
                competing = []

        if competing:
            return MatchResult(
                matched=False,
                status="needs_review",
                reason="ambiguous_multiple_candidates",
                candidates=candidates
            )

    # Ambiguity check 2: Bundle title mentioning multiple distinct model numbers
    # e.g., "HP LaserJet 1018/1160/1320/P2015"
    if len(candidates) > 1:
        distinct_model_ids = {c.reference_model_id for c in candidates if c.confidence >= 0.90}
        if len(distinct_model_ids) > 1:
            # If multiple models match independently with high confidence, verify if title is a bundle
            matched_terms = [c.matched_term for c in candidates if c.confidence >= 0.90]
            # If title contains multiple distinct matched terms
            present_terms = [t for t in matched_terms if has_token_boundary_phrase(t, title)]
            if len(set(present_terms)) > 1:
                return MatchResult(
                    matched=False,
                    status="needs_review",
                    reason="bundle_multiple_models_detected",
                    candidates=candidates
                )

    # Verify candidate meets minimum auto threshold
    if top_candidate.confidence < 0.90:
        return MatchResult(
            matched=False,
            status="needs_review",
            reason=f"confidence_below_threshold ({top_candidate.confidence})",
            candidates=candidates
        )

    # Fetch reference model from DB
    ref_obj = db.query(models.ProductReferenceModel).filter(
        models.ProductReferenceModel.id == top_candidate.reference_model_id
    ).first()

    if not ref_obj:
        return MatchResult(
            matched=False,
            status="no_match",
            reason="reference_model_not_found"
        )

    # Calculate what fields would be filled
    would_fill: Dict[str, Any] = {}
    if not brand and ref_obj.brand:
        would_fill["brand"] = ref_obj.brand
    if not model and ref_obj.model:
        would_fill["model"] = ref_obj.model
    if ref_obj.default_category_id:
        would_fill["category_id"] = ref_obj.default_category_id
    if ref_obj.site_title:
        would_fill["site_title"] = ref_obj.site_title
    if ref_obj.site_description:
        would_fill["site_description"] = ref_obj.site_description
    if ref_obj.specifications_json:
        try:
            import json
            specs = json.loads(ref_obj.specifications_json)
            if isinstance(specs, dict):
                would_fill["specifications"] = specs
        except Exception:
            pass

    return MatchResult(
        matched=True,
        reference_model_id=ref_obj.id,
        canonical_name=ref_obj.canonical_name,
        brand=ref_obj.brand,
        model=ref_obj.model,
        method=top_candidate.tier,
        confidence=top_candidate.confidence,
        status="matched",
        reason="high_confidence_match",
        reference_model=ref_obj,
        candidates=candidates,
        would_fill=would_fill,
    )
