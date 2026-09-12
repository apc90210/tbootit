import os
import sys
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
admin_shell_path = str(REPO_ROOT / "admin-shell")
for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        mod = sys.modules[k]
        if hasattr(mod, "__file__") and mod.__file__ and "admin-shell" not in mod.__file__:
            sys.modules.pop(k, None)

if admin_shell_path in sys.path:
    sys.path.remove(admin_shell_path)
sys.path.insert(0, admin_shell_path)

import app.main as admin_main
app = admin_main.app
_is_local_dev = admin_main._is_local_dev
auth_manager = admin_main.auth_manager

client = TestClient(app)


@pytest.fixture
def owner_headers():
    return {"x-auth-is-owner": "1"}


def test_is_local_dev_detection(tmp_path, monkeypatch):
    """Verify _is_local_dev correctly evaluates environment and sentinel files."""
    # When prod env variable is set -> False
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert _is_local_dev() is False

    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    assert _is_local_dev() is False

    monkeypatch.delenv("APP_ENV", raising=False)


def test_production_environment_blocks_operations(monkeypatch, owner_headers):
    """On production / VDS, sync and update operations MUST be blocked with 403."""
    # Simulate VDS environment
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert _is_local_dev() is False

    # Try sync
    resp_sync = client.post("/admin-api/system/operations/sync", headers=owner_headers)
    assert resp_sync.status_code == 403
    assert "доступны только из локальной DEV-среды" in resp_sync.json()["detail"]

    # Try update
    resp_update = client.post("/admin-api/system/operations/update", headers=owner_headers)
    assert resp_update.status_code == 403
    assert "доступны только из локальной DEV-среды" in resp_update.json()["detail"]


def test_local_dev_environment_allows_operations(owner_headers):
    """In local dev environment, owner can trigger sync and update."""
    assert _is_local_dev() is True

    # Trigger sync
    resp_sync = client.post("/admin-api/system/operations/sync", headers=owner_headers)
    assert resp_sync.status_code == 200
    data = resp_sync.json()
    assert data["status"] == "queued"
    assert data["operation"] == "sync_vds_to_local"
    assert "job_id" in data
