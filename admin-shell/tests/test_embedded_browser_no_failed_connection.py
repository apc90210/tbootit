from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_browser_page_has_reconnect_fallback_ui():
    """Verify avito_browser.html contains reloadVncFrame fallback script and container."""
    res = client.get("/avito/accounts/acc_test/browser")
    assert res.status_code == 200
    assert "vncErrorContainer" in res.text
    assert "reloadVncFrame()" in res.text
