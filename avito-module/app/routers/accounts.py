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
        "novnc_url": "http://localhost:8061"
    })

@router.get("/accounts/api/profiles", response_model=List[schemas.AvitoAccountProfile])
async def get_profiles():
    return storage.list_profiles()

@router.post("/accounts/api/profiles", response_model=schemas.AvitoAccountProfile)
async def create_profile(payload: schemas.ProfileCreateRequest):
    p = storage.get_profile(payload.account_key)
    if p:
        p.display_name = payload.display_name
        p.api_client_id = payload.api_client_id
        p.api_client_secret = payload.api_client_secret
    else:
        p = schemas.AvitoAccountProfile(
            account_key=payload.account_key,
            display_name=payload.display_name,
            api_client_id=payload.api_client_id,
            api_client_secret=payload.api_client_secret
        )
    storage.save_profile(p)
    return p

@router.post("/accounts/api/profiles/{account_key}/check-auth")
async def check_profile_auth(account_key: str):
    profile = storage.get_profile(account_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    worker = AvitoBrowserWorker(account_key)
    auth_st, err_msg = await worker.check_auth_state()
    profile.auth_status = auth_st
    storage.save_profile(profile)
    return {"account_key": account_key, "auth_status": auth_st, "error": err_msg}

@router.post("/accounts/api/profiles/{account_key}/import")
async def start_import(
    account_key: str,
    background_tasks: BackgroundTasks,
    scope: str = Form("all"),
    item_id_filter: Optional[str] = Form(None)
):
    profile = storage.get_profile(account_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

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

    # Run import for first failed ID as retry
    new_run = await import_service.run_account_import(
        account_key=old_run.account_key,
        scope=old_run.scope,
        item_id_filter=failed_ids[0]
    )
    return new_run
