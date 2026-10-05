"""
Product Reference Enrichment Service.

Applies model-level reference data from a matched ProductReferenceModel to a Product instance
in accordance with strict safety invariants:

Invariants:
1. Restoration rule is ABSOLUTE:
   If a product has a restoration marker or is classified in "Техника под восстановление",
   its category remains "Техника под восстановление" (category_id = 52).
2. Explicit product data wins over reference defaults:
   Enriches missing fields only:
   - brand (if empty)
   - model (if empty)
   - category (if missing/empty/Без категории AND not restoration)
   - site_title (if empty)
   - site_description (if empty)
   - specifications (merge only missing keys: product existing > reference default)
3. Never automatically overwrite:
   sale_price, purchase_price, quantity, status, condition, serial_number, photos, notes,
   defects, individual description, or restoration category.
4. Record full provenance:
   reference_model_id, reference_match_method, reference_match_confidence, reference_enriched_at,
   and audit logging.
"""

import json
import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session

from app import models
from app.services.product_categorizer import RE_RESTORATION, CANONICAL_CATEGORIES
from app.routers.customers import log_audit


RESTORATION_CATEGORY_ID = 52
UNCATEGORIZED_CATEGORY_ID = 48


def has_restoration_marker(product: models.Product) -> bool:
    """Check if product has explicit restoration keywords in any text field."""
    text_parts = [
        product.title or "",
        product.site_title or "",
        product.model or "",
        product.description or "",
        product.notes or ""
    ]
    combined = " ".join(text_parts).lower()
    return bool(RE_RESTORATION.search(combined))


def enrich_product_from_reference(
    db: Session,
    product: models.Product,
    reference: models.ProductReferenceModel,
    method: str,
    confidence: float,
    apply: bool = True,
) -> Dict[str, Any]:
    """
    Enrich product with reference model data, adhering strictly to non-overwrite rules.
    Returns a dict describing changes made / fields filled.
    """
    before_state: Dict[str, Any] = {
        "brand": product.brand,
        "model": product.model,
        "category_id": product.category_id,
        "site_title": product.site_title,
        "site_description": product.site_description,
        "avito_params_json": product.avito_params_json,
        "reference_model_id": product.reference_model_id,
        "reference_match_method": product.reference_match_method,
        "reference_match_confidence": product.reference_match_confidence,
    }

    fields_filled: Dict[str, Any] = {}

    # 1. Brand (if missing or empty)
    if not product.brand or not str(product.brand).strip():
        if reference.brand:
            fields_filled["brand"] = reference.brand
            if apply:
                product.brand = reference.brand

    # 2. Model (if missing or empty)
    if not product.model or not str(product.model).strip():
        if reference.model:
            fields_filled["model"] = reference.model
            if apply:
                product.model = reference.model

    # 3. Category
    # Invariant: If restoration marker is present or existing category is restoration, DO NOT override!
    is_restoration = (
        product.category_id == RESTORATION_CATEGORY_ID
        or has_restoration_marker(product)
    )

    if not is_restoration:
        # Fill category if current category is missing, empty, or "Без категории"
        current_cat_empty = (
            not product.category_id
            or product.category_id == UNCATEGORIZED_CATEGORY_ID
        )
        if current_cat_empty and reference.default_category_id:
            fields_filled["category_id"] = reference.default_category_id
            if apply:
                product.category_id = reference.default_category_id
    else:
        # Restoration category has absolute priority
        if product.category_id != RESTORATION_CATEGORY_ID and apply:
            product.category_id = RESTORATION_CATEGORY_ID

    # 4. site_title (if missing or empty)
    if not product.site_title or not str(product.site_title).strip():
        proposed_site_title = reference.site_title or reference.canonical_name
        if proposed_site_title:
            fields_filled["site_title"] = proposed_site_title
            if apply:
                product.site_title = proposed_site_title

    # 5. site_description (if missing or empty)
    if not product.site_description or not str(product.site_description).strip():
        if reference.site_description:
            fields_filled["site_description"] = reference.site_description
            if apply:
                product.site_description = reference.site_description

    # 6. Specifications merge
    # Invariant: product existing value > reference default value
    # Only missing keys are merged
    ref_specs: Dict[str, Any] = {}
    if reference.specifications_json:
        try:
            parsed = json.loads(reference.specifications_json)
            if isinstance(parsed, dict):
                ref_specs = parsed
        except Exception:
            pass

    prod_specs: Dict[str, Any] = {}
    if product.avito_params_json:
        try:
            parsed = json.loads(product.avito_params_json)
            if isinstance(parsed, dict):
                prod_specs = parsed
        except Exception:
            pass

    specs_added: Dict[str, Any] = {}
    for spec_key, spec_val in ref_specs.items():
        if spec_key not in prod_specs or prod_specs[spec_key] is None or str(prod_specs[spec_key]).strip() == "":
            prod_specs[spec_key] = spec_val
            specs_added[spec_key] = spec_val

    if specs_added:
        fields_filled["specifications_added"] = specs_added
        if apply:
            product.avito_params_json = json.dumps(prod_specs, ensure_ascii=False)

    # 7. Set Provenance
    now = datetime.datetime.now(datetime.timezone.utc)
    if apply:
        product.reference_model_id = reference.id
        product.reference_match_method = method
        product.reference_match_confidence = confidence
        product.reference_enriched_at = now

    after_state: Dict[str, Any] = {
        "brand": product.brand,
        "model": product.model,
        "category_id": product.category_id,
        "site_title": product.site_title,
        "site_description": product.site_description,
        "avito_params_json": product.avito_params_json,
        "reference_model_id": reference.id,
        "reference_match_method": method,
        "reference_match_confidence": confidence,
    }

    # 8. Audit logging
    if apply and fields_filled:
        try:
            log_audit(
                db=db,
                entity_type="product",
                entity_id=product.id,
                action="reference_enrich",
                old_value=json.dumps(before_state, ensure_ascii=False, default=str),
                new_value=json.dumps(after_state, ensure_ascii=False, default=str),
                comment=f"Auto-enriched from reference model #{reference.id} ({reference.canonical_name}) via {method} (conf={confidence:.2f})"
            )
        except Exception as e:
            # Non-fatal audit log warning
            pass

    return {
        "product_id": product.id,
        "reference_model_id": reference.id,
        "canonical_name": reference.canonical_name,
        "method": method,
        "confidence": confidence,
        "fields_filled": fields_filled,
        "applied": apply,
    }
