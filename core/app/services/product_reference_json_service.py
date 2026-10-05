"""
Product Reference Catalog JSON Import and Export Service.

Supports validated round-trip import and export of reference models and aliases.
Format adheres to PROMPT_WEB_07A Section 14:
{
  "version": 1,
  "models": [ ... ]
}

Features:
- Full schema validation
- Dry-run mode
- Idempotent upsert by stable_key
- Category name / slug resolution
- Duplicate alias prevention
- Complete export
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app import models
from app.services.product_reference_matcher import generate_stable_key, normalize_for_matching


def get_category_id_map(db: Session) -> Dict[str, int]:
    """Map category names and slugs (casefold) to category IDs."""
    cats = db.query(models.Category).all()
    cat_map: Dict[str, int] = {}
    for c in cats:
        if c.name:
            cat_map[c.name.strip().casefold()] = c.id
        if c.slug:
            cat_map[c.slug.strip().casefold()] = c.id
    return cat_map


def validate_reference_models_payload(data: Any) -> Tuple[bool, List[str]]:
    """Validate JSON payload against reference catalog schema."""
    errors = []
    if not isinstance(data, dict):
        return False, ["Payload must be a JSON object with 'version' and 'models' keys."]
    
    ver = data.get("version") or data.get("schema_version")
    if ver not in (1, "1", "1.0", 1.0):
        errors.append(f"Unsupported schema version: {ver}. Supported version: 1")


    models_list = data.get("models")
    if not isinstance(models_list, list):
        errors.append("'models' must be a list of model definitions.")
        return False, errors

    for idx, item in enumerate(models_list):
        prefix = f"Model #{idx + 1}"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: Item must be a dictionary.")
            continue

        if not item.get("brand") or not str(item.get("brand")).strip():
            errors.append(f"{prefix}: 'brand' is required and cannot be empty.")
        if not item.get("model") or not str(item.get("model")).strip():
            errors.append(f"{prefix}: 'model' is required and cannot be empty.")

        aliases = item.get("aliases")
        if aliases is not None and not isinstance(aliases, list):
            errors.append(f"{prefix}: 'aliases' must be a list of strings.")

        specs = item.get("specifications")
        if specs is not None and not isinstance(specs, dict):
            errors.append(f"{prefix}: 'specifications' must be a dictionary.")

    return len(errors) == 0, errors


def import_reference_models_from_dict(
    db: Session,
    data: Dict[str, Any],
    dry_run: bool = False,
    source: str = "json_import",
    source_note: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Import reference models from dictionary into Core DB.
    Uses stable_key for duplicate detection and idempotent update.
    """
    valid, errors = validate_reference_models_payload(data)
    if not valid:
        return {
            "success": False,
            "dry_run": dry_run,
            "errors": errors,
            "created": 0,
            "updated": 0,
            "aliases_created": 0,
            "total_in_payload": 0,
        }

    cat_map = get_category_id_map(db)
    models_list = data.get("models", [])

    created_count = 0
    updated_count = 0
    aliases_created_count = 0
    processed_models = []

    for item in models_list:
        brand = str(item.get("brand")).strip()
        model_name = str(item.get("model")).strip()
        canonical_name = str(item.get("canonical_name") or f"{brand} {model_name}").strip()
        device_type = item.get("device_type")
        category_hint = item.get("category")

        # Resolve category ID
        default_cat_id = item.get("default_category_id")
        if default_cat_id and default_cat_id not in cat_map.values():
            default_cat_id = None
        if not default_cat_id and category_hint:
            cat_key = str(category_hint).strip().casefold()
            default_cat_id = cat_map.get(cat_key)

        specs_dict = item.get("specifications") or {}
        specs_json = json.dumps(specs_dict, ensure_ascii=False) if specs_dict else None

        site_title = item.get("site_title") or canonical_name
        site_description = item.get("site_description")
        active = bool(item.get("active", True))

        stable_key = item.get("stable_key") or generate_stable_key(brand, model_name)
        aliases = item.get("aliases") or []
        # Ensure canonical name and brand+model are included in aliases
        canon_alias = canonical_name
        brand_model_alias = f"{brand} {model_name}"
        all_aliases = list(dict.fromkeys([canon_alias, brand_model_alias] + aliases))

        # Check existing by stable_key
        existing = db.query(models.ProductReferenceModel).filter(
            models.ProductReferenceModel.stable_key == stable_key
        ).first()

        if existing:
            action = "update"
            updated_count += 1
            if not dry_run:
                existing.canonical_name = canonical_name
                existing.brand = brand
                existing.model = model_name
                if device_type:
                    existing.device_type = device_type
                if default_cat_id:
                    existing.default_category_id = default_cat_id
                if specs_json:
                    # Merge with existing specs if present
                    if existing.specifications_json:
                        try:
                            curr_specs = json.loads(existing.specifications_json)
                            if isinstance(curr_specs, dict):
                                curr_specs.update(specs_dict)
                                existing.specifications_json = json.dumps(curr_specs, ensure_ascii=False)
                        except Exception:
                            existing.specifications_json = specs_json
                    else:
                        existing.specifications_json = specs_json
                if site_title:
                    existing.site_title = site_title
                if site_description:
                    existing.site_description = site_description
                existing.active = active
                ref_record = existing
            else:
                ref_record = existing
        else:
            action = "create"
            created_count += 1
            if not dry_run:
                ref_record = models.ProductReferenceModel(
                    stable_key=stable_key,
                    canonical_name=canonical_name,
                    brand=brand,
                    model=model_name,
                    device_type=device_type,
                    default_category_id=default_cat_id,
                    specifications_json=specs_json,
                    site_title=site_title,
                    site_description=site_description,
                    active=active,
                    source=source,
                    source_note=source_note,
                )
                db.add(ref_record)
                db.flush()
            else:
                ref_record = None

        # Process Aliases
        if not dry_run and ref_record:
            existing_norm_aliases = {
                a.normalized_alias for a in ref_record.aliases
            }
            for a_str in all_aliases:
                if not a_str or not str(a_str).strip():
                    continue
                a_clean = str(a_str).strip()
                norm_a = normalize_for_matching(a_clean)
                if norm_a and norm_a not in existing_norm_aliases:
                    new_alias = models.ProductReferenceAlias(
                        reference_model_id=ref_record.id,
                        alias=a_clean,
                        normalized_alias=norm_a,
                        priority=100,
                        active=True,
                    )
                    db.add(new_alias)
                    existing_norm_aliases.add(norm_a)
                    aliases_created_count += 1
        elif dry_run:
            aliases_created_count += len(all_aliases)

        processed_models.append({
            "stable_key": stable_key,
            "canonical_name": canonical_name,
            "action": action,
            "aliases_count": len(all_aliases),
        })

    if not dry_run:
        db.commit()

    return {
        "success": True,
        "dry_run": dry_run,
        "total_in_payload": len(models_list),
        "created": created_count,
        "updated": updated_count,
        "aliases_created": aliases_created_count,
        "processed_models": processed_models,
        "errors": [],
    }


