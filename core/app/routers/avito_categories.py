from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/v1/avito/categories", tags=["avito-categories"])
product_router = APIRouter(prefix="/api/v1/products", tags=["products-avito-attributes"])

@router.get("", response_model=List[schemas.AvitoCategorySchema])
def list_avito_categories(db: Session = Depends(get_db)):
    """Retrieve stored Avito categories."""
    return db.query(models.AvitoCategory).filter(models.AvitoCategory.is_active == True).all()

@router.get("/{category_id}/schema", response_model=schemas.AvitoCategorySchema)
def get_avito_category_schema(category_id: int, db: Session = Depends(get_db)):
    """Retrieve Avito category schema definitions and allowed options."""
    category = db.query(models.AvitoCategory).filter(models.AvitoCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория Avito не найдена.")
    return category

@product_router.get("/{product_id}/avito-attributes", response_model=schemas.ProductAvitoAttributesResponse)
def get_product_avito_attributes(product_id: int, db: Session = Depends(get_db)):
    """Retrieve product Avito category binding and dynamic attribute values."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден.")

    avito_cat_schema = None
    if product.avito_category:
        avito_cat_schema = schemas.AvitoCategorySchema.model_validate(product.avito_category)

    attr_values = db.query(models.ProductAvitoAttributeValue).filter(
        models.ProductAvitoAttributeValue.product_id == product_id
    ).all()

    attributes_list = []
    for val_row in attr_values:
        def_model = val_row.definition
        val_schema = schemas.ProductAvitoAttributeValueSchema(
            id=val_row.id,
            product_id=val_row.product_id,
            attribute_definition_id=val_row.attribute_definition_id,
            option_id=val_row.option_id,
            external_key=def_model.external_key if def_model else None,
            attribute_name=def_model.name if def_model else None,
            value=val_row.value,
            raw_value=val_row.raw_value,
            source=val_row.source or "avito",
            updated_at=val_row.updated_at
        )
        attributes_list.append(val_schema)

    return schemas.ProductAvitoAttributesResponse(
        product_id=product_id,
        avito_category=avito_cat_schema,
        attributes=attributes_list
    )
