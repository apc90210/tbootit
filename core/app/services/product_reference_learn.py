"""
Learning from Confirmed Product Service.

Allows the Owner / operator to explicitly promote a confirmed Product into a Reference Model.
Adheres to PROMPT_WEB_07A Section 17:
- Explicit action only (no silent learning from arbitrary products)
- Extracts verified brand, model, specifications, site_title, site_description
- Preserves clean category for reference model (even if product was in restoration)
- Generates aliases from title, canonical name, and custom aliases
- Links the confirmed product to the newly created/updated reference model
"""

import json
import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app import models
from app.services.product_categorizer import classify_product
from app.services.product_reference_matcher import generate_stable_key, normalize_for_matching

RESTORATION_CATEGORY_ID = 52



def save_product_as_reference_model(
    db: Session,
    product_id: int,
    canonical_name: Optional[str] = None,
    brand_override: Optional[str] = None,
    model_override: Optional[str] = None,
    custom_aliases: Optional[List[str]] = None,
    override_existing: bool = True,
) -> Dict[str, Any]:
    """
    Explicitly convert/promote a confirmed product into a Reference Model.
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise ValueError(f"Product {product_id} not found.")

    # Determine brand & model
    brand = (brand_override or product.brand or "").strip()
    model = (model_override or product.model or "").strip()

    # If brand or model is missing, attempt to extract from title
    if not brand or not model:
        title_norm = normalize_for_matching(product.title)
        # Fallback if both empty
        if not brand:
            # Check title first word or known brand
            for b_name in ["HP", "Xerox", "Canon", "Samsung", "Kyocera", "Lenovo", "Asus", "Acer", "Dell", "Brother", "Pantum", "Epson"]:
                if b_name.lower() in title_norm:
                    brand = b_name
                    break
        if not brand:
            brand = "Generic"
        if not model:
            model = product.title

    c_name = canonical_name or f"{brand} {model}".strip()
    stable_key = generate_stable_key(brand, model)

    # Specifications from product
    specs_json = None
    if product.avito_params_json:
        try:
            p_specs = json.loads(product.avito_params_json)
            if isinstance(p_specs, dict) and p_specs:
                specs_json = json.dumps(p_specs, ensure_ascii=False)
        except Exception:
            pass

    # Resolve default category for model
    # If the product itself was under restoration, determine the model's actual functional category
    default_cat_id = product.category_id
    if default_cat_id == 52 or not default_cat_id or default_cat_id == 48:
        # Classify without restoration override to find the model's device category
        cls_res = classify_product(
            title=product.title,
            brand=brand,
            model=model,
            existing_category_name=None,
            allow_override_valid_category=True
        )
        cat_row = db.query(models.Category).filter(models.Category.slug == cls_res.category_slug).first()
        if cat_row:
            default_cat_id = cat_row.id

    site_title = product.site_title or c_name
    site_description = product.site_description

    # Check existing by stable_key
    ref_model = db.query(models.ProductReferenceModel).filter(
        models.ProductReferenceModel.stable_key == stable_key
    ).first()

    action = "updated" if ref_model else "created"

    if ref_model:
        if override_existing:
            ref_model.canonical_name = c_name
            ref_model.brand = brand
            ref_model.model = model
            if default_cat_id:
                ref_model.default_category_id = default_cat_id
            if specs_json:
                ref_model.specifications_json = specs_json
            if site_title:
                ref_model.site_title = site_title
            if site_description:
                ref_model.site_description = site_description
            ref_model.source = "confirmed_product"
            ref_model.source_note = f"confirmed_from_product_{product_id}"
    else:
        ref_model = models.ProductReferenceModel(
            stable_key=stable_key,
            canonical_name=c_name,
            brand=brand,
            model=model,
            default_category_id=default_cat_id,
            specifications_json=specs_json,
            site_title=site_title,
            site_description=site_description,
            active=True,
            source="confirmed_product",
            source_note=f"confirmed_from_product_{product_id}",
        )
        db.add(ref_model)
        db.flush()

    # Collect and attach aliases
    aliases_to_add = [c_name, f"{brand} {model}", product.title]
    if custom_aliases:
        aliases_to_add.extend(custom_aliases)

    existing_norm_aliases = {a.normalized_alias for a in ref_model.aliases}
    for alias_text in aliases_to_add:
        if not alias_text or not str(alias_text).strip():
            continue
        clean_alias = str(alias_text).strip()
        norm_alias = normalize_for_matching(clean_alias)
        if norm_alias and norm_alias not in existing_norm_aliases:
            alias_obj = models.ProductReferenceAlias(
                reference_model_id=ref_model.id,
                alias=clean_alias,
                normalized_alias=norm_alias,
                priority=100,
                active=True,
            )
            db.add(alias_obj)
            existing_norm_aliases.add(norm_alias)

    # Link the source product to this reference model
    now = datetime.datetime.now(datetime.timezone.utc)
    product.reference_model_id = ref_model.id
    product.reference_match_method = "confirmed_product"
    product.reference_match_confidence = 1.00
    product.reference_enriched_at = now

    db.commit()
    db.refresh(ref_model)

    return {
        "success": True,
        "action": action,
        "id": ref_model.id,
        "reference_model_id": ref_model.id,
        "canonical_name": ref_model.canonical_name,
        "brand": ref_model.brand,
        "model": ref_model.model,
        "stable_key": ref_model.stable_key,
        "source_product_id": product_id,
        "aliases": [{"id": a.id, "alias": a.alias, "normalized_alias": a.normalized_alias} for a in ref_model.aliases],
    }

