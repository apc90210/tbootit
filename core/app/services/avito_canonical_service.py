import re
import datetime
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app import models

def normalize_label(label: str) -> str:
    """Normalize label for exact matching: lowercase, strip, collapse whitespace."""
    if not label:
        return ""
    cleaned = re.sub(r"\s+", " ", str(label).strip().lower())
    return cleaned

def slugify_key(text: str) -> str:
    """Convert text to internal slug key."""
    if not text:
        return "unknown"
    trans = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    lowered = text.strip().lower()
    res = []
    for char in lowered:
        if char in trans:
            res.append(trans[char])
        elif char.isalnum() or char in ('_', '-'):
            res.append(char)
        else:
            res.append('_')
    slug = re.sub(r'_+', '_', ''.join(res)).strip('_')
    return slug or "attr"

def ensure_canonical_category_from_observed(
    db: Session,
    observed_category: models.AvitoCategory,
    official_slug: Optional[str] = None,
    official_source: Optional[str] = None
) -> models.AvitoCanonicalCategory:
    """
    Ensure a transport-neutral canonical category exists for an observed AvitoCategory.
    Does not assume official slug availability.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    internal_key = f"cat_{slugify_key(observed_category.name)}"

    canonical_cat = db.query(models.AvitoCanonicalCategory).filter(
        (models.AvitoCanonicalCategory.observed_category_id == observed_category.id) |
        (models.AvitoCanonicalCategory.internal_key == internal_key)
    ).first()

    if not canonical_cat:
        canonical_cat = models.AvitoCanonicalCategory(
            internal_key=internal_key,
            display_name=observed_category.name,
            observed_category_id=observed_category.id,
            official_slug=official_slug,
            official_source=official_source,
            capability_source="official_api" if official_slug else "observed",
            active=True,
            created_at=now
        )
        db.add(canonical_cat)
        db.flush()
    else:
        canonical_cat.observed_category_id = observed_category.id
        if official_slug and not canonical_cat.official_slug:
            canonical_cat.official_slug = official_slug
            canonical_cat.official_source = official_source or "official_api"
            canonical_cat.capability_source = "official_api"
        canonical_cat.updated_at = now
        db.flush()

    return canonical_cat

def sync_observed_category_to_canonical(
    db: Session,
    observed_category_id: int
) -> Tuple[models.AvitoCanonicalCategory, List[models.AvitoObservedFieldMapping]]:
    """
    Synchronize observed category definitions into canonical fields and create exact_label mappings.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    observed_cat = db.query(models.AvitoCategory).filter(models.AvitoCategory.id == observed_category_id).first()
    if not observed_cat:
        raise ValueError(f"AvitoCategory {observed_category_id} not found")

    canonical_cat = ensure_canonical_category_from_observed(db, observed_cat)
    mappings = []

    for attr_def in observed_cat.definitions:
        norm_name = normalize_label(attr_def.name)
        if not norm_name:
            continue

        field_key = slugify_key(attr_def.external_key or attr_def.name)

        # Lookup or create canonical field
        canonical_field = db.query(models.AvitoCanonicalField).filter(
            models.AvitoCanonicalField.category_id == canonical_cat.id,
            models.AvitoCanonicalField.internal_key == field_key
        ).first()

        if not canonical_field:
            canonical_field = models.AvitoCanonicalField(
                category_id=canonical_cat.id,
                internal_key=field_key,
                display_name=attr_def.name,
                data_type="string" if attr_def.type not in ("integer", "float", "boolean") else attr_def.type,
                field_type="select" if attr_def.options else "input",
                active=True,
                created_at=now
            )
            db.add(canonical_field)
            db.flush()

        # Lookup or create observed mapping
        mapping = db.query(models.AvitoObservedFieldMapping).filter(
            models.AvitoObservedFieldMapping.category_id == observed_cat.id,
            models.AvitoObservedFieldMapping.observed_name_normalized == norm_name
        ).first()

        if not mapping:
            mapping = models.AvitoObservedFieldMapping(
                category_id=observed_cat.id,
                observed_name=attr_def.name,
                observed_name_normalized=norm_name,
                canonical_field_id=canonical_field.id,
                mapping_source="exact_label",
                confidence=1.0,
                active=True,
                created_at=now
            )
            db.add(mapping)
            db.flush()
        else:
            if not mapping.canonical_field_id:
                mapping.canonical_field_id = canonical_field.id
            mapping.updated_at = now
            db.flush()

        mappings.append(mapping)

    return canonical_cat, mappings

def get_canonical_projection_for_product(db: Session, product_id: int) -> Dict[str, Any]:
    """
    Project product data and dynamic attributes onto canonical fields.
    Preserves all unmapped characteristics in unresolved_fields.
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise ValueError(f"Product {product_id} not found")

    canonical_fields: Dict[str, Any] = {}
    unresolved_fields: List[Dict[str, Any]] = []

    # Map core standard fields
    if product.brand:
        canonical_fields["brand"] = product.brand
    if product.model:
        canonical_fields["model"] = product.model
    if product.condition:
        canonical_fields["condition"] = product.condition

    # Map dynamic observed attributes
    if product.avito_category_id:
        observed_cat = db.query(models.AvitoCategory).filter(models.AvitoCategory.id == product.avito_category_id).first()
        canonical_cat = None
        if observed_cat:
            canonical_cat = ensure_canonical_category_from_observed(db, observed_cat)
            if product.canonical_category_id != canonical_cat.id:
                product.canonical_category_id = canonical_cat.id
                db.flush()

        for attr_val in product.avito_attribute_values:
            attr_name = attr_val.definition.name if attr_val.definition else "Attribute"
            norm_name = normalize_label(attr_name)
            val_to_use = attr_val.value or attr_val.raw_value

            mapping = None
            if observed_cat:
                mapping = db.query(models.AvitoObservedFieldMapping).filter(
                    models.AvitoObservedFieldMapping.category_id == observed_cat.id,
                    models.AvitoObservedFieldMapping.observed_name_normalized == norm_name,
                    models.AvitoObservedFieldMapping.active == True
                ).first()

            if mapping and mapping.canonical_field and mapping.canonical_field_id:
                key = mapping.canonical_field.internal_key
                canonical_fields[key] = val_to_use
            else:
                unresolved_fields.append({
                    "name": attr_name,
                    "normalized_name": norm_name,
                    "raw_value": val_to_use,
                    "status": "unmapped"
                })

    return {
        "product_id": product.id,
        "canonical_category_id": product.canonical_category_id,
        "canonical_category_name": product.canonical_category.display_name if product.canonical_category else (product.avito_category.name if product.avito_category else None),
        "official_slug": product.canonical_category.official_slug if product.canonical_category else None,
        "canonical_fields": canonical_fields,
        "unresolved_fields": unresolved_fields
    }
