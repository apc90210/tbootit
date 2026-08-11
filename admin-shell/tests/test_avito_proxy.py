import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("httpx.AsyncClient.get")
def test_avito_health_proxy(mock_get):
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.json = lambda: {
        "module": "ok",
        "core": "ok",
        "browser_runtime": "ok",
        "chromium": "ok",
        "profile_storage": "ok"
    }
    mock_get.return_value = mock_resp


    response = client.get("/avito/health")
    assert response.status_code == 200
    data = response.json()
    assert data["module"] == "ok"
    assert data["chromium"] == "ok"

@patch("httpx.AsyncClient.get")
def test_proxy_get_profiles(mock_get):
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.content = b'[{"account_key":"acc1","display_name":"Test Account"}]'
    mock_get.return_value = mock_resp

    response = client.get("/admin-api/avito/profiles")
    assert response.status_code == 200
    assert response.json()[0]["account_key"] == "acc1"
