import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import storage, schemas

client = TestClient(app)

def test_discover_blocked_when_unauthorized():
    p = schemas.AvitoAccountProfile(account_key="test_blocked", display_name="Test Blocked", auth_status="unauthorized")
    storage.save_profile(p)

    res = client.get("/accounts/api/profiles/test_blocked/discover")
    assert res.status_code == 409
    assert "AUTH_REQUIRED" in res.json()["detail"]

    storage.delete_profile("test_blocked")

def test_probe_import_blocked_when_unauthorized():
    p = schemas.AvitoAccountProfile(account_key="test_blocked2", display_name="Test Blocked 2", auth_status="unauthorized")
    storage.save_profile(p)

    res = client.post("/accounts/api/profiles/test_blocked2/probe-import", json={"external_item_id": "123456"})
    assert res.status_code == 409
    assert "AUTH_REQUIRED" in res.json()["detail"]

    storage.delete_profile("test_blocked2")
