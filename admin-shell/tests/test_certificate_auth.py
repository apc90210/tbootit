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


def test_stage07a_r2_user_cert_issuance_modal_and_password_download():
    """Verify TEST A through TEST H from Stage 07A-R2 prompt."""
    from app.main import auth_manager
    owner = [c for c in auth_manager.list_certificates() if c.get("is_owner")][0]
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner["serial_hex"],
        "x-client-cert-fingerprint": owner["fingerprint_sha256"],
    }

    # TEST A: Issue a USER certificate through backend/API
    res = client.post("/admin-api/certificates", json={"name": "TEST-PASSWORD-UI"}, headers=owner_headers)
    assert res.status_code == 200
    created = res.json()
    assert "id" in created
    assert "password" in created and len(created["password"]) > 0
    cert_id = created["id"]
    gen_pass = created["password"]

    # TEST A & D: .p12 download works
    p12_res = client.get(f"/admin-api/certificates/{cert_id}/download", headers=owner_headers)
    assert p12_res.status_code == 200
    assert len(p12_res.content) > 0
    assert p12_res.headers["content-type"] == "application/x-pkcs12"

    # TEST E: Password .txt download works and contains exactly the generated password (+ optional newline)
    txt_res = client.get(f"/admin-api/certificates/{cert_id}/password.txt", headers=owner_headers)
    assert txt_res.status_code == 200
    assert txt_res.text.strip() == gen_pass

    # TEST F: Password is NOT written into certificate registry
    all_certs = auth_manager.list_certificates()
    target_in_reg = next(c for c in all_certs if c["id"] == cert_id)
    assert "password" not in target_in_reg

    # TEST B, C, D, E in UI: Verify UI contains persistent modal, copy button, download links, and no auto-reload
    ui_res = client.get("/certificates", headers=owner_headers)
    assert ui_res.status_code == 200
    assert 'id="certResultModal"' in ui_res.text
    assert "Сертификат выпущен" in ui_res.text
    assert 'id="resCertPass"' in ui_res.text
    assert 'id="btnCopyPass"' in ui_res.text and 'copyPassword()' in ui_res.text
    assert 'id="resDownloadP12"' in ui_res.text
    assert 'id="resDownloadTxt"' in ui_res.text
    assert 'id="btnCloseModal"' in ui_res.text and 'closeResultModal()' in ui_res.text
    # Ensure no auto-reloading timeout hides the password
    assert "setTimeout(() => { window.location.reload(); }, 1500)" not in ui_res.text

    # TEST G: Ordinary USER cannot access /certificates or admin-api
    user_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": target_in_reg["serial_hex"],
        "x-client-cert-fingerprint": target_in_reg["fingerprint_sha256"],
    }
    user_ui_res = client.get("/certificates", headers=user_headers)
    assert user_ui_res.status_code == 403

    user_api_res = client.get("/admin-api/certificates", headers=user_headers)
    assert user_api_res.status_code == 403

    # TEST H: Revocation works
    revoke_res = client.post(f"/admin-api/certificates/{cert_id}/revoke", headers=owner_headers)
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "REVOKED"


