from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}
    def json(self):
        return self._json_data

async def mock_async_get(*args, **kwargs):
    return MockResponse(200, {"online": True, "version": "0.1.0", "paired": True, "active_tokens_count": 1})

@patch("httpx.AsyncClient.get", side_effect=mock_async_get)
def test_avito_extension_status_ui_proxy(mock_get):
    """Verify extension status badge displays online/paired state."""
    res = client.get("/avito/extension")
    assert res.status_code == 200
    assert "Работает" in res.text
