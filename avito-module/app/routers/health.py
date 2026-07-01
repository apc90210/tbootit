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

@router.get("/api/core/health")
async def core_health_check():
    try:
        url = f"{settings.CORE_API_BASE_URL.rstrip('/')}/health"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5)
            response.raise_for_status()
            return {"status": "ok", "core": "reachable", "core_response": response.json()}
    except Exception as e:
        return {"status": "error", "core": "unreachable", "detail": str(e)}
