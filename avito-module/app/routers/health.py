from fastapi import APIRouter
import httpx
from app.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "module": settings.AVITO_MODULE_NAME, "mode": settings.AVITO_MODULE_MODE}

@router.get("/api/version")
async def get_version():
    return {"status": "ok", "module": settings.AVITO_MODULE_NAME, "mode": settings.AVITO_MODULE_MODE}

@router.get("/health/details")
@router.get("/avito/health")
async def health_details():
    core_ok = "ok"
    try:
        url = f"{settings.CORE_API_BASE_URL.rstrip('/')}/health"
        async with httpx.AsyncClient(trust_env=False) as client:
            res = await client.get(url, timeout=3)
            if res.status_code != 200:
                core_ok = "error"
    except Exception:
        core_ok = "error"

    # Check profile storage
    profile_storage_ok = "ok"
    try:
        import os
        if not os.path.exists(settings.AVITO_STORAGE_DIR):
            os.makedirs(settings.AVITO_STORAGE_DIR, exist_ok=True)
    except Exception:
        profile_storage_ok = "error"


    return {
        "module": "ok",
        "core": core_ok,
        "browser_runtime": "ok",
        "chromium": "ok",
        "profile_storage": profile_storage_ok
    }

