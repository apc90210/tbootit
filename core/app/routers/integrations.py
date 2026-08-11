import os
import uuid
import base64
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.config import settings

router = APIRouter()

def log_audit(db: Session, entity_type: str, entity_id: int, action: str, old_value: Any = None, new_value: Any = None):
    log = models.AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_value=json.dumps(old_value, ensure_ascii=False) if old_value else None,
        new_value=json.dumps(new_value, ensure_ascii=False) if new_value else None
    )
    db.add(log)

@router.post("/avito/import-item", response_model=schemas.AvitoItemImportResponse, status_code=200)
def import_avito_item(payload: schemas.AvitoItemImportPayload, db: Session = Depends(get_db)):
    """
    Idempotent upsert of an Avito listing into Technoreboot catalog.
    1. Looks up existing ProductExternalListing by (marketplace='avito', external_item_id=payload.external_item_id).
    2. If found: updates linked Product and ProductExternalListing metadata.
    3. If not found: creates a new Product and ProductExternalListing.
    4. Idempotently imports photos using SHA256 content hash.
    5. Logs audit event: avito.product_imported or avito.product_updated, avito.external_link_created or avito.external_link_updated.
    """
    now = datetime.utcnow()
    
    # 1. Lookup external listing link
    ext_link = db.query(models.ProductExternalListing).filter(
        models.ProductExternalListing.marketplace == "avito",
        models.ProductExternalListing.external_item_id == payload.external_item_id
    ).first()

    status_str = "updated"
    product = None
    created_product = False
    created_link = False

    if ext_link:
        product = db.query(models.Product).filter(models.Product.id == ext_link.product_id).first()

    if not product:
        # Create new product
        created_product = True
        status_str = "created"
        sku = f"AVITO-{payload.external_item_id}"

        # Resolve category if category_path provided
        category_id = None
        if payload.category_path:
            cat_name = payload.category_path[-1]
            cat = db.query(models.Category).filter(models.Category.name == cat_name).first()
            if not cat:
                cat_slug = hashlib.md5(cat_name.encode("utf-8")).hexdigest()[:8]
                cat = models.Category(name=cat_name, slug=cat_slug)
                db.add(cat)
                db.flush()
            category_id = cat.id

        product = models.Product(
            sku=sku,
            title=payload.title,
            category_id=category_id,
            brand=payload.brand or (payload.parameters.get("Производитель") or payload.parameters.get("Бренд")),
            model=payload.model or payload.parameters.get("Модель"),
            condition=payload.condition or payload.parameters.get("Состояние", "Б/у"),
            description=payload.description or "",
            sale_price=payload.price or 0.0,
            status="draft",
            storage_location="store",
            quantity=1,
            avito_title=payload.title,
            avito_description=payload.description,
            avito_category_path=" / ".join(payload.category_path) if payload.category_path else None,
            avito_condition=payload.condition,
            avito_params_json=json.dumps(payload.parameters, ensure_ascii=False) if payload.parameters else None,
            source_attributes_json=json.dumps(payload.parameters, ensure_ascii=False) if payload.parameters else None,
            source_origin="avito",
            source_type="avito_bootstrap",
            last_imported_at=now
        )
        db.add(product)
        db.flush()
    else:
        # Update existing product fields
        product.title = payload.title
        if payload.price is not None:
            product.sale_price = payload.price
        if payload.description:
            product.description = payload.description
        if payload.brand:
            product.brand = payload.brand
        if payload.model:
            product.model = payload.model
        if payload.condition:
            product.condition = payload.condition
        product.avito_title = payload.title
        product.avito_description = payload.description
        if payload.parameters:
            product.avito_params_json = json.dumps(payload.parameters, ensure_ascii=False)
            product.source_attributes_json = json.dumps(payload.parameters, ensure_ascii=False)
        product.source_origin = "avito"
        product.last_imported_at = now
        db.flush()

    # 2. Upsert ProductExternalListing
    if not ext_link:
        created_link = True
        ext_link = models.ProductExternalListing(
            product_id=product.id,
            marketplace="avito",
            external_account_key=payload.account_key,
            external_item_id=payload.external_item_id,
            external_url=payload.external_url,
            remote_status=payload.remote_status,
            remote_status_raw=payload.remote_status_raw,
            source_title=payload.title,
            source_price=payload.price,
            source_attributes_json=json.dumps(payload.parameters, ensure_ascii=False) if payload.parameters else None,
            last_seen_at=now,
            last_imported_at=now,
            sync_state="synced"
        )
        db.add(ext_link)
        db.flush()
    else:
        ext_link.external_account_key = payload.account_key
        ext_link.external_url = payload.external_url
        ext_link.remote_status = payload.remote_status
        ext_link.remote_status_raw = payload.remote_status_raw
        ext_link.source_title = payload.title
        ext_link.source_price = payload.price
        ext_link.source_attributes_json = json.dumps(payload.parameters, ensure_ascii=False) if payload.parameters else None
        ext_link.last_seen_at = now
        ext_link.last_imported_at = now
        ext_link.sync_state = "synced"
        db.flush()

    # 3. Import photos idempotently using content SHA256 / source_url
    photos_imported = 0
    photos_skipped = 0
    storage_photos_dir = os.path.join(settings.storage_root, "product_photos")
    os.makedirs(storage_photos_dir, exist_ok=True)

    for idx, item_photo in enumerate(payload.photos):
        photo_bytes = None
        content_hash = None
        source_url = item_photo.url

        if item_photo.content_base64:
            try:
                photo_bytes = base64.b64decode(item_photo.content_base64)
                content_hash = hashlib.sha256(photo_bytes).hexdigest()
            except Exception:
                pass

        if not content_hash and source_url:
            content_hash = hashlib.sha256(source_url.encode("utf-8")).hexdigest()

        # Check existing photo by content_hash or source_url for this product
        existing_photo = None
        if content_hash:
            existing_photo = db.query(models.ProductPhoto).filter(
                models.ProductPhoto.product_id == product.id,
                models.ProductPhoto.content_hash == content_hash
            ).first()
        if not existing_photo and source_url:
            existing_photo = db.query(models.ProductPhoto).filter(
                models.ProductPhoto.product_id == product.id,
                models.ProductPhoto.source_url == source_url
            ).first()

        if existing_photo:
            photos_skipped += 1
            continue

        # Save photo file if bytes available
        filename = f"{product.id}_{uuid.uuid4().hex[:8]}.jpg"
        storage_path = os.path.join(storage_photos_dir, filename)
        media_url = f"/media/product_photos/{filename}"

        if photo_bytes:
            with open(storage_path, "wb") as f:
                f.write(photo_bytes)
        else:
            with open(storage_path, "wb") as f:
                f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \x1c\x1c(7),01444\x1f'9=82<.342\xFF\xC0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xFF\xDA\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xFF\xd9")

        new_photo = models.ProductPhoto(
            product_id=product.id,
            filename=filename,
            storage_path=storage_path,
            media_url=media_url,
            source_url=source_url,
            content_hash=content_hash,
            sort_order=idx
        )
        db.add(new_photo)
        photos_imported += 1

    # 4. Audit events
    event_type = "avito.product_imported" if created_product else "avito.product_updated"
    log_audit(
        db,
        "product",
        product.id,
        event_type,
        new_value={
            "product_id": product.id,
            "external_item_id": payload.external_item_id,
            "account_key": payload.account_key,
            "title": payload.title,
            "price": payload.price,
            "remote_status": payload.remote_status
        }
    )

    link_event = "avito.external_link_created" if created_link else "avito.external_link_updated"
    log_audit(
        db,
        "product_external_listing",
        ext_link.id,
        link_event,
        new_value={
            "external_listing_id": ext_link.id,
            "product_id": product.id,
            "external_item_id": payload.external_item_id,
            "account_key": payload.account_key
        }
    )

    db.commit()
    db.refresh(product)
    db.refresh(ext_link)

    return schemas.AvitoItemImportResponse(
        status=status_str,
        product_id=product.id,
        external_listing_id=ext_link.id,
        photos_imported=photos_imported,
        photos_skipped=photos_skipped
    )
