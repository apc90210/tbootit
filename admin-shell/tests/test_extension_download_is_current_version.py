from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extension_download_is_current_version():
    """Verify /avito/extension/download returns versioned filename and Cache-Control headers."""
    res = client.get("/avito/extension/download")
    assert res.status_code == 200
    assert any(v in res.headers.get("content-disposition", "") for v in ("0.2.53", "0.2.54"))
    assert "no-store" in res.headers.get("cache-control", "")
