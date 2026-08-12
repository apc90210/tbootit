from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = {"content-type": "application/json"}
        self.content = json.dumps(self._json_data).encode("utf-8") if isinstance(self._json_data, dict) else b"{}"
    def json(self):
        return self._json_data

import json

async def mock_async_request(*args, **kwargs):
    return MockResponse(200, {"pair_code": "483921", "expires_in_seconds": 600})

@patch("httpx.AsyncClient.request", side_effect=mock_async_request)
def test_avito_extension_pairing_api_proxy(mock_req):
    """Verify admin shell proxies pairing code generation request."""
    res = client.post("/admin-api/avito-extension/pairing/generate")
    assert res.status_code == 200
    assert res.json()["pair_code"] == "483921"
