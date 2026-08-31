from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app import models
from app.services.avito_capability_service import get_avito_capabilities
from app.services.avito_canonical_service import get_canonical_projection_for_product

def build_avito_publication_package(db: Session, product_id: int) -> Dict[str, Any]:
    """
    Build a transport-neutral publication package for a product.
    Usable by Browser-Assisted adapter, Manual copy workflow, or Official Autoload.
    Does NOT publish anything.
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise ValueError(f"Product {product_id} not found")

    capabilities = get_avito_capabilities(db)
    projection = get_canonical_projection_for_product(db, product_id)

    # Collect photos
    product_photos = getattr(product, "photos", None)
    if product_photos is None:
        product_photos = db.query(models.ProductPhoto).filter_by(product_id=product.id).all()

    photos_data = []
    for photo in product_photos:
        photos_data.append({
            "id": photo.id,
            "filename": getattr(photo, "filename", None),
            "media_url": photo.media_url,
            "source_url": getattr(photo, "source_url", None),
            "is_primary": getattr(photo, "is_primary", False) if hasattr(photo, "is_primary") else (photo.sort_order == 0),
            "sort_order": getattr(photo, "sort_order", 0)
        })

    # Characteristics dictionary
    characteristics: Dict[str, Any] = {}
    for attr_val in product.avito_attribute_values:
        attr_name = attr_val.definition.name if attr_val.definition else "attr"
        characteristics[attr_name] = attr_val.value or attr_val.raw_value

    org_settings = db.query(models.OrganizationSettings).first()
    shop_address = (org_settings.address if org_settings and org_settings.address else "Свердловская область, Екатеринбург, улица Кузнецова, 10")
    
    canonical_cat_name = projection.get("canonical_category_name") or (product.category.name if getattr(product, "category", None) else "Товары")
    observed_path = projection.get("observed_path") or ([canonical_cat_name] if canonical_cat_name else [])

    category_info = {
        "display_name": canonical_cat_name,
        "observed_path": observed_path,
        "canonical_category_id": projection.get("canonical_category_id")
    }

    location_info = {
        "city": (org_settings.city if org_settings and getattr(org_settings, "city", None) else "Екатеринбург") if shop_address else None,
        "address": shop_address,
        "source": "store_default" if shop_address else "none",
        "verified": bool(shop_address)
    }

    package = {
        "product_id": product.id,
        "sku": product.sku,
        "category": category_info,
        "title": product.title or product.avito_title or "",
        "description": product.description or product.avito_description or "",
        "price": float(product.sale_price or 0.0),
        "brand": product.brand,
        "model": product.model,
        "condition": product.condition or product.avito_condition or "Б/у",
        "address": shop_address,
        "location": location_info,
        "characteristics": characteristics,
        "photos": photos_data,
        "canonical_fields": projection.get("canonical_fields", {}),
        "unresolved_fields": projection.get("unresolved_fields", []),
        "transport_options": {
            "official_autoload": capabilities.get("autoload_schema_present", False) and bool(projection.get("official_slug")),
            "browser_assisted": capabilities.get("browser_assisted_available", True),
            "manual": capabilities.get("manual_available", True)
        }
    }
    return package

def preflight_product_for_avito(db: Session, product_id: int) -> Dict[str, Any]:
    """
    Run publication preflight validation for a product.
    Transport-neutral validation applies to all modes.
    Official Autoload validation applies strictly if official schema capability is active.
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise ValueError(f"Product {product_id} not found")

    capabilities = get_avito_capabilities(db)
    projection = get_canonical_projection_for_product(db, product_id)
    canonical_fields = projection.get("canonical_fields", {})
    unresolved = projection.get("unresolved_fields", [])

    errors: List[str] = []
    warnings: List[str] = []

    # 1. Transport-neutral validation
    title = (product.title or product.avito_title or "").strip()
    if not title:
        errors.append("MISSING_TITLE: Заголовок объявления обязателен")

    description = (product.description or product.avito_description or "").strip()
    if not description:
        errors.append("MISSING_DESCRIPTION: Описание объявления обязательно")

    price = float(product.sale_price or 0.0)
    if price <= 0:
        errors.append("INVALID_PRICE: Цена продажи должна быть больше 0")

    product_photos = getattr(product, "photos", None)
    if product_photos is None:
        product_photos = db.query(models.ProductPhoto).filter_by(product_id=product.id).all()
    photos_count = len(product_photos)
    if photos_count == 0:
        errors.append("MISSING_PHOTOS: Для публикации требуется хотя бы одна фотография")

    if not projection.get("canonical_category_name"):
        warnings.append("UNRESOLVED_CATEGORY: Категория товара не определена в канонической структуре")

    if unresolved:
        warnings.append(f"UNRESOLVED_FIELDS: Обнаружено {len(unresolved)} не сопоставленных характеристик")

    # 2. Capability-based transport readiness
    is_valid_base = len(errors) == 0

    ready_for_browser_assisted = is_valid_base and capabilities.get("browser_assisted_available", True)
    ready_for_manual = is_valid_base and capabilities.get("manual_available", True)

    ready_for_official_autoload = False
    if not capabilities.get("autoload_schema_present", False) or not projection.get("official_slug"):
        warnings.append("AUTOLOAD_SCHEMA_UNAVAILABLE: Официальная схема Avito Autoload не подключена или не сопоставлен официальный slug")
    else:
        # If official autoload schema capability is active, validate official rules
        official_errors = []
        canonical_cat_id = projection.get("canonical_category_id")
        if canonical_cat_id:
            fields = db.query(models.AvitoCanonicalField).filter(
                models.AvitoCanonicalField.category_id == canonical_cat_id,
                models.AvitoCanonicalField.active == True
            ).all()

            for f in fields:
                for rule in f.rules:
                    # Ignore inferred_disabled rules in production publish preflight
                    if rule.rule_source == "inferred_disabled":
                        continue
                    if rule.required:
                        if f.internal_key not in canonical_fields or not canonical_fields[f.internal_key]:
                            official_errors.append(f"OFFICIAL_REQUIRED_FIELD_MISSING: Поле '{f.display_name}' ({f.official_tag}) обязательно")

        if not official_errors and is_valid_base:
            ready_for_official_autoload = True
        else:
            errors.extend(official_errors)

    ready_for_any_publication = ready_for_browser_assisted or ready_for_manual or ready_for_official_autoload

    return {
        "ready_for_any_publication": ready_for_any_publication,
        "ready_for_official_autoload": ready_for_official_autoload,
        "ready_for_browser_assisted": ready_for_browser_assisted,
        "ready_for_manual": ready_for_manual,
        "product_id": product.id,
        "canonical_category": projection.get("canonical_category_name"),
        "official_slug": projection.get("official_slug"),
        "fields": canonical_fields,
        "errors": errors,
        "warnings": warnings,
        "unresolved_fields": unresolved
    }
