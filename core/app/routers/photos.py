from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, storage
from app.routers.customers import log_audit
import os

router = APIRouter()

@router.post("/{product_id}/photos", response_model=schemas.ProductPhoto)
def upload_photo(product_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    filename = file.filename
    file_path = storage.save_upload_file_to_storage(file, product_id, filename)
    
    media_url = f"/media/product_photos/{product_id}/{filename}"
    
    db_photo = models.ProductPhoto(
        product_id=product_id,
        filename=filename,
        storage_path=file_path,
        media_url=media_url
    )
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    
    log_audit(db, "product_photo", db_photo.id, "create", comment=f"Uploaded photo {filename} for product {product_id}")
    db.commit()
    return db_photo

@router.get("/{product_id}/photos", response_model=List[schemas.ProductPhoto])
def get_product_photos(product_id: int, db: Session = Depends(get_db)):
    return db.query(models.ProductPhoto).filter(models.ProductPhoto.product_id == product_id).all()

@router.delete("/{product_id}/photos/{photo_id}")
def delete_photo(product_id: int, photo_id: int, db: Session = Depends(get_db)):
    db_photo = db.query(models.ProductPhoto).filter(models.ProductPhoto.id == photo_id, models.ProductPhoto.product_id == product_id).first()
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
        
    storage.delete_file_from_storage(product_id, db_photo.filename)
    
    db.delete(db_photo)
    db.commit()
    
    log_audit(db, "product_photo", photo_id, "delete", comment=f"Deleted photo for product {product_id}")
    db.commit()
    
    return {"message": "Photo deleted successfully"}
