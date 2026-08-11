import httpx
from typing import Optional, Dict, Any, List

class AvitoOfficialApiClient:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.avito.ru"
        self.access_token = None

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def authenticate(self) -> bool:
        if not self.is_configured():
            return False
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(
                    f"{self.base_url}/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if res.status_code == 200:
                    data = res.json()
                    self.access_token = data.get("access_token")
                    return True
                return False
            except Exception:
                return False

    async def get_my_items(self, status_filter: str = "active") -> List[Dict[str, Any]]:
        if not self.access_token:
            if not await self.authenticate():
                return []
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(
                    f"{self.base_url}/core/v1/items",
                    headers=headers,
                    params={"status": status_filter}
                )
                if res.status_code == 200:
                    return res.json().get("resources", [])
                return []
            except Exception:
                return []

    async def get_item_details(self, item_id: str) -> Optional[Dict[str, Any]]:
        if not self.access_token:
            if not await self.authenticate():
                return None
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(
                    f"{self.base_url}/core/v1/items/{item_id}",
                    headers=headers
                )
                if res.status_code == 200:
                    return res.json()
                return None
            except Exception:
                return None
