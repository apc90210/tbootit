from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_browser_page_framebuffer_container():
    """Verify avito_browser.html contains iframe container for framebuffer rendering."""
    res = client.get("/avito/accounts/acc_test/browser")
    assert res.status_code == 200
    assert "iframe-container" in res.text
    assert "vncFrame" in res.text
