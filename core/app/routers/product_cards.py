from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import Product, ProductCardImport, Category, ProductEvent
from app.schemas import ProductCardJSONPayload, ProductCardImportSchema
import json

router = APIRouter()

@router.post("/validate-json")
def validate_json(payload: ProductCardJSONPayload):
    errors = []
    warnings = []
    
    # 1. Check required fields
    if not payload.product.sku:
        errors.append("Не указан артикул (sku) товара.")
    if not payload.product.title:
        errors.append("Не указано название (title) товара.")
        
    # 2. Check avito structure
    if not payload.avito:
        warnings.append("Отсутствует секция Авито.")
    else:
        if not payload.avito.phone:
            warnings.append("Не указан телефон для Авито.")
        if not payload.avito.price:
            warnings.append("Не указана цена для Авито.")
            
    # 3. Check pricing
    if payload.product.sale_price is None and (payload.avito and payload.avito.price is None):
        warnings.append("Не указана цена продажи.")
        
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

@router.post("/import-json")
def import_json(payload: ProductCardJSONPayload, db: Session = Depends(get_db)):
    # 1. Validate
    val_res = validate_json(payload)
    if not val_res["valid"]:
        # Log failed import
        db_import = ProductCardImport(
            source_type=payload.source,
            source_json=payload.model_dump_json(),
            validation_status="invalid",
            validation_errors=json.dumps(val_res["errors"], ensure_ascii=False)
        )
        db.add(db_import)
        db.commit()
        raise HTTPException(status_code=400, detail={"msg": "Invalid JSON", "errors": val_res["errors"]})

    warnings = val_res["warnings"]
    operation = "created"

    # 2. Map category
    cat_id = None
    if payload.product.category_path:
        cat_name = payload.product.category_path[-1] # take last node as category
        cat = db.query(Category).filter(Category.name == cat_name).first()
        if not cat:
            cat = Category(name=cat_name, slug=cat_name.lower().replace(" ", "-"))
            db.add(cat)
            db.commit()
            db.refresh(cat)
        cat_id = cat.id

    # 3. Find existing product
    product = db.query(Product).filter(Product.sku == payload.product.sku).first()
    
    if product:
        operation = "updated"
        # Log event
        db_event = ProductEvent(
            product_id=product.id,
            event_type="json_import_update",
            comment="Updated via JSON import"
        )
        db.add(db_event)
    else:
        product = Product(sku=payload.product.sku)
        db.add(product)
        db.flush()
        # Log event
        db_event = ProductEvent(
            product_id=product.id,
            event_type="json_import_create",
            comment="Created via JSON import"
        )
        db.add(db_event)

    # 4. Map fields
    product.title = payload.product.title
    if cat_id: product.category_id = cat_id
    product.brand = payload.product.brand
    product.model = payload.product.model
    product.serial_number = payload.product.serial_number
    product.condition = payload.product.condition
    product.description = payload.product.description
    product.purchase_price = payload.product.purchase_price
    product.sale_price = payload.product.sale_price
    product.min_price = payload.product.min_price
    product.market_price = payload.product.market_price
    product.quantity = payload.product.quantity
    product.storage_location = payload.product.storage_location
    product.notes = payload.product.notes

    # Map Avito
    if payload.avito:
        product.avito_title = payload.avito.title
        product.avito_description = payload.avito.description
        if payload.avito.category_path:
            product.avito_category_path = json.dumps(payload.avito.category_path, ensure_ascii=False)
        product.avito_goods_type = payload.avito.goods_type
        product.avito_condition = payload.avito.condition
        if payload.avito.parameters:
            product.avito_params_json = json.dumps(payload.avito.parameters, ensure_ascii=False)
        product.avito_contact_name = payload.avito.contact_name
        product.avito_phone = payload.avito.phone
        product.avito_address = payload.avito.address
        product.avito_seller_type = payload.avito.seller_type

    # Map Site
    if payload.site:
        product.site_title = payload.site.title
        product.site_description = payload.site.description
        product.is_published_site = 1 if payload.site.publish_ready else 0
        
    # Map Source Metadata
    product.source_json = payload.model_dump_json()
    product.source_type = payload.source
    from datetime import datetime
    product.last_imported_at = datetime.utcnow()

    # Save to db
    db.commit()
    db.refresh(product)

    # 5. Log import success
    db_import = ProductCardImport(
        product_id=product.id,
        source_type=payload.source,
        source_json=payload.model_dump_json(),
        validation_status="success",
        validation_errors=json.dumps(warnings, ensure_ascii=False)
    )
    db.add(db_import)
    db.commit()

    return {
        "status": "imported",
        "operation": operation,
        "product_id": product.id,
        "sku": product.sku,
        "warnings": warnings
    }

@router.get("/imports", response_model=List[ProductCardImportSchema])
def list_imports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(ProductCardImport).order_by(ProductCardImport.id.desc()).offset(skip).limit(limit).all()
