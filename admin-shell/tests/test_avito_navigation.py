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
    return MockResponse(200, [{"account_key": "test_acc", "display_name": "Test Acc"}])

def test_avito_main_navigation():
    response = client.get("/avito")
    assert response.status_code == 200
    assert "Интеграция с Avito" in response.text
    assert "Обзор" in response.text

def test_avito_accounts_navigation():
    response = client.get("/avito/accounts")
    assert response.status_code == 200
    assert "Аккаунты Avito" in response.text

@patch("httpx.AsyncClient.get", side_effect=mock_async_get)
def test_avito_browser_navigation(mock_get):
    response = client.get("/avito/accounts/test_acc/browser")
    assert response.status_code == 200
    assert "Авторизация Avito" in response.text
    assert "novnc/vnc.html" in response.text

def test_avito_probe_navigation():
    response = client.get("/avito/probe")
    assert response.status_code == 200
    assert "Пробный импорт 1 объявления" in response.text
