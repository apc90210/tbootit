from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_extension_download_returns_zip():
    """Verify /avito/extension/download returns a zip file."""
    res = client.get("/avito/extension/download")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    assert len(res.content) > 100
