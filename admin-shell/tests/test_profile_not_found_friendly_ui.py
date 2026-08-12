from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_missing_profile_browser_page_renders_friendly_ui():
    """Verify requesting non-existent account browser page returns friendly 404 HTML."""
    res = client.get("/avito/accounts/acc_nonexistent_xyz/browser")
    assert res.status_code == 404
    assert "Профиль Avito не найден" in res.text
    assert "К аккаунтам Avito" in res.text
