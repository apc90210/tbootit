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

VALID_PAYMENT_METHODS = ["cash", "card", "transfer", "sbp", "legal_entity_account", "mixed", "other"]

@router.get("/", response_model=schemas.SaleListResponse)
def get_sales(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    payment_method: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Sale)
    
    if status:
        query = query.filter(models.Sale.status == status)
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
        if db_product.storage_location != "store":
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} must be in 'store' location to be sold")
        if (db_product.quantity or 0) < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient quantity for product {item.product_id}. Available: {db_product.quantity or 0}")

    sale_data = sale.model_dump()
    items_data = sale_data.pop("items")
    
    sale_data["warranty_enabled"] = 1 if sale_data.get("warranty_enabled") else 0
    sale_data["status"] = "completed"
    
    db_sale = models.Sale(**sale_data)
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    for item in items_data:
        db_item = models.SaleItem(**item, sale_id=db_sale.id)
        db.add(db_item)
        
        db_product = db.query(models.Product).filter(models.Product.id == item["product_id"]).first()
        old_status = db_product.status
        old_quantity = db_product.quantity or 0
        db_product.quantity = old_quantity - item["quantity"]
        
        mov = models.StockMovement(
            product_id=db_product.id,
            movement_type="sale",
            quantity_delta=-item["quantity"],
            old_quantity=old_quantity,
            new_quantity=db_product.quantity,
            reason="sale",
            comment=f"Sale {db_sale.id}"
        )
        db.add(mov)

        if db_product.quantity == 0:
            db_product.status = "sold"
        
        log_product_event(db, db_product.id, "sale_completed", old_value={"status": old_status, "quantity": old_quantity}, new_value={"status": db_product.status, "quantity": db_product.quantity}, comment=f"Sold {item['quantity']} items in sale {db_sale.id}. Price: {item['price']}")

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
    if db_sale.status in ["canceled", "cancelled", "superseded"]:
        raise HTTPException(status_code=409, detail=f"Sale cannot be canceled (status: {db_sale.status})")
        
    db_sale.status = "canceled"
    db_sale.cancelled_at = datetime.utcnow()
    db_sale.cancel_reason = cancel_data.reason
    db_sale.canceled_by = cancel_data.canceled_by or "Администратор"
    
    sale_items = db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).all()
    for item in sale_items:
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if db_product:
            old_quantity = db_product.quantity or 0
            db_product.quantity = old_quantity + item.quantity
            
            mov = models.StockMovement(
                product_id=db_product.id,
                movement_type="sale_cancel",
                quantity_delta=item.quantity,
                old_quantity=old_quantity,
                new_quantity=db_product.quantity,
                reason="sale_cancel",
                comment=f"Sale {db_sale.id} canceled"
            )
            db.add(mov)

            old_status = db_product.status
            if db_product.status == "sold" and db_product.quantity > 0:
                db_product.status = "in_stock"
                
            log_product_event(db, db_product.id, "sale_canceled", old_value={"status": old_status, "quantity": old_quantity}, new_value={"status": db_product.status, "quantity": db_product.quantity}, comment=f"Sale {sale_id} canceled: {cancel_data.reason}")
            
    log_audit(db, "sale", db_sale.id, "cancel", new_value={"status": "canceled", "reason": cancel_data.reason, "canceled_by": db_sale.canceled_by})
    db.commit()
    db.refresh(db_sale)
    return db_sale

@router.post("/{sale_id}/reissue", response_model=schemas.Sale)
def reissue_sale(sale_id: int, reissue_data: schemas.SaleReissue, db: Session = Depends(get_db)):
    db_old_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_old_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
        
    if db_old_sale.status == "superseded" or db_old_sale.superseded_by_sale_id is not None or db_old_sale.replaced_by_sale_id is not None:
        raise HTTPException(status_code=409, detail="Original sale was already superseded")
        
    if db_old_sale.status not in ["canceled", "cancelled"]:
        raise HTTPException(status_code=400, detail="Only canceled sales can be reissued")
        
    if reissue_data.payment_method not in VALID_PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail=f"Invalid payment method. Allowed: {', '.join(VALID_PAYMENT_METHODS)}")
        
    if not reissue_data.items:
        raise HTTPException(status_code=400, detail="Sale must contain at least one item")

    # Validate items before processing
    product_ids = set()
    for item in reissue_data.items:
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
        if db_product.storage_location != "store":
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} must be in 'store' location to be sold")
        if (db_product.quantity or 0) < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient quantity for product {item.product_id}. Available: {db_product.quantity or 0}")

    total_amount = sum(item.price * item.quantity for item in reissue_data.items)

    new_sale = models.Sale(
        customer_id=db_old_sale.customer_id,
        total_amount=total_amount,
        payment_method=reissue_data.payment_method,
        comment=f"Reissue of sale #{sale_id}",
        status="reissued",
        warranty_days=db_old_sale.warranty_days,
        warranty_enabled=db_old_sale.warranty_enabled,
        source_sale_id=sale_id,
        original_sale_id=sale_id,
        reissued_at=datetime.utcnow()
    )
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    
    db_old_sale.status = "superseded"
    db_old_sale.superseded_by_sale_id = new_sale.id
    db_old_sale.replaced_by_sale_id = new_sale.id
    
    for item in reissue_data.items:
        db_item = models.SaleItem(**item.model_dump(), sale_id=new_sale.id)
        db.add(db_item)
        
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        old_q = db_product.quantity or 0
        db_product.quantity = old_q - item.quantity
        
        mov = models.StockMovement(
            product_id=db_product.id,
            movement_type="sale_reissue_deduct",
            quantity_delta=-item.quantity,
            old_quantity=old_q,
            new_quantity=db_product.quantity,
            reason="sale_reissue_deduct",
            comment=f"Stock deduct for sale {new_sale.id} reissue"
        )
        db.add(mov)
        
        old_s = db_product.status
        if db_product.quantity == 0:
            db_product.status = "sold"
            
        log_product_event(db, db_product.id, "sale_reissue_deduct", old_value={"status": old_s, "quantity": old_q}, new_value={"status": db_product.status, "quantity": db_product.quantity}, comment=f"Deducted for sale {new_sale.id}")

    log_audit(db, "sale", db_old_sale.id, "superseded", old_value={"status": "canceled"}, new_value={"status": "superseded", "superseded_by_sale_id": new_sale.id})
    log_audit(db, "sale", new_sale.id, "reissued", new_value={"status": "reissued", "source_sale_id": sale_id})
    db.commit()
    db.refresh(new_sale)
    return new_sale
