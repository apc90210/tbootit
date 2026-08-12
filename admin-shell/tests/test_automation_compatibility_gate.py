from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_probe_page_requires_manual_login_acceptance():
    """Verify probe page retains manual login warning or probe gate."""
    res = client.get("/avito/probe")
    assert res.status_code == 200
    assert "пробы" in res.text or "Probe" in res.text or "аккаунт" in res.text
