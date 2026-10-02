"""
Deterministic Product Categorizer Service.

Categorizes products into one of the 7 canonical categories based on strict priority rules:
1. МФУ
2. Ноутбуки
3. Мониторы
4. Принтеры
5. Компьютеры
6. Комплектующие
7. Без категории (fallback)

Fast, offline, deterministic rule engine without external network or LLM dependencies.
"""

import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

CANONICAL_CATEGORIES: Dict[str, Dict[str, str]] = {
    "Техника под восстановление": {"name": "Техника под восстановление", "slug": "pod-vosstanovlenie"},
    "МФУ": {"name": "МФУ", "slug": "mfu"},
    "Ноутбуки": {"name": "Ноутбуки", "slug": "noutbuki"},
    "Мониторы": {"name": "Мониторы", "slug": "monitory"},
    "Принтеры": {"name": "Принтеры", "slug": "printery"},
    "Компьютеры": {"name": "Компьютеры", "slug": "kompyutery"},
    "Комплектующие": {"name": "Комплектующие", "slug": "komplektuyuschie"},
    "Без категории": {"name": "Без категории", "slug": "bez-kategorii"},
}

CANONICAL_NAMES = set(CANONICAL_CATEGORIES.keys())
SPECIFIC_CANONICAL_NAMES = CANONICAL_NAMES - {"Без категории"}

# Absolute Priority 1: Restoration (MUST evaluate before all other categories and overrides existing category)
RE_RESTORATION = re.compile(
    r"\bпод\s+восстановлени[еяюемх]\b",
    re.IGNORECASE
)

# Priority 2: MFP
RE_MFP = re.compile(
    r"\b(мфу|mfp|многофункциональн\w*|multifunction\w*|multi-function\w*|all-in-one printer|aio printer)\b"
    r"|\b3\s*[-в/]\s*1\b"
    r"|\b(печать|принтер)\b.*?\b(сканер|копир)\b"
    r"|\b(сканер|копир)\b.*?\b(печать|принтер)\b",
    re.IGNORECASE
)

# Priority 2: Laptops
RE_LAPTOP = re.compile(
    r"\b(ноутбук\w*|ноут\w*|laptop\w*|notebook\w*|ultrabook\w*|ультрабук\w*|нетбук\w*|netbook\w*)\b"
    r"|\b(macbook|thinkpad|ideapad|zenbook|vivobook|elitebook|probook)\b",
    re.IGNORECASE
)

# Priority 3: Monitors
# Matches monitor inflections and standalone displays, strictly excluding мониторинг
RE_MONITOR = re.compile(
    r"\bмонитор(?:[аеуоы]|ом|ов|ам|ами|ах)?\b"
    r"|\bmonitors?\b"
    r"|\b(led|lcd|ips|сенсорный)\s+(дисплей\w*|display\w*|монитор\w*|monitor\w*)\b",
    re.IGNORECASE
)

# Priority 4: Printers (MFP checked first; will not match MFP)
RE_PRINTER = re.compile(
    r"\b(принтер\w*|printer\w*|лазерный принтер\w*|струйный принтер\w*|термопринтер\w*|чековый принтер\w*|laserjet|deskjet|stylus photo|phaser|pixma)\b",
    re.IGNORECASE
)

# Priority 5: Computers
RE_COMPUTER = re.compile(
    r"\b(компьютер\w*|системный блок\w*|системник\w*|моноблок\w*|мини[- ]пк\b|минипк\w*|неттоп\w*|десктоп\w*|all[- ]in[- ]one pc\b|aio pc\b)"
    r"|\b(пк|pc)\b(?!\s*[-/]?\s*\d{4,5})"
    r"|\b(настольный компьютер\w*|персональный компьютер\w*)\b",
    re.IGNORECASE
)

# Priority 6: Components
RE_COMPONENTS = re.compile(
    r"\b(видеокарт\w*|gpu|geforce|radeon|rtx\s*\d+|gtx\s*\d+|rx\s*\d+)\b"
    r"|\b(процессор\w*|cpu|сокет\w*|socket\s*(?:lga|am\d))\b"
    r"|\b(материнск\w*\s+плат\w*|материнк\w*|motherboard|mainboard)\b"
    r"|\b(оперативн\w*\s+памят\w*|озу|ram\b|sodimm|dimm|ddr[2345])\b"
    r"|\b(жестк\w*\s+диск\w*|жесткий диск|жёсткий диск|hdd\b|винчестер\w*)\b"
    r"|\b(ssd\b|ssd[- ]накопител\w*|твердотельн\w*\s+накопител\w*)\b"
    r"|\b(блок\w*\s+питани\w*|psu\b)\b"
    r"|\b(корпус\w*|кулер\w*|куллер\w*|вентилятор\w*|радиатор\w*|охлаждени\w*)\b"
    r"|\b(сетев\w*\s+(?:адаптер\w*|карт\w*)|звуков\w*\s+карт\w*|wi[- ]fi\s+адаптер\w*)\b"
    r"|\b(мат\.?\s*плата|комплект\s+мат|ga-[a-z0-9]+|h110m|b250m|z370|h81m|h61m)\b",
    re.IGNORECASE
)


