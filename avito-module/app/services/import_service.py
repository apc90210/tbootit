import uuid
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.config import settings
from app.schemas import AvitoAccountProfile, ImportRun, ImportItemResult
from app import storage
from app.official_api import AvitoOfficialApiClient
from app.browser_worker import AvitoBrowserWorker

ACTIVE_RUN_STOP_FLAGS: Dict[str, bool] = {}

async def run_account_import(
    account_key: str,
    scope: str = "all",
    item_id_filter: Optional[str] = None,
    mock_discovery: Optional[List[Dict[str, Any]]] = None,
    mock_cards: Optional[Dict[str, Dict[str, Any]]] = None
) -> ImportRun:
    run_id = str(uuid.uuid4())
    now_str = datetime.utcnow().isoformat()

    run = ImportRun(
        run_id=run_id,
        account_key=account_key,
        started_at=now_str,
        status="running",
        scope=scope,
        items=[]
    )
    storage.save_import_run(run)
    ACTIVE_RUN_STOP_FLAGS[run_id] = False

    profile = storage.get_profile(account_key)
    if not profile:
        profile = AvitoAccountProfile(account_key=account_key, display_name=f"Avito ({account_key})")
        storage.save_profile(profile)

    browser_worker = AvitoBrowserWorker(account_key)
    api_client = AvitoOfficialApiClient(profile.api_client_id, profile.api_client_secret)

    # Step 1: Check Auth
    if not mock_discovery and not mock_cards:
        if api_client.is_configured():
            auth_ok = await api_client.authenticate()
            profile.auth_status = "authorized" if auth_ok else "unauthorized"
        else:
            auth_st, err_msg = await browser_worker.check_auth_state()
            profile.auth_status = auth_st
            if auth_st in ("unauthorized", "challenge_required"):
                run.status = "failed"
                run.last_error = err_msg or "Ошибка авторизации"
                run.finished_at = datetime.utcnow().isoformat()
                storage.save_import_run(run)
                profile.last_checked_at = datetime.utcnow().isoformat()
                storage.save_profile(profile)
                return run

    profile.last_checked_at = datetime.utcnow().isoformat()
    storage.save_profile(profile)

    # Step 2: Discover listings
    listings = []
    if mock_discovery is not None:
        listings = mock_discovery
    elif api_client.is_configured():
        listings = await api_client.get_my_items(status_filter=scope if scope != "all" else "active")
    else:
        listings = await browser_worker.discover_my_listings(scope=scope)

    if item_id_filter:
        listings = [l for l in listings if str(l.get("external_item_id")) == str(item_id_filter)]

    run.listings_found = len(listings)
    storage.save_import_run(run)

    # Step 3: Process items sequentially
    core_url = f"{settings.CORE_API_BASE_URL.rstrip('/')}/api/integrations/avito/import-item"

    async with httpx.AsyncClient(timeout=15.0, trust_env=False) as http_client:
        for item_data in listings:
            if ACTIVE_RUN_STOP_FLAGS.get(run_id, False):
                run.status = "stopped"
                break

            item_id = str(item_data.get("external_item_id", ""))
            title = item_data.get("title", f"Объявление {item_id}")
            item_url = item_data.get("external_url", f"https://www.avito.ru/item/{item_id}")
            price = item_data.get("price")
            remote_st = item_data.get("remote_status", "active")
            remote_st_raw = item_data.get("remote_status_raw", remote_st)

            # Card extraction
            card_details = {}
            if mock_cards and item_id in mock_cards:
                card_details = mock_cards[item_id]
            elif api_client.is_configured():
                api_card = await api_client.get_item_details(item_id)
                if api_card:
                    card_details = {
                        "title": api_card.get("title", title),
                        "price": api_card.get("price", price),
                        "description": api_card.get("description", ""),
                        "parameters": api_card.get("parameters", {}),
                        "photos": [{"url": p} for p in api_card.get("photos", [])]
                    }
            else:
                card_details = await browser_worker.extract_item_card(item_url)

            final_title = card_details.get("title") or title
            final_price = card_details.get("price") if card_details.get("price") is not None else price
            final_desc = card_details.get("description") or ""
            final_params = card_details.get("parameters") or {}
            final_photos = card_details.get("photos") or item_data.get("photos") or []

            payload = {
                "account_key": account_key,
                "external_item_id": item_id,
                "external_url": item_url,
                "remote_status": remote_st,
                "remote_status_raw": remote_st_raw,
                "title": final_title,
                "price": final_price,
                "description": final_desc,
                "category_path": item_data.get("category_path", []),
                "brand": item_data.get("brand"),
                "model": item_data.get("model"),
                "condition": item_data.get("condition"),
                "parameters": final_params,
                "photos": final_photos,
                "raw_source_data": card_details
            }

            item_result = ImportItemResult(
                external_item_id=item_id,
                title=final_title,
                status="failed",
                photos_imported=0
            )

            try:
                res = await http_client.post(core_url, json=payload)
                if res.status_code == 200:
                    resp_data = res.json()
                    item_result.status = resp_data.get("status", "updated")
                    item_result.product_id = resp_data.get("product_id")
                    item_result.photos_imported = resp_data.get("photos_imported", 0)

                    if item_result.status == "created":
                        run.created_count += 1
                    elif item_result.status == "updated":
                        run.updated_count += 1
                    elif item_result.status == "unchanged":
                        run.skipped_count += 1
                else:
                    item_result.status = "failed"
                    item_result.error = f"HTTP {res.status_code}: {res.text}"
                    run.error_count += 1
            except Exception as e:
                item_result.status = "failed"
                item_result.error = f"Core API call error: {str(e)}"
                run.error_count += 1

            run.items.append(item_result)
            storage.save_import_run(run)

    if run.status != "stopped":
        run.status = "completed"

    run.finished_at = datetime.utcnow().isoformat()
    storage.save_import_run(run)

    # Update profile stats
    profile.last_imported_at = datetime.utcnow().isoformat()
    profile.stats.found = run.listings_found
    profile.stats.imported += run.created_count
    profile.stats.updated += run.updated_count
    profile.stats.skipped += run.skipped_count
    profile.stats.errors += run.error_count
    storage.save_profile(profile)

    return run

def stop_import_run(run_id: str):
    ACTIVE_RUN_STOP_FLAGS[run_id] = True
