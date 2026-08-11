import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("app.routers.health.httpx.AsyncClient.get", new_callable=AsyncMock)
def test_health_details_endpoint(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    res = client.get("/health/details")
    assert res.status_code == 200
    data = res.json()
    assert data["module"] == "ok"
    assert data["core"] == "ok"
    assert data["browser_runtime"] == "ok"
    assert data["chromium"] == "ok"
    assert data["profile_storage"] == "ok"

    # Ensure no secrets in output
    text_content = str(data)
    assert "cookie" not in text_content.lower()
    assert "token" not in text_content.lower()
    assert "secret" not in text_content.lower()

@patch("app.routers.health.httpx.AsyncClient.get", new_callable=AsyncMock)
def test_avito_health_alias_endpoint(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    res = client.get("/avito/health")
    assert res.status_code == 200
    assert res.json()["module"] == "ok"
