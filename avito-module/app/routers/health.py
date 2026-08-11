import os
import socket
import subprocess
import httpx
from fastapi import APIRouter
from app.config import settings

router = APIRouter()

def is_socket_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False

def is_xvfb_running() -> bool:
    if os.path.exists("/tmp/.X11-unix/X99"):
        return True
    try:
        res = subprocess.run(["pgrep", "Xvfb"], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

def is_chromium_available() -> bool:
    try:
        from playwright.async_api import async_playwright
        return True
    except Exception:
        return False

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

    profile_storage_ok = "ok"
    try:
        if not os.path.exists(settings.AVITO_STORAGE_DIR):
            os.makedirs(settings.AVITO_STORAGE_DIR, exist_ok=True)
    except Exception:
        profile_storage_ok = "error"

    xvfb_ok = "ok" if is_xvfb_running() else "error"
    vnc_ok = "ok" if is_socket_open("127.0.0.1", 5900) else "error"
    novnc_ok = "ok" if is_socket_open("127.0.0.1", 6080) else "error"
    chromium_ok = "ok" if is_chromium_available() else "error"

    browser_runtime_ok = "ok" if (
        xvfb_ok == "ok" and 
        vnc_ok == "ok" and 
        novnc_ok == "ok" and 
        chromium_ok == "ok" and 
        profile_storage_ok == "ok"
    ) else "error"

    return {
        "module": "ok",
        "core": core_ok,
        "browser_runtime": browser_runtime_ok,
        "xvfb": xvfb_ok,
        "vnc": vnc_ok,
        "novnc": novnc_ok,
        "chromium": chromium_ok,
        "profile_storage": profile_storage_ok
    }
