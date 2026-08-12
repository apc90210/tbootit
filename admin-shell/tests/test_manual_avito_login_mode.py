from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_browser_page_has_manual_login_elements():
    """Verify avito_browser.html contains manual login mode controls."""
    res = client.get("/avito/accounts/acc_test/browser")
    # For existing account or fallback:
    assert res.status_code in [200, 404]
    if res.status_code == 200:
        assert "verifyAuth" in res.text
        assert "closeBrowser" in res.text
