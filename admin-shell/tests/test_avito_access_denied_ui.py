from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or []
    def json(self):
        return self._json_data

async def mock_async_get(*args, **kwargs):
    return MockResponse(200, [{"account_key": "acc_test", "display_name": "Acc Test"}])

@patch("httpx.AsyncClient.get", side_effect=mock_async_get)
def test_avito_browser_template_handles_access_denied_status(mock_get):
    """Verify avito_browser.html template has access_denied branch in verifyAuth script."""
    res = client.get("/avito/accounts/acc_test/browser")
    assert res.status_code == 200
    assert "access_denied" in res.text
    assert "Доступ закрыт!" in res.text
