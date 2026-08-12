import uuid
from typing import Optional, List
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app import storage, schemas
from app.browser_worker import AvitoBrowserWorker
from app.services import import_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/accounts", response_class=HTMLResponse)
async def view_accounts_page(request: Request):
    profiles = storage.list_profiles()
    runs = storage.list_import_runs()[:10]
    return templates.TemplateResponse("accounts_list.html", {
        "request": request,
        "profiles": profiles,
        "runs": runs,
        "novnc_url": "http://127.0.0.1:8061"
    })

@router.get("/accounts/api/profiles", response_model=List[schemas.AvitoAccountProfile])
async def get_profiles():
    return storage.list_profiles()

@router.get("/accounts/api/profiles/{account_key}", response_model=schemas.AvitoAccountProfile)
async def get_profile_by_key(account_key: str):
    profile = storage.get_profile(account_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post("/accounts/api/profiles", response_model=schemas.AvitoAccountProfile)
async def create_profile(payload: schemas.ProfileCreateRequest):
    existing_profiles = storage.list_profiles()
    account_key = payload.account_key or f"acc_{uuid.uuid4().hex[:8]}"

    existing = storage.get_profile(account_key)
    if not existing and len(existing_profiles) >= 3:
        raise HTTPException(
            status_code=400,
            detail="Превышен лимит профилей (максимум 3 аккаунта). Удалите неиспользуемый профиль перед созданием нового."
        )

    if existing:
        existing.display_name = payload.display_name
        existing.api_client_id = payload.api_client_id
        existing.api_client_secret = payload.api_client_secret
        storage.save_profile(existing)
        return existing
    else:
        new_p = schemas.AvitoAccountProfile(
            account_key=account_key,
            display_name=payload.display_name,
            api_client_id=payload.api_client_id,
            api_client_secret=payload.api_client_secret
        )
        storage.save_profile(new_p)
        return new_p

@router.delete("/accounts/api/profiles/{account_key}")
async def delete_profile(account_key: str):
    profile = storage.get_profile(account_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Check if active import run
    runs = storage.list_import_runs()
    active_runs = [r for r in runs if r.account_key == account_key and r.status == "running"]
    if active_runs:
        raise HTTPException(status_code=400, detail="Нельзя удалить профиль с активным процессом импорта.")

    storage.delete_profile(account_key)
    return {"status": "deleted", "account_key": account_key}

from app.browser_worker import AvitoBrowserWorker, browser_session_manager

@router.post("/accounts/api/profiles/{account_key}/launch-browser")
async def launch_profile_browser(account_key: str):
    profile = storage.get_profile(account_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    success, msg = await browser_session_manager.launch_session(account_key, profile.display_name)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "launched", "account_key": account_key, "message": msg}

@router.post("/accounts/api/profiles/{account_key}/stop-browser")
async def stop_profile_browser(account_key: str):
    await browser_session_manager.stop_session()
    return {"status": "stopped", "account_key": account_key}

@router.get("/accounts/api/profiles/{account_key}/browser-status")
async def get_browser_status(account_key: str):
    return browser_session_manager.get_status(account_key)

@router.post("/accounts/api/profiles/{account_key}/verify-probe")
async def verify_probe(account_key: str):
    profile = storage.get_profile(account_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.probe_verified = True
    storage.save_profile(profile)
    return {"status": "verified", "account_key": account_key, "probe_verified": True}

@router.post("/accounts/api/profiles/{account_key}/check-auth")
async def check_profile_auth(account_key: str):
    profile = storage.get_profile(account_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    worker = AvitoBrowserWorker(account_key)
    auth_st, err_msg = await worker.check_auth_state()
    profile.auth_status = auth_st
    import datetime
    profile.last_checked_at = datetime.datetime.now().isoformat()
    storage.save_profile(profile)
    return {"account_key": account_key, "auth_status": auth_st, "error": err_msg}

@router.get("/accounts/api/profiles/{account_key}/discover")
async def discover_listings(account_key: str, scope: str = "active"):
    profile = storage.get_profile(account_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.auth_status != "authorized":
        raise HTTPException(
            status_code=409,
            detail="AUTH_REQUIRED: Сначала выполните ручную авторизацию в Avito встроенном браузере."
        )

    worker = AvitoBrowserWorker(account_key)
    listings = await worker.discover_my_listings(scope=scope)
    return {"account_key": account_key, "listings_found": len(listings), "items": listings[:10]}

@router.get("/accounts/api/profiles/{account_key}/preview/{external_item_id}", response_model=schemas.ProbePreviewResponse)
async def preview_listing(account_key: str, external_item_id: str):
    profile = storage.get_profile(account_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.auth_status != "authorized":
        raise HTTPException(
            status_code=409,
            detail="AUTH_REQUIRED: Сначала выполните ручную авторизацию в Avito встроенном браузере."
        )

    worker = AvitoBrowserWorker(account_key)
    item_url = f"https://www.avito.ru/item/{external_item_id}"
    card = await worker.extract_item_card(item_url)

    title = card.get("title") or f"Объявление {external_item_id}"
    price = card.get("price")
    photos = card.get("photos") or []
    photo_urls = [p["url"] for p in photos if "url" in p]

    return schemas.ProbePreviewResponse(
        account_key=account_key,
        external_item_id=external_item_id,
        external_url=item_url,
        title=title,
        price=price,
        remote_status="active",
        photo_count=len(photo_urls),
        photo_urls=photo_urls,
        description=card.get("description"),
        parameters=card.get("parameters") or {}
    )

@router.post("/accounts/api/profiles/{account_key}/probe-import")
async def execute_one_item_probe(account_key: str, payload: schemas.OneItemProbeRequest):
    """
    Executes a 1-item trial probe import. Safe owner probe gate.
    """
    profile = storage.get_profile(account_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.auth_status != "authorized":
        raise HTTPException(
            status_code=409,
            detail="AUTH_REQUIRED: Сначала выполните ручную авторизацию в Avito встроенном браузере."
        )

    run = await import_service.run_account_import(
        account_key=account_key,
        scope="probe",
        item_id_filter=payload.external_item_id
    )
    return run

@router.post("/accounts/api/profiles/{account_key}/import")
async def start_full_import(
    account_key: str,
    scope: str = Form("all"),
    item_id_filter: Optional[str] = Form(None),
    allow_full: bool = Form(False)
):
    profile = storage.get_profile(account_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.auth_status != "authorized":
        raise HTTPException(
            status_code=409,
            detail="AUTH_REQUIRED: Сначала выполните ручную авторизацию в Avito встроенном браузере."
        )

    # Gate: do not allow full account import until probe import has been executed or allow_full is True or probe_verified is True
    if not allow_full and not item_id_filter:
        runs = storage.list_import_runs()
        successful_probes = [r for r in runs if r.account_key == account_key and r.created_count + r.updated_count > 0]
        if not profile.probe_verified and not successful_probes:
            raise HTTPException(
                status_code=403,
                detail="FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: Запуск полного импорта заблокирован до проведения успешного пробного импорта 1 объявления (One-Item Probe)."
            )

    run = await import_service.run_account_import(account_key, scope=scope, item_id_filter=item_id_filter)
    return run

@router.post("/accounts/api/runs/{run_id}/stop")
async def stop_run(run_id: str):
    import_service.stop_import_run(run_id)
    return {"status": "stopping", "run_id": run_id}

@router.post("/accounts/api/runs/{run_id}/retry")
async def retry_failed_items(run_id: str):
    old_run = storage.get_import_run(run_id)
    if not old_run:
        raise HTTPException(status_code=404, detail="Run not found")

    failed_ids = [item.external_item_id for item in old_run.items if item.status == "failed"]
    if not failed_ids:
        return {"status": "no_failed_items", "run_id": run_id}

    new_run = await import_service.run_account_import(
        account_key=old_run.account_key,
        scope=old_run.scope,
        item_id_filter=failed_ids[0]
    )
    return new_run

