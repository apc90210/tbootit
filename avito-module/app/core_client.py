import httpx
from typing import Dict, Any
from app.config import settings
from app.schemas import ProductCardImport

async def validate_product_card(card: ProductCardImport) -> Dict[str, Any]:
    url = f"{settings.CORE_API_BASE_URL.rstrip('/')}/api/product-cards/validate-json"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=card.model_dump())
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                return e.response.json()
            return {"valid": False, "errors": [f"HTTP error {e.response.status_code}"], "warnings": []}
        except Exception as e:
            return {"valid": False, "errors": [f"Connection error: {str(e)}"], "warnings": []}

async def import_product_card(card: ProductCardImport) -> Dict[str, Any]:
    url = f"{settings.CORE_API_BASE_URL.rstrip('/')}/api/product-cards/import-json"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=card.model_dump())
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (400, 422):
                return {"status": "failed", "error": f"Validation error: {e.response.text}"}
            return {"status": "failed", "error": f"HTTP error {e.response.status_code}"}
        except Exception as e:
            return {"status": "failed", "error": f"Connection error: {str(e)}"}
