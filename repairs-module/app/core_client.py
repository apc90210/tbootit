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

    async def get_repair_options(self):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/repairs/options", timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def create_repair(self, payload: dict):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/api/repairs/", json=payload, timeout=10.0)
                if response.status_code in [200, 201]:
                    return response.json()
                detail = ""
                try:
                    detail = response.json().get("detail", "")
                except Exception:
                    detail = response.text
                return {"error": True, "status_code": response.status_code, "detail": detail}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_repairs(self, params: dict = None):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/repairs/", params=params or {}, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_repair(self, repair_id: int):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/repairs/{repair_id}", timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return {"error": True, "status_code": 404, "detail": "Ремонтный заказ не найден"}
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_repair_by_number(self, number: str):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/repairs/by-number/{number}", timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def update_repair(self, repair_id: int, payload: dict):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(f"{self.base_url}/api/repairs/{repair_id}", json=payload, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                detail = ""
                try:
                    detail = response.json().get("detail", "")
                except Exception:
                    detail = response.text
                return {"error": True, "status_code": response.status_code, "detail": detail}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def update_repair_status(
        self,
        repair_id: int,
        status: str,
        comment: Optional[str] = None,
        changed_by: Optional[str] = None,
        estimated_repair_amount: Optional[int] = None
    ):
        async with httpx.AsyncClient() as client:
            try:
                payload = {"status": status, "comment": comment, "changed_by": changed_by}
                if estimated_repair_amount is not None:
                    payload["estimated_repair_amount"] = estimated_repair_amount
                response = await client.post(f"{self.base_url}/api/repairs/{repair_id}/status", json=payload, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                detail = ""
                try:
                    detail = response.json().get("detail", "")
                except Exception:
                    detail = response.text
                return {"error": True, "status_code": response.status_code, "detail": detail}
            except Exception as e:
                return {"error": True, "details": str(e)}

    async def get_organization_settings(self):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/settings/organization", timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": True, "status_code": response.status_code}
            except Exception as e:
                return {"error": True, "details": str(e)}

core_client = CoreClient()
