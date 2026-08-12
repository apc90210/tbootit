from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_extension_live_route_returns_200_and_ui():
    """Verify /avito/extension returns 200 (not 404) and expected UI elements."""
    res = client.get("/avito/extension")
    assert res.status_code == 200
    assert "Расширение Chrome" in res.text
    assert "Скачать расширение" in res.text
    assert "Создать новый код подключения" in res.text
