from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.database import get_db
from app import models, schemas
from app.routers.customers import log_audit
import json

router = APIRouter()

def log_product_event(db: Session, product_id: int, event_type: str, old_value=None, new_value=None, comment=None):
    old_val_str = json.dumps(old_value, default=str) if old_value else None
    new_val_str = json.dumps(new_value, default=str) if new_value else None
    ev = models.ProductEvent(
        product_id=product_id,
        event_type=event_type,
        old_value=old_val_str,
        new_value=new_val_str,
        comment=comment
    )
    db.add(ev)
    return ev

@router.get("/", response_model=schemas.ProductListResponse)
def get_products(
    q: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    storage_location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    avito_ready: Optional[bool] = None,
    site_ready: Optional[bool] = None,
    sort: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)
    
    if q:
        query = query.filter(
            or_(
                models.Product.title.ilike(f"%{q}%"),
                models.Product.sku.ilike(f"%{q}%"),
                models.Product.brand.ilike(f"%{q}%"),
                models.Product.model.ilike(f"%{q}%"),
                models.Product.serial_number.ilike(f"%{q}%")
            )
        )
    if status:
        query = query.filter(models.Product.status == status)
    if source:
        query = query.filter(models.Product.source_type == source)
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if brand:
        query = query.filter(models.Product.brand.ilike(f"%{brand}%"))
    if storage_location:
        query = query.filter(models.Product.storage_location.ilike(f"%{storage_location}%"))
    if min_price is not None:
        query = query.filter(models.Product.sale_price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.sale_price <= max_price)
    if avito_ready is not None:
        if avito_ready:
            query = query.filter(models.Product.avito_title != None, models.Product.avito_description != None)
        else:
            query = query.filter(or_(models.Product.avito_title == None, models.Product.avito_description == None))
    if site_ready is not None:
        if site_ready:
            query = query.filter(models.Product.site_title != None, models.Product.site_description != None)
        else:
            query = query.filter(or_(models.Product.site_title == None, models.Product.site_description == None))
            
    if sort == "price_asc":
        query = query.order_by(models.Product.sale_price.asc())
    elif sort == "price_desc":
        query = query.order_by(models.Product.sale_price.desc())
    elif sort == "created_asc":
        query = query.order_by(models.Product.created_at.asc())
    elif sort == "created_desc":
        query = query.order_by(models.Product.created_at.desc())
    else:
        query = query.order_by(models.Product.id.desc())
        
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/meta")
def get_meta(db: Session = Depends(get_db)):
    statuses = {
        "draft": "Черновик",
        "in_stock": "В наличии",
        "reserved": "Зарезервирован",
        "sold": "Продан",
        "in_repair": "В ремонте",
        "for_parts": "На запчасти",
        "written_off": "Списан",
        "published_site": "На сайте",
        "published_avito": "На Авито"
    }
    repair_statuses = {
        "new": "Новая заявка",
        "accepted": "Принято",
        "diagnostics": "Диагностика",
        "waiting_parts": "Ожидание запчастей",
        "in_progress": "В работе",
        "ready": "Готово",
        "issued": "Выдано",
        "cancelled": "Отменено"
    }
    brands = [r[0] for r in db.query(models.Product.brand).filter(models.Product.brand != None).distinct()]
    locations = [r[0] for r in db.query(models.Product.storage_location).filter(models.Product.storage_location != None).distinct()]
    
    return {
        "product_statuses": statuses,
        "repair_statuses": repair_statuses,
        "brands": brands,
        "storage_locations": locations
    }

