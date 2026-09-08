import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
from app.auth_manager import AuthManager
from app.main import app

client = TestClient(app)

@pytest.fixture
def temp_auth_dir():
    temp_dir = tempfile.mkdtemp(prefix="technoreboot_auth_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_auth_manager_initialization(temp_auth_dir):
    am = AuthManager(auth_dir=temp_auth_dir)
    assert os.path.exists(am.ca_cert_path)
    assert os.path.exists(am.ca_key_path)
    assert os.path.exists(am.server_cert_path)
    assert os.path.exists(am.server_key_path)
    assert os.path.exists(am.owner_password_file)
    assert len(am.get_owner_password()) > 0

    certs = am.list_certificates()
    assert len(certs) == 1
    owner = certs[0]
    assert owner["id"] == "owner"
    assert owner["is_owner"] is True
    assert owner["status"] == "ACTIVE"

def test_owner_revoke_protection(temp_auth_dir):
    am = AuthManager(auth_dir=temp_auth_dir)
    with pytest.raises(PermissionError, match="OWNER"):
        am.revoke_certificate("owner")

def test_user_lifecycle_and_verification(temp_auth_dir):
    am = AuthManager(auth_dir=temp_auth_dir)
    
    # Issue user certificate
    user_cert = am.create_user_certificate("Тестовый магазин")
    assert user_cert["name"] == "Тестовый магазин"
    assert user_cert["status"] == "ACTIVE"
    assert user_cert["is_owner"] is False
    assert "password" in user_cert
    
    p12_path, filename = am.get_p12_path(user_cert["id"])
    assert os.path.exists(p12_path)

    owner_cert = am.get_certificate("owner")

    # TEST B: No client certificate
    ok, code, msg, _ = am.verify_request(None, None, None, "/")
    assert not ok
    assert code == 403

    ok, code, msg, _ = am.verify_request("FAILED:bad_cert", "123", None, "/")
    assert not ok
    assert code == 403

    # TEST C: OWNER normal access
    ok, code, msg, c = am.verify_request("SUCCESS", owner_cert["serial_hex"], owner_cert["fingerprint_sha256"], "/")
    assert ok
    assert code == 200

    # TEST D: OWNER admin access
    ok, code, msg, c = am.verify_request("SUCCESS", owner_cert["serial_hex"], owner_cert["fingerprint_sha256"], "/certificates")
    assert ok
    assert code == 200

    # TEST F: USER normal access
    ok, code, msg, c = am.verify_request("SUCCESS", user_cert["serial_hex"], user_cert["fingerprint_sha256"], "/")
    assert ok
    assert code == 200

    # TEST G: USER admin denied
    ok, code, msg, c = am.verify_request("SUCCESS", user_cert["serial_hex"], user_cert["fingerprint_sha256"], "/certificates")
    assert not ok
    assert code == 403

    # TEST H: Revoke USER
    revoked = am.revoke_certificate(user_cert["id"])
    assert revoked["status"] == "REVOKED"
    assert revoked["revoked_at"] is not None

    # TEST I: Revoked USER denied
    ok, code, msg, c = am.verify_request("SUCCESS", user_cert["serial_hex"], user_cert["fingerprint_sha256"], "/")
    assert not ok
    assert code == 403
    assert "REVOKED" in msg

def test_persistence(temp_auth_dir):
    am1 = AuthManager(auth_dir=temp_auth_dir)
    user = am1.create_user_certificate("Пользователь 1")
    am1.revoke_certificate(user["id"])
    
    with open(am1.ca_cert_path, "rb") as f:
        ca_cert_bytes = f.read()
    owner1 = am1.get_certificate("owner")

    # Re-instantiate in the same directory
    am2 = AuthManager(auth_dir=temp_auth_dir)
    with open(am2.ca_cert_path, "rb") as f:
        assert f.read() == ca_cert_bytes

    owner2 = am2.get_certificate("owner")
    assert owner1["serial_hex"] == owner2["serial_hex"]
    assert owner1["fingerprint_sha256"] == owner2["fingerprint_sha256"]

    revoked_user = am2.get_certificate(user["id"])
    assert revoked_user is not None
    assert revoked_user["status"] == "REVOKED"

def test_endpoints_via_testclient():
    from app.main import auth_manager
    # Test /internal-auth/verify with no headers
    resp = client.get("/internal-auth/verify")
    assert resp.status_code == 403

    owner = [c for c in auth_manager.list_certificates() if c.get("is_owner")][0]
    
    # Test with valid owner headers
    resp = client.get("/internal-auth/verify", headers={
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner["serial_hex"],
        "x-client-cert-fingerprint": owner["fingerprint_sha256"],
        "x-original-uri": "/",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["is_owner"] is True

    # Test /certificates admin page with owner
    resp = client.get("/certificates", headers={
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner["serial_hex"],
        "x-client-cert-fingerprint": owner["fingerprint_sha256"],
    })
    assert resp.status_code == 200
    assert "ТЕХНОРЕБУТ — ДОСТУП" in resp.text

