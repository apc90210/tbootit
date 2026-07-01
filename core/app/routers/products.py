from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.routers.customers import log_audit
import json

router = APIRouter()

@router.get("/", response_model=List[schemas.Product])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@router.post("/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    log_audit(db, "product", db_product.id, "create", new_value=product.model_dump())
    db.commit()
    return db_product

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
    
    old_data = {c.name: getattr(db_product, c.name) for c in db_product.__table__.columns}
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    
    new_data = {c.name: getattr(db_product, c.name) for c in db_product.__table__.columns}
    log_audit(db, "product", db_product.id, "update", old_value=old_data, new_value=new_data)
    db.commit()
    return db_product

@router.patch("/{product_id}/status", response_model=schemas.Product)
def update_product_status(product_id: int, status_update: schemas.ProductStatusUpdate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_status = db_product.status
    db_product.status = status_update.status
    db.commit()
    db.refresh(db_product)
    
    log_audit(db, "product", db_product.id, "update_status", old_value={"status": old_status}, new_value={"status": status_update.status})
    db.commit()
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
    db.commit()
    return {"message": "Product softly deleted (written_off)"}