@router.post("/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    log_audit(db, "product", db_product.id, "create", new_value=product.model_dump())
    log_product_event(db, db_product.id, "create", comment="Product created")
    
    if db_product.quantity and db_product.quantity > 0:
        mov = models.StockMovement(
            product_id=db_product.id,
            movement_type="initial",
            quantity_delta=db_product.quantity,
            old_quantity=0,
            new_quantity=db_product.quantity,
            reason="initial_stock"
        )
        db.add(mov)
        
    db.commit()
    return db_product

@router.get("/{product_id}/details", response_model=schemas.ProductDetails)
def get_product_details(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    photos = db.query(models.ProductPhoto).filter(models.ProductPhoto.product_id == product_id).order_by(models.ProductPhoto.sort_order).all()
    events = db.query(models.ProductEvent).filter(models.ProductEvent.product_id == product_id).order_by(models.ProductEvent.created_at.desc()).all()
    movements = db.query(models.StockMovement).filter(models.StockMovement.product_id == product_id).order_by(models.StockMovement.created_at.desc()).all()
    
    margin = None
    if db_product.sale_price and db_product.purchase_price:
        margin = db_product.sale_price - db_product.purchase_price
        
    available = (db_product.quantity or 0) - (db_product.reserved_quantity or 0)
    
    # We must convert to dict first because we need to add fields not present in the DB model directly, or use model_validate/dump
    p_dict = {c.name: getattr(db_product, c.name) for c in db_product.__table__.columns}
    p_dict["margin"] = margin
    p_dict["available_quantity"] = available
    p_dict["has_photos"] = len(photos) > 0
    p_dict["avito_ready"] = bool(db_product.avito_title and db_product.avito_description and db_product.avito_price if hasattr(db_product, 'avito_price') else True)
    p_dict["site_ready"] = bool(db_product.site_title and db_product.site_description)
    p_dict["photos"] = photos
    p_dict["events"] = events
    p_dict["stock_movements"] = movements
    
    return p_dict

@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.patch("/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.sale_price is not None and product.sale_price < 0:
        raise HTTPException(status_code=400, detail="Price must be non-negative")
    if product.purchase_price is not None and product.purchase_price < 0:
        raise HTTPException(status_code=400, detail="Price must be non-negative")
    if product.title is not None and len(product.title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
        
    if product.status is not None:
        raise HTTPException(status_code=400, detail="Use /status endpoint to update status")
    
    old_data = {c.name: getattr(db_product, c.name) for c in db_product.__table__.columns}
    update_data = product.model_dump(exclude_unset=True)
    if "status" in update_data:
        del update_data["status"]
        
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    
    new_data = {c.name: getattr(db_product, c.name) for c in db_product.__table__.columns}
    log_audit(db, "product", db_product.id, "update", old_value=old_data, new_value=new_data)
    log_product_event(db, db_product.id, "update", old_value=old_data, new_value=new_data, comment="Product updated")
    db.commit()
    return db_product

VALID_TRANSITIONS = {
    "draft": ["in_stock", "archived", "imported", "reserved", "sold", "written_off"],
    "imported": ["in_stock", "archived", "reserved", "sold", "written_off"],
    "in_stock": ["reserved", "sold", "written_off", "archived"],
    "reserved": ["in_stock", "sold", "archived"],
    "sold": ["archived"],
    "written_off": ["archived"],
    "archived": ["imported", "draft", "in_stock"]
}

@router.post("/{product_id}/status", response_model=schemas.Product)
def update_product_status(product_id: int, status_update: schemas.ProductStatusUpdate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_status = db_product.status or "draft"
    new_status = status_update.status
    
    allowed = VALID_TRANSITIONS.get(old_status, [])
    if new_status not in allowed and old_status != new_status:
        raise HTTPException(status_code=400, detail=f"Invalid transition from {old_status} to {new_status}")
    
    db_product.status = new_status
    db.commit()
    db.refresh(db_product)
    
    log_audit(db, "product", db_product.id, "update_status", old_value={"status": old_status}, new_value={"status": new_status})
    log_product_event(db, db_product.id, "update_status", old_value=old_status, new_value=new_status, comment=status_update.reason or "Status changed")
    db.commit()
    return db_product

@router.get("/{product_id}/events", response_model=List[schemas.ProductEvent])
def get_product_events(product_id: int, db: Session = Depends(get_db)):
    return db.query(models.ProductEvent).filter(models.ProductEvent.product_id == product_id).order_by(models.ProductEvent.created_at.desc()).all()

@router.post("/{product_id}/events", response_model=schemas.ProductEvent)
def create_product_event(product_id: int, event: schemas.ProductEventCreate, db: Session = Depends(get_db)):
    ev = log_product_event(db, product_id, event.event_type, event.old_value, event.new_value, event.comment)
    db.commit()
    db.refresh(ev)
    return ev

@router.post("/{product_id}/stock-adjustment", response_model=schemas.Product)
def adjust_stock(product_id: int, adj: schemas.StockAdjustment, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    old_q = db_product.quantity or 0
    new_q = old_q + adj.quantity_delta
    db_product.quantity = new_q
    
    mov = models.StockMovement(
        product_id=product_id,
        movement_type="manual_adjustment",
        quantity_delta=adj.quantity_delta,
        old_quantity=old_q,
        new_quantity=new_q,
        reason=adj.reason,
        comment=adj.comment
    )
    db.add(mov)
    
    log_product_event(db, product_id, "stock_adjustment", old_value=old_q, new_value=new_q, comment=adj.comment)
    log_audit(db, "product", product_id, "stock_adjustment", old_value={"quantity": old_q}, new_value={"quantity": new_q}, comment=adj.comment)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.patch("/{product_id}/site-publication", response_model=schemas.Product)
def site_publication(product_id: int, pub: schemas.SitePublication, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_product.is_published_site = pub.is_published_site
    if pub.site_title is not None:
        db_product.site_title = pub.site_title
    if pub.site_description is not None:
        db_product.site_description = pub.site_description
        
    log_product_event(db, product_id, "site_publication_prep", new_value=pub.model_dump(), comment="Prepared for site")
    db.commit()
    db.refresh(db_product)
    return db_product

@router.patch("/{product_id}/avito-publication", response_model=schemas.Product)
def avito_publication(product_id: int, pub: schemas.AvitoPublication, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_product.is_published_avito = pub.is_published_avito
    if pub.avito_title is not None:
        db_product.avito_title = pub.avito_title
    if pub.avito_description is not None:
        db_product.avito_description = pub.avito_description
        
    log_product_event(db, product_id, "avito_publication_prep", new_value=pub.model_dump(), comment="Prepared for Avito")
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_status = db_product.status
    db_product.status = "written_off"
    db.commit()
    
    log_audit(db, "product", db_product.id, "delete_soft", old_value={"status": old_status}, new_value={"status": "written_off"})
    log_product_event(db, product_id, "delete_soft", old_value=old_status, new_value="written_off", comment="Product softly deleted (written_off)")
    db.commit()
    return {"message": "Product softly deleted (written_off)"}
