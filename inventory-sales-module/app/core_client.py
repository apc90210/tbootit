import httpx
from typing import Optional
from app.config import settings

class CoreClient:
    def __init__(self):
        self.base_url = settings.core_api_base_url.rstrip("/")
        
    async def health(self):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                if response.status_code == 200:
                    return {"core_available": True, "core_response": response.json()}
                return {"core_available": False, "status_code": response.status_code}
            except Exception as e:
                return {"core_available": False, "error": str(e)}

    async def get_products(self, params: dict):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/products/", params=params, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_product_filter_options(self, params: dict = None):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/products/filter-options", params=params or {}, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_product(self, product_id: int):
        # Fallback to get_product_details if preferred, this just gets basic info
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/products/{product_id}", timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return {"error": "Not Found", "status_code": 404}
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_product_details(self, product_id: int):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/products/{product_id}/details", timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return {"error": "Not Found", "status_code": 404}
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    # --- Sales methods (Stage 04E) ---

    async def create_sale(self, payload: dict):
        """Create a sale through Core API POST /api/sales/."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/sales/",
                    json=payload,
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json()
                # Return structured error with detail from Core
                error_detail = ""
                try:
                    error_detail = response.json().get("detail", "")
                except Exception:
                    error_detail = response.text
                return {"error": True, "status_code": response.status_code, "detail": error_detail}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_sale(self, sale_id: int):
        """Get single sale by ID from Core API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/sales/{sale_id}", timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return {"error": "Not Found", "status_code": 404}
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_sales(self, params: dict = None):
        """Get list of sales from Core API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/sales/",
                    params=params or {},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json()
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_sales_today(self):
        """Get today's sales from Core API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/sales/today", timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_organization_settings(self):
        from app.defaults import get_effective_settings
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/settings/organization", timeout=10.0)
                if response.status_code == 200:
                    return get_effective_settings(response.json())
                return get_effective_settings({"error": True, "status_code": response.status_code})
            except Exception as e:
                return get_effective_settings({"error": True, "details": str(e)})

    async def update_organization_settings(self, payload: dict):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(f"{self.base_url}/api/settings/organization", json=payload, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_sales_report(self, period: str = "today", date_from: Optional[str] = None, date_to: Optional[str] = None) -> dict:
        params = {"period": period}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/reports/sales", params=params, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

core_client = CoreClient()
