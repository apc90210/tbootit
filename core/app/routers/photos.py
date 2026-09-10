import os
import uuid
import hashlib
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.database import get_db
from app import models, schemas, storage
from app.storage import check_persistent_photo_storage
from app.routers.customers import log_audit

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/pjpeg"
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

def _validate_and_save_photo(upload_file: UploadFile, product_id: int, db: Session) -> models.ProductPhoto:
    filename = upload_file.filename or "photo.jpg"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый формат файла '{filename}'. Разрешены только JPEG, PNG, WebP."
        )

    ct = (upload_file.content_type or "").lower()
    if ct and not (ct in ALLOWED_MIME_TYPES or ct.startswith("image/")):
        raise HTTPException(
            status_code=400,
            detail=f"Файл '{filename}' не является допустимым изображением."
        )

    ok, storage_err = check_persistent_photo_storage()
    if not ok:
        raise HTTPException(
            status_code=503,
            detail=f"Хранилище фотографий временно недоступно: {storage_err}"
        )

    content = upload_file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Файл '{filename}' превышает лимит 15 МБ."
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Файл '{filename}' пустой."
        )

    content_hash = hashlib.sha256(content).hexdigest()
    safe_filename = f"{product_id}_{uuid.uuid4().hex[:8]}{ext}"
    target_dir = os.path.join(storage.get_product_photos_dir(), str(product_id))
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    max_order = db.query(func.max(models.ProductPhoto.sort_order)).filter(
        models.ProductPhoto.product_id == product_id
    ).scalar()
    next_order = (max_order + 1) if max_order is not None else 0

    media_url = f"/media/product_photos/{product_id}/{safe_filename}"
    db_photo = models.ProductPhoto(
        product_id=product_id,
        filename=safe_filename,
        storage_path=file_path,
        media_url=media_url,
        content_hash=content_hash,
        sort_order=next_order
    )
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)

    log_audit(db, "product_photo", db_photo.id, "create", comment=f"Uploaded photo {safe_filename} for product {product_id}")
    db.commit()
    return db_photo

@router.post("/{product_id}/photos", response_model=schemas.ProductPhoto)
def upload_photo(product_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return _validate_and_save_photo(file, product_id, db)

@router.post("/{product_id}/photos/batch")
def upload_photos_batch(product_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    uploaded = []
    errors = []
    for f in files:
        try:
            photo = _validate_and_save_photo(f, product_id, db)
            uploaded.append({
                "id": photo.id,
                "filename": photo.filename,
                "media_url": photo.media_url,
                "sort_order": photo.sort_order
            })
        except HTTPException as e:
            errors.append({"filename": f.filename, "error": e.detail})
        except Exception as e:
            errors.append({"filename": f.filename, "error": str(e)})

    return {
        "uploaded": uploaded,
        "errors": errors,
        "total_uploaded": len(uploaded),
        "total_errors": len(errors)
    }

@router.get("/{product_id}/photos", response_model=List[schemas.ProductPhoto])
def get_product_photos(product_id: int, db: Session = Depends(get_db)):
    return db.query(models.ProductPhoto).filter(
        models.ProductPhoto.product_id == product_id
    ).order_by(models.ProductPhoto.sort_order.asc(), models.ProductPhoto.id.asc()).all()

@router.post("/{product_id}/photos/reorder")
def reorder_photos(product_id: int, payload: schemas.PhotoReorderRequest, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    for idx, pid in enumerate(payload.photo_ids):
        photo = db.query(models.ProductPhoto).filter(
            models.ProductPhoto.id == pid,
            models.ProductPhoto.product_id == product_id
        ).first()
        if photo:
            photo.sort_order = idx

    db.commit()
    return db.query(models.ProductPhoto).filter(
        models.ProductPhoto.product_id == product_id
    ).order_by(models.ProductPhoto.sort_order.asc(), models.ProductPhoto.id.asc()).all()

@router.post("/{product_id}/photos/{photo_id}/make-main")
def make_photo_main(product_id: int, photo_id: int, db: Session = Depends(get_db)):
    target_photo = db.query(models.ProductPhoto).filter(
        models.ProductPhoto.id == photo_id,
        models.ProductPhoto.product_id == product_id
    ).first()
    if not target_photo:
        raise HTTPException(status_code=404, detail="Фотография не найдена")

    all_photos = db.query(models.ProductPhoto).filter(
        models.ProductPhoto.product_id == product_id
    ).order_by(models.ProductPhoto.sort_order.asc(), models.ProductPhoto.id.asc()).all()

    target_photo.sort_order = 0
    order = 1
    for ph in all_photos:
        if ph.id != photo_id:
            ph.sort_order = order
            order += 1

    db.commit()
    return db.query(models.ProductPhoto).filter(
        models.ProductPhoto.product_id == product_id
    ).order_by(models.ProductPhoto.sort_order.asc(), models.ProductPhoto.id.asc()).all()

@router.delete("/{product_id}/photos/{photo_id}")
def delete_photo(product_id: int, photo_id: int, db: Session = Depends(get_db)):
    db_photo = db.query(models.ProductPhoto).filter(
        models.ProductPhoto.id == photo_id,
        models.ProductPhoto.product_id == product_id
    ).first()
    if not db_photo:
        raise HTTPException(status_code=404, detail="Фотография не найдена")

    storage.delete_file_from_storage(product_id, db_photo.filename)

    was_main = (db_photo.sort_order == 0)
    db.delete(db_photo)
    db.commit()

    if was_main:
        first_remaining = db.query(models.ProductPhoto).filter(
            models.ProductPhoto.product_id == product_id
        ).order_by(models.ProductPhoto.sort_order.asc(), models.ProductPhoto.id.asc()).first()
        if first_remaining:
            first_remaining.sort_order = 0
            db.commit()

    log_audit(db, "product_photo", photo_id, "delete", comment=f"Deleted photo for product {product_id}")
    db.commit()

    return {"message": "Фотография успешно удалена"}

