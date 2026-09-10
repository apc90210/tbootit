import os
import time
import uuid
import secrets
import hashlib
import json
import httpx
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from app.config import settings
from app import storage, schemas
from app.services import import_service

router = APIRouter(prefix="/extension/api", tags=["chrome-extension"])

PAIR_CODES_FILE = os.path.join(settings.AVITO_STORAGE_DIR, "extension_pair_codes.json")
TOKENS_FILE = os.path.join(settings.AVITO_STORAGE_DIR, "extension_tokens.json")
MY_LISTINGS_FILE = os.path.join(settings.AVITO_STORAGE_DIR, "extension_my_listings.json")

def _load_json(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_json(file_path: str, data: Dict[str, Any]):
    parent = os.path.dirname(file_path)
    if parent:
        try:
            os.makedirs(parent, exist_ok=True)
        except Exception:
            pass
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def verify_extension_token(x_extension_token: Optional[str] = Header(None)) -> str:
    if not x_extension_token:
        raise HTTPException(status_code=401, detail="X-Extension-Token header is required")
    
    tokens = _load_json(TOKENS_FILE)
    token_hash = _hash_token(x_extension_token)
    if token_hash not in tokens:
        raise HTTPException(status_code=401, detail="Invalid or un-paired Extension Token")
    return x_extension_token

# Schemas
class PairRequest(BaseModel):
    pair_code: str

class ListingPayload(BaseModel):
    schema_version: int = 1
    extension_version: str = "0.1.0"
    captured_at: str
    page_type: str = "listing"
    listing: Dict[str, Any]

class MyListingsPayload(BaseModel):
    schema_version: int = 1
    extension_version: str = "0.2.49"
    captured_at: Optional[str] = None
    page_type: Optional[str] = "my_listings"
    listings_count: Optional[int] = 0
    items: List[Dict[str, Any]] = []

class BulkImportPayload(BaseModel):
    schema_version: int = 1
    extension_version: str = "0.2.49"
    captured_at: Optional[str] = None
    page_type: Optional[str] = "bulk_import"
    listings_count: Optional[int] = None
    items: List[Dict[str, Any]] = []

@router.get("/status")
async def get_extension_status(x_extension_token: Optional[str] = Header(None)):
    paired = False
    tokens = _load_json(TOKENS_FILE)
    
    if x_extension_token:
        t_hash = _hash_token(x_extension_token)
        if t_hash in tokens:
            paired = True
            tokens[t_hash]["last_active_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            _save_json(TOKENS_FILE, tokens)

    return {
        "online": True,
        "version": "0.2.49",
        "paired": paired,
        "token_valid": paired,
        "active_tokens_count": len(tokens)
    }

@router.get("/last-ingest")
async def get_last_ingest():
    last_ingest_file = os.path.join(settings.AVITO_STORAGE_DIR, "extension_last_ingest.json")
    if os.path.exists(last_ingest_file):
        return _load_json(last_ingest_file)
    return {}

@router.post("/pairing/generate")
async def generate_pair_code():
    code = f"{secrets.randbelow(1000000):06d}"
    now = time.time()
    expires_at = now + 600  # 10 mins TTL
    codes = _load_json(PAIR_CODES_FILE)
    # Prune expired codes older than 24 hours to keep registry compact
    pruned_codes = {
        k: v for k, v in codes.items()
        if isinstance(v, dict) and v.get("expires_at", 0) > (now - 86400)
    }
    pruned_codes[code] = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": expires_at,
        "used": False
    }
    _save_json(PAIR_CODES_FILE, pruned_codes)
    return {"pair_code": code, "expires_in_seconds": 600}

@router.post("/pairing/pair")
async def pair_extension(payload: PairRequest):
    code = payload.pair_code.strip()
    codes = _load_json(PAIR_CODES_FILE)
    
    if code not in codes:
        raise HTTPException(status_code=400, detail="Код подключения не найден.")
    
    entry = codes[code]
    if entry.get("used") or time.time() > entry.get("expires_at", 0):
        raise HTTPException(status_code=400, detail="Срок действия кода подключения истёк. Сгенерируйте новый код.")

    # Mark used
    entry["used"] = True
    _save_json(PAIR_CODES_FILE, codes)

    # Issue token
    raw_token = f"ext_tok_{uuid.uuid4().hex}"
    t_hash = _hash_token(raw_token)
    tokens = _load_json(TOKENS_FILE)
    tokens[t_hash] = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_active_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    _save_json(TOKENS_FILE, tokens)

    return {"status": "paired", "extension_token": raw_token}

@router.post("/heartbeat")
async def extension_heartbeat(token: str = Depends(verify_extension_token)):
    tokens = _load_json(TOKENS_FILE)
    t_hash = _hash_token(token)
    if t_hash in tokens:
        tokens[t_hash]["last_active_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        _save_json(TOKENS_FILE, tokens)
    return {"status": "ok", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.post("/bulk-import")
@router.post("/my-listings")
async def receive_bulk_import(payload: BulkImportPayload, token: str = Depends(verify_extension_token)):
    # 1. Save last bulk payload for diagnostics
    _save_json(MY_LISTINGS_FILE, payload.model_dump())

    # 2. Get profile for account key
    profiles = storage.list_profiles()
    account_key = profiles[0].account_key if profiles else "acc_extension_owner"
    if not profiles:
        p = schemas.AvitoAccountProfile(account_key=account_key, display_name="Владелец (Расширение)")
        storage.save_profile(p)

    core_url = f"{settings.CORE_API_BASE_URL.rstrip('/')}/api/integrations/avito/import-item"

    created_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0
    results = []

    async with httpx.AsyncClient(trust_env=False, timeout=60.0) as http_client:
        for item in payload.items:
            # Extract lightweight card data
            item_id = str(item.get("avito_id") or item.get("external_item_id") or item.get("id") or "").strip()
            item_url = str(item.get("url") or item.get("external_url") or "").strip()
            title = str(item.get("title") or "").strip()
            
            if not item_id:
                error_count += 1
                results.append({
                    "avito_id": None,
                    "title": title or "Неизвестный товар",
                    "status": "failed",
                    "error": "Отсутствует Avito ID"
                })
                continue

            if not item_url:
                item_url = f"https://www.avito.ru/item/{item_id}"

            if not title:
                title = f"Объявление Avito {item_id}"

            # Price extraction
            price_raw = item.get("price")
            price = None
            if price_raw is not None and str(price_raw).strip():
                try:
                    price_cleaned = str(price_raw).replace(" ", "").replace(",", ".").replace("₽", "").strip()
                    price = float(price_cleaned)
                except Exception:
                    price = None

            status = str(item.get("status") or item.get("remote_status") or "active").strip()
            cat_str = str(item.get("category") or "").strip()
            category_path = [cat_str] if cat_str else []

            params = {}
            loc = str(item.get("location") or item.get("address") or "").strip()
            if loc:
                params["Адрес"] = loc

            photo_url = str(item.get("photo_url") or item.get("thumbnail_url") or item.get("main_photo") or "").strip()
            photos = []
            if photo_url and photo_url.startswith("http"):
                photos.append({"url": photo_url, "position": 0})

            core_payload = {
                "account_key": account_key,
                "external_item_id": item_id,
                "external_url": item_url,
                "remote_status": status,
                "remote_status_raw": status,
                "title": title,
                "price": price,
                "description": None,
                "category_path": category_path,
                "brand": None,
                "model": None,
                "condition": None,
                "parameters": params,
                "photos": photos,
                "raw_source_data": {"lightweight": True, "bulk_import": True, "source_card": item}
            }

            try:
                res = await http_client.post(core_url, json=core_payload)
                if res.status_code == 200:
                    resp_data = res.json()
                    st = resp_data.get("status", "updated")
                    prod_id = resp_data.get("product_id")
                    if st == "created":
                        created_count += 1
                    elif st == "updated":
                        updated_count += 1
                    elif st == "unchanged":
                        skipped_count += 1
                    else:
                        updated_count += 1

                    results.append({
                        "avito_id": item_id,
                        "title": title,
                        "status": st,
                        "product_id": prod_id,
                        "price": price
                    })
                else:
                    error_count += 1
                    err_msg = f"Core HTTP {res.status_code}"
                    try:
                        err_json = res.json()
                        detail = err_json.get("detail") or err_json.get("message")
                        if detail:
                            err_msg = str(detail)
                    except Exception:
                        pass
                    results.append({
                        "avito_id": item_id,
                        "title": title,
                        "status": "failed",
                        "error": err_msg
                    })
            except Exception as e:
                error_count += 1
                results.append({
                    "avito_id": item_id,
                    "title": title,
                    "status": "failed",
                    "error": f"Ошибка запроса: {str(e)}"
                })

    total = len(payload.items)
    failed_items = [r for r in results if r.get("status") == "failed"]
    return {
        "status": "success",
        "total": total,
        "count": total,
        "created": created_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "error_count": error_count,
        "errors": failed_items,
        "results": results
    }

@router.post("/listing")
async def receive_listing(payload: ListingPayload, token: str = Depends(verify_extension_token)):
    listing = payload.listing
    
    # 1. Validation
    ext_id = str(listing.get("external_item_id") or "").strip()
    ext_url = str(listing.get("external_url") or "").strip()
    title = str(listing.get("title") or "").strip()
    
    if not ext_id:
        raise HTTPException(status_code=400, detail="Отсутствует обязательный external_item_id.")
    if not ext_url or "avito.ru" not in ext_url:
        raise HTTPException(status_code=400, detail="Невалидный URL объявления (должен быть avito.ru).")
    if not title:
        title = f"Объявление Avito {ext_id}"

    # Security scan: Ensure 0 cookies/credentials
    str_payload = json.dumps(listing, ensure_ascii=False).lower()
    if "cookie" in str_payload or "sessionid" in str_payload or "authorization" in str_payload:
        raise HTTPException(status_code=400, detail="Обнаружены запрещённые поля сессии/cookie.")

    # 2. Build ParsedAd data
    price = listing.get("price")
    try:
        price_val = float(price) if price is not None else None
    except Exception:
        price_val = None

    raw_photos = listing.get("photos") or []
    photos = []
    for item in raw_photos:
        if isinstance(item, str) and item.strip():
            photos.append(schemas.Photo(url=item.strip()))
        elif isinstance(item, dict) and item.get("url"):
            url_str = str(item.get("url")).strip()
            if url_str:
                photos.append(schemas.Photo(url=url_str, content_base64=item.get("content_base64")))

    photos_received = len(raw_photos)
    photos_forwarded = len(photos)

    parsed_ad = schemas.ParsedAd(
        id=ext_id,
        run_id="extension_ingest",
        source="avito",
        source_url=ext_url,
        external_id=ext_id,
        title=title,
        price=price_val,
        currency="RUB",
        description=listing.get("description"),
        seller_name="Owner",
        category_path=[listing.get("category")] if listing.get("category") else [],
        parameters=listing.get("characteristics") or {},
        photos=photos,
        parse_status="success",
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    storage.save_parsed_ad(parsed_ad)

    # 3. Import to Core API
    profiles = storage.list_profiles()
    account_key = profiles[0].account_key if profiles else "acc_extension_owner"
    if not profiles:
        p = schemas.AvitoAccountProfile(account_key=account_key, display_name="Владелец (Расширение)")
        storage.save_profile(p)

    res = await import_service.import_ad_to_core(ext_id, account_key)
    product_id = res.get("product_id")
    result_status = res.get("status", "failed")
    photos_imported = res.get("photos_imported", 0)
    photos_skipped = res.get("photos_skipped", 0)
    photos_total = photos_imported + photos_skipped

    if product_id is not None and result_status != "failed":
        if photos_received > 0 and photos_imported == 0 and photos_skipped == 0:
            result_status = "partial"

    # Save last ingest info
    last_ingest_file = os.path.join(settings.AVITO_STORAGE_DIR, "extension_last_ingest.json")
    _save_json(last_ingest_file, {
        "external_item_id": ext_id,
        "title": title,
        "price": price_val,
        "result": result_status,
        "product_id": product_id,
        "photos_received": photos_received,
        "photos_forwarded": photos_forwarded,
        "photos_imported": photos_imported,
        "photos_skipped": photos_skipped,
        "photos_total": photos_total,
        "photos_count": photos_total,
        "error": res.get("error"),
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })

    if product_id is None or result_status == "failed":
        raise HTTPException(
            status_code=422,
            detail={
                "status": "failed",
                "external_item_id": ext_id,
                "product_id": None,
                "message": f"Не удалось импортировать объявление в Техноребут: {res.get('error', 'Ошибка Core API')}",
                "error_code": "CORE_IMPORT_FAILED"
            }
        )

    msg = f"Объявление {ext_id} импортировано в Техноребут (Product ID: {product_id}, фото: {photos_total})."
    if result_status == "partial":
        msg = f"Товар {ext_id} импортирован с предупреждением: фото не сохранены (ID: {product_id})."

    return {
        "status": "success" if result_status in ("created", "updated") else result_status,
        "external_item_id": ext_id,
        "product_id": product_id,
        "result": result_status,
        "photos_imported": photos_imported,
        "photos_skipped": photos_skipped,
        "photos_total": photos_total,
        "photos_received": photos_received,
        "message": msg,
        "details": res
    }

@router.get("/publication-package/{product_id}")
async def get_extension_publication_package(
    product_id: int,
    token: str = Depends(verify_extension_token)
):
    """
    Fetch transport-neutral publication package and preflight validation for a product.
    Requires paired extension token.
    Queries Core internal API:
    - GET http://core:8000/api/integrations/avito/products/{product_id}/publication-package
    - GET http://core:8000/api/integrations/avito/products/{product_id}/preflight
    """
    import datetime
    import urllib.request
    import urllib.error

    core_base = settings.CORE_API_BASE_URL.rstrip('/')
    pkg_url = f"{core_base}/api/integrations/avito/products/{product_id}/publication-package"
    preflight_url = f"{core_base}/api/integrations/avito/products/{product_id}/preflight"

    try:
        req_pkg = urllib.request.Request(pkg_url)
        with urllib.request.urlopen(req_pkg, timeout=10) as resp_pkg:
            pkg_data = json.loads(resp_pkg.read().decode('utf-8'))

        req_pre = urllib.request.Request(preflight_url)
        with urllib.request.urlopen(req_pre, timeout=10) as resp_pre:
            pre_data = json.loads(resp_pre.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found in Technoreboot Core")
        raise HTTPException(status_code=502, detail=f"Error querying Core API: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Core API connection failed: {e}")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    expires_iso = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)).isoformat()

    return {
        "schema_version": 1,
        "product_id": product_id,
        "prepared_at": now_iso,
        "expires_at": expires_iso,
        "title": pkg_data.get("title") or "",
        "description": pkg_data.get("description") or "",
        "price": pkg_data.get("price") or 0.0,
        "category": {
            "display_name": pkg_data.get("category") or "Товары",
            "observed_path": [pkg_data.get("category")] if pkg_data.get("category") else [],
            "official_slug": pre_data.get("official_slug")
        },
        "condition": pkg_data.get("condition") or "Б/у",
        "brand": pkg_data.get("brand"),
        "model": pkg_data.get("model"),
        "characteristics": pkg_data.get("characteristics") or {},
        "photos": pkg_data.get("photos") or [],
        "preflight": {
            "ready_for_browser_assisted": pre_data.get("ready_for_browser_assisted", True),
            "errors": pre_data.get("errors", []),
            "warnings": pre_data.get("warnings", [])
        }
    }

