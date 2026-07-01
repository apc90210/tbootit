from fastapi import APIRouter
from app.config import settings
from app.core_client import core_client

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "module": "inventory-sales-module"
    }

@router.get("/api/version")
async def version():
    return {
        "version": "1.0.0",
        "module": settings.inventory_sales_module_name
    }

@router.get("/api/core/health")
async def core_health():
    res = await core_client.health()
    return res
