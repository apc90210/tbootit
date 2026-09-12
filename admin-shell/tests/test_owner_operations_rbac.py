import pytest
from fastapi.testclient import TestClient
from app.main import app, auth_manager

client = TestClient(app)


@pytest.fixture
def seller_cert():
    users = [c for c in auth_manager.list_certificates() if not c.get("is_owner") and c.get("status") == "ACTIVE"]
    if users:
        return users[0]
    return auth_manager.create_user_certificate("Тестовый Продавец Operations RBAC")


@pytest.fixture
def owner_cert():
    owner = auth_manager.get_certificate("owner")
    assert owner is not None
    return owner


def test_user_forbidden_from_operations_page(seller_cert):
    """USER role certificate must receive 403 on /system/operations."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }
    resp = client.get("/system/operations", headers=seller_headers)
    assert resp.status_code == 403
    assert "Owner certificate required" in resp.json()["detail"]


def test_anonymous_forbidden_from_operations_page():
    """Anonymous requests must receive 403 on /system/operations."""
    resp = client.get("/system/operations")
    assert resp.status_code == 403
    assert "Owner certificate required" in resp.json()["detail"]


def test_user_forbidden_from_operations_api(seller_cert):
    """USER role certificate must receive 403 on all operations API endpoints."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }

    # Status
    status_resp = client.get("/admin-api/system/operations/status", headers=seller_headers)
    assert status_resp.status_code == 403
    assert "Owner certificate required" in status_resp.json()["detail"]

    # Sync
    sync_resp = client.post("/admin-api/system/operations/sync", headers=seller_headers)
    assert sync_resp.status_code == 403
    assert "Owner certificate required" in sync_resp.json()["detail"]

    # Update
    update_resp = client.post("/admin-api/system/operations/update", headers=seller_headers)
    assert update_resp.status_code == 403
    assert "Owner certificate required" in update_resp.json()["detail"]

    # Audit
    audit_resp = client.get("/admin-api/system/operations/audit", headers=seller_headers)
    assert audit_resp.status_code == 403
    assert "Owner certificate required" in audit_resp.json()["detail"]


def test_owner_allowed_operations_page(owner_cert):
    """OWNER certificate must be granted access to /system/operations."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }
    resp = client.get("/system/operations", headers=owner_headers)
    assert resp.status_code == 200
    assert "Управление операциями" in resp.text
    assert "Синхронизировать данные с VDS" in resp.text
    assert "UPDATE VDS" in resp.text


def test_owner_allowed_operations_status(owner_cert):
    """OWNER certificate can fetch operations status and audit."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }
    status_resp = client.get("/admin-api/system/operations/status", headers=owner_headers)
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert "is_local_dev" in data
    assert "schema_guard" in data
    assert "is_locked" in data

    audit_resp = client.get("/admin-api/system/operations/audit", headers=owner_headers)
    assert audit_resp.status_code == 200
    assert "records" in audit_resp.json()
