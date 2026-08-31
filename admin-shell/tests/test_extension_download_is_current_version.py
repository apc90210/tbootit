from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extension_download_is_current_version():
    """Verify /avito/extension/download returns versioned filename and Cache-Control headers."""
    res = client.get("/avito/extension/download")
    assert res.status_code == 200
    assert "0.2.33" in res.headers.get("content-disposition", "")
    assert "no-store" in res.headers.get("cache-control", "")
