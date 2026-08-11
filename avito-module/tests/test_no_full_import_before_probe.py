import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import storage, schemas

client = TestClient(app)

def test_full_import_blocked_before_probe():
    """
    Test Blocker F & Gate rule:
    Attempts to trigger full account import without an authorized probe or allow_full=true
    must be blocked with HTTP 403 FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED.
    """
    p = schemas.AvitoAccountProfile(account_key="gated_acc_1", display_name="Заблокированный Профиль")
    storage.save_profile(p)

    # Attempt full import without probe
    res = client.post("/accounts/api/profiles/gated_acc_1/import", data={"scope": "all"})
    assert res.status_code == 403
    assert "FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED" in res.json()["detail"]

    # Cleanup
    storage.delete_profile("gated_acc_1")
