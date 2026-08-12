import os
import time
import uuid
import secrets
import hashlib
import json
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
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
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
    extension_version: str = "0.1.0"
    captured_at: str
    page_type: str = "my_listings"
    listings_count: int = 0
    items: List[Dict[str, Any]] = []

@router.get("/status")
async def get_extension_status(x_extension_token: Optional[str] = Header(None)):
    paired = False
    if x_extension_token:
        tokens = _load_json(TOKENS_FILE)
        if _hash_token(x_extension_token) in tokens:
            paired = True
            # Update last active
            t_hash = _hash_token(x_extension_token)
            tokens[t_hash]["last_active_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            _save_json(TOKENS_FILE, tokens)

    tokens = _load_json(TOKENS_FILE)
    any_paired = len(tokens) > 0

    return {
        "online": True,
        "version": "0.1.0",
        "paired": paired or any_paired,
        "active_tokens_count": len(tokens)
    }

@router.post("/pairing/generate")
async def generate_pair_code():
    code = f"{secrets.randbelow(1000000):06d}"
    expires_at = time.time() + 600  # 10 mins TTL
    codes = _load_json(PAIR_CODES_FILE)
    codes[code] = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": expires_at,
        "used": False
    }
    _save_json(PAIR_CODES_FILE, codes)
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

@router.post("/my-listings")
async def receive_my_listings(payload: MyListingsPayload, token: str = Depends(verify_extension_token)):
    _save_json(MY_LISTINGS_FILE, payload.model_dump())
    return {"status": "received", "count": len(payload.items)}

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

    photos_urls = listing.get("photos") or []
    photos = [schemas.Photo(url=url) for url in photos_urls if isinstance(url, str)]

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
    # Bind to default or primary account profile
    profiles = storage.list_profiles()
    account_key = profiles[0].account_key if profiles else "acc_extension_owner"
    if not profiles:
        p = schemas.AvitoAccountProfile(account_key=account_key, display_name="Владелец (Расширение)")
        storage.save_profile(p)

    res = await import_service.import_ad_to_core(ext_id, account_key)
    
    # Save last ingest info
    last_ingest_file = os.path.join(settings.AVITO_STORAGE_DIR, "extension_last_ingest.json")
    _save_json(last_ingest_file, {
        "external_item_id": ext_id,
        "title": title,
        "price": price_val,
        "result": res.get("status"),
        "product_id": res.get("product_id"),
        "photos_count": len(photos),
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })

    return {
        "status": "imported",
        "external_item_id": ext_id,
        "product_id": res.get("product_id"),
        "result": res.get("status", "created"),
        "details": res
    }
