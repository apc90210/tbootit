from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_browser_page_iframe_autoconnect():
    """Verify avito_browser.html iframe src uses autoconnect=1 and same-origin path."""
    res = client.get("/avito/accounts/acc_test/browser")
    assert res.status_code == 200
    assert "autoconnect=1" in res.text
    assert "path=avito/novnc/websockify" in res.text
