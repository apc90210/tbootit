from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, date
from app.database import get_db
from app import models, schemas
from app.routers.customers import log_audit
from app.routers.products import log_product_event

router = APIRouter()

VALID_PAYMENT_METHODS = ["cash", "card", "transfer", "mixed", "other"]

@router.get("/", response_model=schemas.SaleListResponse)
def get_sales(
    limit: int = 50,
    offset: int = 0,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    payment_method: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Sale)
    
    if date_from:
        query = query.filter(models.Sale.created_at >= date_from)
    if date_to:
        query = query.filter(models.Sale.created_at <= date_to)
    if payment_method:
        query = query.filter(models.Sale.payment_method == payment_method)
    if customer_id:
        query = query.filter(models.Sale.customer_id == customer_id)
        
    query = query.order_by(models.Sale.created_at.desc())
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/today", response_model=schemas.SaleListResponse)
def get_sales_today(db: Session = Depends(get_db)):
    today = date.today()
    query = db.query(models.Sale).filter(models.Sale.created_at >= today).order_by(models.Sale.created_at.desc())
    total = query.count()
    items = query.all()
    
    return {
        "items": items,
        "total": total,
        "limit": 1000,
        "offset": 0
    }

@router.post("/", response_model=schemas.Sale)
def create_sale(sale: schemas.SaleCreate, db: Session = Depends(get_db)):
    if sale.payment_method not in VALID_PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail=f"Invalid payment method. Allowed: {', '.join(VALID_PAYMENT_METHODS)}")
        
    if not sale.items:
        raise HTTPException(status_code=400, detail="Sale must contain at least one item")

    # Validate items before processing
    product_ids = set()
    for item in sale.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Item quantity must be > 0")
        if item.price < 0:
            raise HTTPException(status_code=400, detail="Item price must be >= 0")
        if item.product_id in product_ids:
            raise HTTPException(status_code=400, detail=f"Duplicate product_id {item.product_id} in sale")
        product_ids.add(item.product_id)
        
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if db_product.status not in ["in_stock", "reserved"]:
            raise HTTPException(status_code=400, detail=f"Cannot sell product {item.product_id} in status '{db_product.status}'")

    sale_data = sale.model_dump()
    items_data = sale_data.pop("items")
    
    sale_data["warranty_enabled"] = 1 if sale_data.get("warranty_enabled") else 0
    
    db_sale = models.Sale(**sale_data)
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    for item in items_data:
        db_item = models.SaleItem(**item, sale_id=db_sale.id)
        db.add(db_item)
        
        db_product = db.query(models.Product).filter(models.Product.id == item["product_id"]).first()
        old_status = db_product.status
        db_product.status = "sold"
        
        log_product_event(db, db_product.id, "sale_completed", old_value={"status": old_status}, new_value={"status": "sold"}, comment=f"Sold in sale {db_sale.id}. Price: {item['price']}")

    db.commit()
    db.refresh(db_sale)
    
    log_audit(db, "sale", db_sale.id, "create", new_value={"total_amount": sale.total_amount, "payment_method": sale.payment_method})
    db.commit()
    
    return db_sale

@router.get("/{sale_id}", response_model=schemas.Sale)
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return db_sale

@router.post("/{sale_id}/cancel", response_model=schemas.Sale)
def cancel_sale(sale_id: int, cancel_data: schemas.SaleCancel, db: Session = Depends(get_db)):
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    if db_sale.status == "cancelled":
        raise HTTPException(status_code=400, detail="Sale is already cancelled")
        
    db_sale.status = "cancelled"
    db_sale.cancelled_at = datetime.utcnow()
    db_sale.cancel_reason = cancel_data.reason
    
    sale_items = db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).all()
    for item in sale_items:
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if db_product and db_product.status == "sold":
            db_product.status = "in_stock"
            log_product_event(db, db_product.id, "sale_cancelled", old_value={"status": "sold"}, new_value={"status": "in_stock"}, comment=f"Sale {sale_id} cancelled: {cancel_data.reason}")
            
    log_audit(db, "sale", db_sale.id, "cancel", new_value={"status": "cancelled", "reason": cancel_data.reason})
    db.commit()
    db.refresh(db_sale)
    return db_sale
