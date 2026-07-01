from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.routers.customers import log_audit
import json

router = APIRouter()

@router.get("/", response_model=List[schemas.Sale])
def get_sales(db: Session = Depends(get_db)):
    return db.query(models.Sale).all()

@router.post("/", response_model=schemas.Sale)
def create_sale(sale: schemas.SaleCreate, db: Session = Depends(get_db)):
    sale_data = sale.model_dump()
    items_data = sale_data.pop("items")
    
    db_sale = models.Sale(**sale_data)
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    for item in items_data:
        db_item = models.SaleItem(**item, sale_id=db_sale.id)
        db.add(db_item)
        # Update product status to sold
        db_product = db.query(models.Product).filter(models.Product.id == item["product_id"]).first()
        if db_product:
            db_product.status = "sold"
            log_audit(db, "product", db_product.id, "update_status", old_value={"status": "previous"}, new_value={"status": "sold"}, comment=f"Sold in sale {db_sale.id}")

    db.commit()
    db.refresh(db_sale)
    
    log_audit(db, "sale", db_sale.id, "create", new_value={"total_amount": sale.total_amount})
    db.commit()
    
    return db_sale

@router.get("/{sale_id}", response_model=schemas.Sale)
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return db_sale