def export_reference_models_to_dict(
    db: Session,
    active_only: bool = False
) -> Dict[str, Any]:
    """Export all reference models and aliases to standard JSON dict."""
    q = db.query(models.ProductReferenceModel)
    if active_only:
        q = q.filter(models.ProductReferenceModel.active == True)
    ref_models = q.order_by(models.ProductReferenceModel.brand.asc(), models.ProductReferenceModel.model.asc()).all()

    models_data = []
    for ref in ref_models:
        specs_dict = {}
        if ref.specifications_json:
            try:
                specs_dict = json.loads(ref.specifications_json)
            except Exception:
                pass

        alias_list = [a.alias for a in sorted(ref.aliases, key=lambda x: (x.priority, -len(x.alias)))]
        cat_name = ref.default_category.name if ref.default_category else None

        models_data.append({
            "stable_key": ref.stable_key,
            "canonical_name": ref.canonical_name,
            "brand": ref.brand,
            "model": ref.model,
            "device_type": ref.device_type,
            "category": cat_name,
            "default_category_id": ref.default_category_id,
            "aliases": alias_list,
            "specifications": specs_dict,
            "site_title": ref.site_title,
            "site_description": ref.site_description,
            "active": ref.active,
            "source": ref.source,
            "source_note": ref.source_note,
        })

    return {
        "version": 1,
        "schema_version": "1.0",
        "total_models": len(models_data),
        "models": models_data
    }



def import_reference_models_from_file(
    db: Session,
    file_path: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Import reference models from a JSON file path."""
    if not os.path.exists(file_path):
        return {
            "success": False,
            "errors": [f"File not found: {file_path}"]
        }
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return import_reference_models_from_dict(db, data, dry_run=dry_run, source="file_import", source_note=file_path)


def export_reference_models_to_file(
    db: Session,
    file_path: str,
    active_only: bool = False
) -> str:
    """Export reference models to a JSON file path."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    data = export_reference_models_to_dict(db, active_only=active_only)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return file_path
