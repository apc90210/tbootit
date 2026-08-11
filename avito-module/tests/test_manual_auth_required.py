import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import storage, schemas

client = TestClient(app)

def test_new_profile_unauthorized_by_default():
    p = schemas.AvitoAccountProfile(account_key="test_auth_req", display_name="Test Auth Req")
    storage.save_profile(p)

    res = client.get("/accounts/api/profiles")
    assert res.status_code == 200
    profiles = res.json()
    target = next((prof for prof in profiles if prof["account_key"] == "test_auth_req"), None)
    assert target is not None
    assert target["auth_status"] in ["unknown", "unauthorized"]

    storage.delete_profile("test_auth_req")
