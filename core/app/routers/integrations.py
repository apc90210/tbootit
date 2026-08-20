import os
import uuid
import base64
import hashlib
import json
import urllib.parse
import ipaddress
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.config import settings

router = APIRouter()

def is_safe_remote_url(url: str) -> bool:
    if not url:
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        hostname_lower = hostname.lower()
        if hostname_lower in ("localhost", "127.0.0.1", "::1"):
            return False
        try:
            ip = ipaddress.ip_address(hostname_lower)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        except ValueError:
            pass
        return True
    except Exception:
        return False

def fetch_remote_image_bytes(url: str) -> Optional[bytes]:
    if not is_safe_remote_url(url):
        return None
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        with httpx.Client(trust_env=False, timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                return None
            content_type = resp.headers.get("content-type", "").lower()
            if not content_type.startswith("image/"):
                return None
            content = resp.content
            if len(content) > 10 * 1024 * 1024:  # 10 MB max
                return None
            return content
    except Exception:
        return None

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
    4. Idempotently imports photos using SHA256 content hash and remote fetch.
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

    # 2b. Stage06A-R9 Avito-First Category & Attribute Dynamic Schema Upsert
    try:
        from app.services.avito_schema_service import upsert_avito_category_schema, upsert_product_avito_attributes
        category_name = cat_name or (payload.category_path[-1] if payload.category_path else "Без категории")
        category_path_str = " / ".join(payload.category_path) if payload.category_path else category_name

        avito_cat = upsert_avito_category_schema(
            db=db,
            category_name=category_name,
            category_path=category_path_str,
            characteristics=payload.parameters
        )
        if avito_cat:
            upsert_product_avito_attributes(
                db=db,
                product_id=product.id,
                category_id=avito_cat.id,
                characteristics=payload.parameters
            )
    except Exception as e:
        print(f"Error upserting Avito category/attribute schema: {e}")

    # 3. Import photos idempotently using content SHA256 / source_url / remote fetch
    import re as _re
    photos_imported = 0
    photos_skipped = 0
    photos_reconciled = 0
    storage_photos_dir = os.path.join(settings.storage_root, "product_photos")
    os.makedirs(storage_photos_dir, exist_ok=True)

    def _extract_avito_resolution_version(url):
        """Extract resolution version from Avito CDN URL.
        New format: 'sePk6ba4HQr' -> 4 (ba4), 'rpQ-qra1FH0' -> 1 (ra1)
        Old format: 'm9BBHLa6' -> 6 (La6)
        """
        if not url:
            return 0
        path_only = url.split("?")[0]
        clean_path = _re.sub(r"^https?://[^/]+/", "", path_only, flags=_re.IGNORECASE)
        clean_path = _re.sub(r"^(?:image/\d+/|\d+x\d+/)+", "", clean_path, flags=_re.IGNORECASE)
        filename = clean_path.split("/")[-1]
        token = _re.sub(r"^\d+\.", "", filename)
        m = _re.search(r"[a-zA-Z]a(\d)", token)
        if m:
            return int(m.group(1))
        return 0

    def _get_avito_canonical_identity(url):
        """Extract canonical Avito photo identity from source_url."""
        if not url:
            return None
        path_only = url.split("?")[0]
        clean_path = _re.sub(r"^https?://[^/]+/", "", path_only, flags=_re.IGNORECASE)
        clean_path = _re.sub(r"^(?:image/\d+/|\d+x\d+/)+", "", clean_path, flags=_re.IGNORECASE)
        filename = clean_path.split("/")[-1]
        token = _re.sub(r"^\d+\.", "", filename)

        # Match [prefix][letter]a[digit] — both new (ba4, ra3) and old (La6) formats
        la_match = _re.search(r"^([A-Za-z0-9_-]{2,}?[A-Za-z0-9_-])[a-zA-Z]a\d", token, _re.IGNORECASE)
        if la_match:
            return "avito_photo_" + la_match.group(1)

        token_no_ext = _re.sub(r"\.(?:jpg|jpeg|webp|png)$", "", token, flags=_re.IGNORECASE)
        if len(token_no_ext) > 10 and _re.match(r"^[A-Za-z0-9_-]{5}", token_no_ext):
            return "avito_photo_" + token_no_ext[:5]

        clean_name = _re.sub(r"[^A-Za-z0-9_-]", "", token_no_ext)
        if len(clean_name) >= 3:
            return "avito_photo_" + clean_name

        if "img.avito.st" in url.lower():
            return path_only
        return None

    def _get_avito_quality_score(url):
        """Score Avito image variant quality by explicit path dimensions, resolution version, or master CDN."""
        if not url:
            return 0

        explicit_bonus = 0
        dim_match = _re.search(r"/(?:(\d+)x(\d+))/", url)
        w = 0
        h = 0
        if dim_match:
            try:
                w = int(dim_match.group(1))
                h = int(dim_match.group(2))
                explicit_bonus = 5
            except Exception:
                pass

        base_area = w * h if (w > 0 and h > 0) else 0

        v = _extract_avito_resolution_version(url)
        la_bonus = v * 10
        if v > 0 and base_area == 0:
            if v >= 4:
                base_area = 1280 * 960  # 1,228,800
            elif v == 3:
                base_area = 640 * 480   # 307,200
            elif v == 2:
                base_area = 208 * 156   # 32,448
            elif v == 1:
                base_area = 140 * 105   # 14,700

        if base_area == 0 and "img.avito.st/image/1/" in url.lower():
            base_area = 1280 * 960

        if base_area > 0:
            return base_area + la_bonus + explicit_bonus

        return 1

    def _is_avito_managed(source_url):
        """Check if a photo is Avito-managed by source_url host."""
        if not source_url:
            return False
        return "img.avito.st" in source_url.lower()

    def _delete_photo_file_and_row(photo_row):
        """Safely delete stored file if exists and delete DB row."""
        if photo_row.storage_path and os.path.exists(photo_row.storage_path):
            try:
                os.remove(photo_row.storage_path)
            except Exception:
                pass
        db.delete(photo_row)

    # Process ALL incoming photos from payload without dropping any photo variants
    effective_photos = payload.photos or []

    # Track incoming content hashes and source URLs for reconciliation
    incoming_content_hashes = set()
    incoming_source_urls = set()

    for idx, item_photo in enumerate(effective_photos):
        photo_bytes = None
        content_hash = None
        source_url = item_photo.url
        sort_order = item_photo.position if hasattr(item_photo, "position") and item_photo.position is not None else idx

        if item_photo.content_base64:
            try:
                photo_bytes = base64.b64decode(item_photo.content_base64)
                content_hash = hashlib.sha256(photo_bytes).hexdigest()
            except Exception:
                pass

        if not photo_bytes and source_url:
            fetched = fetch_remote_image_bytes(source_url)
            if fetched:
                photo_bytes = fetched
                content_hash = hashlib.sha256(photo_bytes).hexdigest()

        if not content_hash and source_url:
            content_hash = hashlib.sha256(source_url.encode("utf-8")).hexdigest()

        if content_hash:
            incoming_content_hashes.add(content_hash)
        if source_url:
            incoming_source_urls.add(source_url)

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
            is_dummy = False
            if existing_photo.storage_path and os.path.exists(existing_photo.storage_path):
                try:
                    if os.path.getsize(existing_photo.storage_path) <= 200:
                        is_dummy = True
                except Exception:
                    pass
            if is_dummy and photo_bytes and len(photo_bytes) > 200:
                try:
                    with open(existing_photo.storage_path, "wb") as f:
                        f.write(photo_bytes)
                    existing_photo.content_hash = content_hash
                    existing_photo.sort_order = sort_order
                    photos_imported += 1
                except Exception:
                    photos_skipped += 1
            else:
                # Update sort_order for existing photo
                existing_photo.sort_order = sort_order
                photos_skipped += 1
            continue

        if not photo_bytes:
            photos_skipped += 1
            continue

        # Save photo file
        filename = f"{product.id}_{uuid.uuid4().hex[:8]}.jpg"
        storage_path = os.path.join(storage_photos_dir, filename)
        media_url = f"/media/product_photos/{filename}"

        with open(storage_path, "wb") as f:
            f.write(photo_bytes)

        new_photo = models.ProductPhoto(
            product_id=product.id,
            filename=filename,
            storage_path=storage_path,
            media_url=media_url,
            source_url=source_url,
            content_hash=content_hash,
            sort_order=sort_order
        )
        db.add(new_photo)
        photos_imported += 1

    # 3b. Avito photo set reconciliation — remove obsolete photos no longer in payload
    if len(payload.photos) > 0:

        all_photos = db.query(models.ProductPhoto).filter(
            models.ProductPhoto.product_id == product.id
        ).all()

        for photo in all_photos:
            if not _is_avito_managed(photo.source_url):
                # Manual or non-Avito photo — DO NOT TOUCH!
                continue
            
            # If photo content hash and source URL are no longer in incoming payload, delete
            if photo.source_url not in incoming_source_urls and photo.content_hash not in incoming_content_hashes:
                _delete_photo_file_and_row(photo)
                photos_reconciled += 1

        # Re-number sort_order contiguously for remaining photos
        if photos_reconciled > 0 or photos_imported > 0:
            remaining = db.query(models.ProductPhoto).filter(
                models.ProductPhoto.product_id == product.id
            ).order_by(models.ProductPhoto.sort_order, models.ProductPhoto.id).all()

            for new_idx, photo in enumerate(remaining):
                photo.sort_order = new_idx

            db.flush()

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
        photos_skipped=photos_skipped,
        photos_reconciled=photos_reconciled
    )
