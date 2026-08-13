from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import httpx
from app.main import app

client = TestClient(app)

def test_media_proxy_returns_image():
    """Verify Admin Shell proxies /media/{path:path} requests to Core API."""
    mock_resp = httpx.Response(
        200,
        content=b"\xff\xd8\xff\xe0\x00\x10JFIF",
        headers={"content-type": "image/jpeg"}
    )
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp
        res = client.get("/media/product_photos/58_d9dc3f1c.jpg")
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/jpeg"
        assert res.content.startswith(b"\xff\xd8")
