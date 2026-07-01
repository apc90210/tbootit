import httpx
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
                response = await client.get(f"{self.base_url}/api/products", params=params, timeout=10.0)
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

core_client = CoreClient()
