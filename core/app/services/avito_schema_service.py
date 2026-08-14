import json
import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app import models

def infer_attribute_type(val: Any) -> str:
    if isinstance(val, bool):
        return "boolean"
    elif isinstance(val, int):
        return "integer"
    elif isinstance(val, float):
        return "decimal"
    elif isinstance(val, list):
        return "multiple_choice"
    elif isinstance(val, str):
        val_lower = val.strip().lower()
        if val_lower in ("true", "false", "да", "нет"):
            return "boolean"
        return "single_choice"
    return "string"

def upsert_avito_category_schema(
    db: Session,
    category_name: str,
    category_path: Optional[str] = None,
    characteristics: Optional[Dict[str, Any]] = None,
    external_category_id: Optional[str] = None
) -> models.AvitoCategory:
    """Idempotently upsert AvitoCategory, AvitoAttributeDefinitions, and AvitoAttributeOptions."""
    now = datetime.datetime.now(datetime.timezone.utc)
    category_name = (category_name or "Без категории").strip()

    # 1. Category lookup/creation
    category = None
    if external_category_id:
        category = db.query(models.AvitoCategory).filter(models.AvitoCategory.external_category_id == external_category_id).first()
    if not category:
        category = db.query(models.AvitoCategory).filter(models.AvitoCategory.name == category_name).first()
    
    if not category:
        category = models.AvitoCategory(
            external_category_id=external_category_id,
            name=category_name,
            path=category_path or category_name,
            source="avito",
            is_active=True,
            observed_at=now
        )
        db.add(category)
        db.flush()
    else:
        category.observed_at = now
        if category_path and not category.path:
            category.path = category_path
        if external_category_id and not category.external_category_id:
            category.external_category_id = external_category_id
        db.flush()

    # 2. Attribute Definitions & Options lookup/creation
    if characteristics and isinstance(characteristics, dict):
        for idx, (attr_key, attr_val) in enumerate(characteristics.items()):
            if not attr_key or attr_val is None:
                continue
            
            attr_key_str = str(attr_key).strip()
            attr_type = infer_attribute_type(attr_val)
            is_multiple = isinstance(attr_val, list)

            # Definition lookup
            definition = db.query(models.AvitoAttributeDefinition).filter(
                models.AvitoAttributeDefinition.category_id == category.id,
                models.AvitoAttributeDefinition.external_key == attr_key_str
            ).first()

            if not definition:
                definition = models.AvitoAttributeDefinition(
                    category_id=category.id,
                    external_key=attr_key_str,
                    name=attr_key_str,
                    type=attr_type,
                    multiple=is_multiple,
                    sort_order=idx,
                    is_active=True,
                    observed_at=now
                )
                db.add(definition)
                db.flush()
            else:
                definition.observed_at = now
                if is_multiple:
                    definition.multiple = True
                db.flush()

            # Options lookup if choice or string type
            option_values = attr_val if isinstance(attr_val, list) else [attr_val]
            for opt_val in option_values:
                if opt_val is None or isinstance(opt_val, (dict, list)):
                    continue
                opt_str = str(opt_val).strip()
                if not opt_str:
                    continue

                option = db.query(models.AvitoAttributeOption).filter(
                    models.AvitoAttributeOption.attribute_definition_id == definition.id,
                    models.AvitoAttributeOption.value == opt_str
                ).first()

                if not option:
                    option = models.AvitoAttributeOption(
                        attribute_definition_id=definition.id,
                        value=opt_str,
                        label=opt_str,
                        is_active=True,
                        last_seen_at=now
                    )
                    db.add(option)
                    db.flush()
                else:
                    option.last_seen_at = now
                    db.flush()

    return category

def upsert_product_avito_attributes(
    db: Session,
    product_id: int,
    category_id: int,
    characteristics: Optional[Dict[str, Any]] = None
) -> List[models.ProductAvitoAttributeValue]:
    """Idempotently bind product to AvitoCategory and store dynamic attribute values preserving exact raw_value."""
    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. Update Product.avito_category_id
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product:
        product.avito_category_id = category_id
        db.flush()

    saved_values = []
    if not characteristics or not isinstance(characteristics, dict):
        return saved_values

    # 2. Iterate characteristics and upsert ProductAvitoAttributeValue
    for attr_key, attr_val in characteristics.items():
        if not attr_key or attr_val is None:
            continue
        
        attr_key_str = str(attr_key).strip()

        # Find or dynamically create definition for unknown attribute safety
        definition = db.query(models.AvitoAttributeDefinition).filter(
            models.AvitoAttributeDefinition.category_id == category_id,
            models.AvitoAttributeDefinition.external_key == attr_key_str
        ).first()

        if not definition:
            attr_type = infer_attribute_type(attr_val)
            definition = models.AvitoAttributeDefinition(
                category_id=category_id,
                external_key=attr_key_str,
                name=attr_key_str,
                type=attr_type,
                multiple=isinstance(attr_val, list),
                sort_order=99,
                is_active=True,
                observed_at=now
            )
            db.add(definition)
            db.flush()

        # Format raw_value and normalized value
        raw_val_str = json.dumps(attr_val, ensure_ascii=False) if isinstance(attr_val, (dict, list)) else str(attr_val)
        normalized_val = ", ".join([str(v) for v in attr_val]) if isinstance(attr_val, list) else str(attr_val)

        # Match single-choice option if scalar
        matched_option = None
        if not isinstance(attr_val, list) and normalized_val:
            matched_option = db.query(models.AvitoAttributeOption).filter(
                models.AvitoAttributeOption.attribute_definition_id == definition.id,
                models.AvitoAttributeOption.value == normalized_val.strip()
            ).first()

        # Upsert value row
        val_row = db.query(models.ProductAvitoAttributeValue).filter(
            models.ProductAvitoAttributeValue.product_id == product_id,
            models.ProductAvitoAttributeValue.attribute_definition_id == definition.id
        ).first()

        if not val_row:
            val_row = models.ProductAvitoAttributeValue(
                product_id=product_id,
                attribute_definition_id=definition.id,
                option_id=matched_option.id if matched_option else None,
                value=normalized_val,
                raw_value=raw_val_str,
                source="avito",
                updated_at=now
            )
            db.add(val_row)
        else:
            val_row.option_id = matched_option.id if matched_option else val_row.option_id
            val_row.value = normalized_val
            val_row.raw_value = raw_val_str
            val_row.updated_at = now

        db.flush()
        saved_values.append(val_row)

    return saved_values
