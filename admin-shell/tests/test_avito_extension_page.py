from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_extension_page_renders_200():
    """Verify /avito/extension page loads with instructions and download link."""
    res = client.get("/avito/extension")
    assert res.status_code == 200
    assert "Расширение Chrome" in res.text
    assert "Скачать расширение" in res.text
