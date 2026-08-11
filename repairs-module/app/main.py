import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.routers import repairs
from app.core_client import core_client

app = FastAPI(title="Technoreboot Repairs Module", version="0.1.0", root_path=os.getenv("ROOT_PATH", ""))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/health")
async def health_check():
    core_status = await core_client.health()
    return {
        "status": "ok",
        "module": "repairs-module",
        "core_available": core_status.get("core_available", False)
    }

app.include_router(repairs.router)