@dataclass
class ClassificationResult:
    category_name: str
    category_slug: str
    reason: str
    confidence: str  # 'explicit', 'keyword', 'fallback'
    rule_name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_name": self.category_name,
            "category_slug": self.category_slug,
            "reason": self.reason,
            "confidence": self.confidence,
            "rule_name": self.rule_name,
        }


def normalize_text(text: Optional[str]) -> str:
    """Normalize text for robust keyword matching: lowercase, replace ё with е, collapse whitespace."""
    if not text:
        return ""
    t = str(text).casefold()
    t = t.replace("ё", "е")
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def classify_product(
    title: Optional[str] = "",
    site_title: Optional[str] = "",
    brand: Optional[str] = "",
    model: Optional[str] = "",
    description: Optional[str] = "",
    existing_category_name: Optional[str] = None,
    allow_override_valid_category: bool = False,
) -> ClassificationResult:
    """
    Deterministic rule engine to classify a product into one of 7 canonical categories.
    
    If product has an existing specific valid canonical category and allow_override_valid_category is False,
    the existing category is preserved with 'explicit' confidence.
    """
    # Prepare normalized combined text
    parts = [title or "", site_title or "", model or "", description or "", brand or ""]
    combined = " ".join(filter(None, parts))
    norm = normalize_text(combined)

    if not norm:
        canon = CANONICAL_CATEGORIES["Без категории"]
        return ClassificationResult(
            category_name=canon["name"],
            category_slug=canon["slug"],
            reason="fallback:empty_input",
            confidence="fallback",
            rule_name="fallback",
        )

    # Absolute Priority 1: Restoration marker ('под восстановление')
    # Overrides all other categories, including existing valid categories.
    m_rest = RE_RESTORATION.search(norm)
    if m_rest:
        canon = CANONICAL_CATEGORIES["Техника под восстановление"]
        return ClassificationResult(
            category_name=canon["name"],
            category_slug=canon["slug"],
            reason="explicit_restoration_marker",
            confidence="explicit",
            rule_name="rule_0_restoration",
        )

    # 0. Check existing valid canonical category (if not a restoration item)
    if existing_category_name and not allow_override_valid_category:
        clean_cat = existing_category_name.strip()
        if clean_cat in SPECIFIC_CANONICAL_NAMES:
            canon = CANONICAL_CATEGORIES[clean_cat]
            return ClassificationResult(
                category_name=canon["name"],
                category_slug=canon["slug"],
                reason="existing_valid_category",
                confidence="explicit",
                rule_name="existing_valid_category",
            )

    # Priority 2: МФУ (Multi-function printer wins over standard printer)
    m = RE_MFP.search(norm)
    if m:
        canon = CANONICAL_CATEGORIES["МФУ"]
        return ClassificationResult(
            category_name=canon["name"],
            category_slug=canon["slug"],
            reason=f"keyword:mfp ({m.group(0)})",
            confidence="keyword",
            rule_name="rule_1_mfp",
        )

    # Priority 2: Ноутбуки
    m = RE_LAPTOP.search(norm)
    if m:
        canon = CANONICAL_CATEGORIES["Ноутбуки"]
        return ClassificationResult(
            category_name=canon["name"],
            category_slug=canon["slug"],
            reason=f"keyword:laptop ({m.group(0)})",
            confidence="keyword",
            rule_name="rule_2_laptops",
        )

    # Priority 3: Мониторы
    m = RE_MONITOR.search(norm)
    if m:
        canon = CANONICAL_CATEGORIES["Мониторы"]
        return ClassificationResult(
            category_name=canon["name"],
            category_slug=canon["slug"],
            reason=f"keyword:monitor ({m.group(0)})",
            confidence="keyword",
            rule_name="rule_3_monitors",
        )

    # Priority 4: Принтеры
    m = RE_PRINTER.search(norm)
    if m:
        canon = CANONICAL_CATEGORIES["Принтеры"]
        return ClassificationResult(
            category_name=canon["name"],
            category_slug=canon["slug"],
            reason=f"keyword:printer ({m.group(0)})",
            confidence="keyword",
            rule_name="rule_4_printers",
        )

    # Priority 5: Компьютеры
    m = RE_COMPUTER.search(norm)
    if m:
        canon = CANONICAL_CATEGORIES["Компьютеры"]
        return ClassificationResult(
            category_name=canon["name"],
            category_slug=canon["slug"],
            reason=f"keyword:computer ({m.group(0)})",
            confidence="keyword",
            rule_name="rule_5_computers",
        )

    # Priority 6: Комплектующие
    m = RE_COMPONENTS.search(norm)
    if m:
        canon = CANONICAL_CATEGORIES["Комплектующие"]
        return ClassificationResult(
            category_name=canon["name"],
            category_slug=canon["slug"],
            reason=f"keyword:components ({m.group(0)})",
            confidence="keyword",
            rule_name="rule_6_components",
        )

    # Priority 7: Fallback
    canon = CANONICAL_CATEGORIES["Без категории"]
    return ClassificationResult(
        category_name=canon["name"],
        category_slug=canon["slug"],
        reason="fallback:no_keyword_match",
        confidence="fallback",
        rule_name="rule_7_fallback",
    )
