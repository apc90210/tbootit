import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("httpx.AsyncClient.get")
def test_novnc_static_proxy(mock_get):
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.content = b"<html>noVNC Canvas</html>"
    mock_resp.headers = {"content-type": "text/html"}
    mock_get.return_value = mock_resp

    response = client.get("/avito/novnc/vnc.html")
    assert response.status_code == 200
    assert b"noVNC Canvas" in response.content

def test_websocket_endpoint_registration():
    routes = [r.path for r in app.routes]
    assert "/avito/novnc/websockify" in routes
