"""
Stage01A — Mobile Access Foundation Tests (updated for R2 PoP scheme)

All original R1 test scenarios preserved, adapted to use Challenge-Response
Proof of Possession (PoP) authentication instead of bearer tokens.

Tests:
 01. active USER certificate creates pairing code -> PASS
 02. active OWNER certificate creates pairing code -> PASS
 03. expired/revoked parent cannot create pairing -> FAIL (403)
 04. pairing code one-time use -> FAIL (400) on reuse
 05. pairing code TTL enforced -> FAIL (400) when expired
 06. enrollment creates device without private key in DB
 07. USER mobile access retains USER permissions
 08. OWNER mobile access receives OWNER permissions
 09. payload role spoofing is forbidden
 10. parent revoke immediately blocks mobile credential
 11. revoke single device blocks only that device
 12. Android web page access (browser mTLS)
 13+14. PRAGMA foreign_key_check and quick_check
"""

import base64
import sqlite3
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

from app.main import app, auth_manager, mobile_manager
from app.mobile_manager import build_canonical_signing_payload, compute_body_sha256

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers (R3: mobile auth uses canonical request-bound PoP)
# ---------------------------------------------------------------------------

def _gen_keypair():
    """Generate ECDSA P-256 key pair (simulates Android Keystore)."""
    priv = ec.generate_private_key(ec.SECP256R1())
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return priv, pub_pem


def _generate_test_public_key() -> str:
    """Generate a mock Android Keystore EC public key PEM (public only, no private)."""
    _, pub_pem = _gen_keypair()
    return pub_pem


def _sign_request(
    private_key,
    credential_id: str,
    nonce_hex: str,
    method: str = "GET",
    path: str = "/api/mobile/me",
    body: bytes = b"",
) -> str:
    """Sign canonical request payload with ECDSA P-256 SHA-256."""
    payload = build_canonical_signing_payload(
        credential_id=credential_id,
        nonce_hex=nonce_hex,
        method=method,
        canonical_path=path,
        body_sha256=compute_body_sha256(body),
    )
    sig = private_key.sign(payload, ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig).decode("utf-8")


def _sign_nonce(private_key, nonce_hex: str, credential_id: str = "mcred_default") -> str:
    return _sign_request(private_key, credential_id, nonce_hex)


def _get_pop_headers(
    credential_id: str,
    private_key,
    method: str = "GET",
    path: str = "/api/mobile/me",
    body: bytes = b"",
) -> dict:
    """Get a fresh challenge nonce and sign the canonical request to produce PoP headers."""
    ch_resp = client.get("/api/mobile/challenge", params={"credential_id": credential_id})
    assert ch_resp.status_code == 200, f"Challenge failed: {ch_resp.text}"
    nonce_hex = ch_resp.json()["nonce"]
    sig = _sign_request(
        private_key,
        credential_id=credential_id,
        nonce_hex=nonce_hex,
        method=method,
        path=path,
        body=body,
    )
    return {
        "X-Mobile-Credential-Id": credential_id,
        "X-Mobile-Nonce": nonce_hex,
        "X-Mobile-Signature": sig,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def owner_headers():
    owner = auth_manager.get_certificate("owner")
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner["serial_hex"],
        "x-client-cert-fingerprint": owner["fingerprint_sha256"],
    }


@pytest.fixture
def active_user_cert():
    name = f"Test Seller {datetime.now(timezone.utc).timestamp()}"
    cert = auth_manager.create_user_certificate(name)
    return cert


@pytest.fixture
def user_headers(active_user_cert):
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": active_user_cert["serial_hex"],
        "x-client-cert-fingerprint": active_user_cert["fingerprint_sha256"],
    }


# ---------------------------------------------------------------------------
# TEST 1 & 2: Active USER and OWNER certificates create pairing code
# ---------------------------------------------------------------------------

def test_01_active_user_creates_pairing_code(user_headers, active_user_cert):
    resp = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "pairing_code" in data
    assert len(data["pairing_code"]) >= 6
    assert data["parent_certificate_id"] == active_user_cert["id"]
    assert data["expires_in_seconds"] == 600

    # Verify audit log
    with mobile_manager._get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM audit_log WHERE action = 'mobile.pairing_code_created' ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        assert row is not None
        assert active_user_cert["id"] in row["new_value"]


def test_02_active_owner_creates_pairing_code(owner_headers):
    resp = client.post("/admin-api/mobile/pairing/generate", headers=owner_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "pairing_code" in data
    assert data["parent_certificate_id"] == "owner"
    assert data["expires_in_seconds"] == 600


# ---------------------------------------------------------------------------
# TEST 3: Revoked parent certificate cannot create pairing code
# ---------------------------------------------------------------------------

def test_03_revoked_parent_cannot_create_pairing():
    rev_cert = auth_manager.create_user_certificate("To Be Revoked")
    auth_manager.revoke_certificate(rev_cert["id"])

    rev_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": rev_cert["serial_hex"],
        "x-client-cert-fingerprint": rev_cert["fingerprint_sha256"],
    }
    resp = client.post("/admin-api/mobile/pairing/generate", headers=rev_headers)
    assert resp.status_code == 403

    # Anonymous / no cert also 403
    resp_anon = client.post("/admin-api/mobile/pairing/generate")
    assert resp_anon.status_code == 403


# ---------------------------------------------------------------------------
# TEST 4 & 5: Pairing code is one-time use and TTL enforced
# ---------------------------------------------------------------------------

def test_04_pairing_code_one_time_use(user_headers):
    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    code = gen_resp.json()["pairing_code"]
    priv, pub_key = _gen_keypair()

    # First enrollment -> SUCCESS
    enroll_resp1 = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_key,
        "device_identifier": f"android-dev-{datetime.now().timestamp()}-1",
        "device_name": "Pixel 8 Pro",
    })
    assert enroll_resp1.status_code == 200, enroll_resp1.text
    assert enroll_resp1.json()["status"] == "enrolled"

    # Second enrollment with SAME code -> FAIL 400
    priv2, pub_key2 = _gen_keypair()
    enroll_resp2 = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_key2,
        "device_identifier": f"android-dev-{datetime.now().timestamp()}-2",
        "device_name": "Pixel 8 Pro Replay",
    })
    assert enroll_resp2.status_code == 400
    assert "уже был использован" in enroll_resp2.json()["detail"]


def test_05_pairing_code_ttl_enforced(user_headers):
    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    code = gen_resp.json()["pairing_code"]
    _, pub_key = _gen_keypair()

    # Manually expire code in DB
    past_iso = "2020-01-01T00:00:00+00:00"
    with mobile_manager._get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE mobile_pairing_codes SET expires_at = ? WHERE code = ?", (past_iso, code))
        conn.commit()

    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_key,
        "device_identifier": f"android-dev-{datetime.now().timestamp()}-expired",
        "device_name": "Expired Device",
    })
    assert enroll_resp.status_code == 400
    assert "истёк" in enroll_resp.json()["detail"]


# ---------------------------------------------------------------------------
# TEST 6: Enrollment creates device without storing private key
# ---------------------------------------------------------------------------

def test_06_enrollment_creates_device_without_private_key(user_headers, active_user_cert):
    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    code = gen_resp.json()["pairing_code"]
    priv, pub_key = _gen_keypair()
    dev_id_str = f"sec-check-device-{datetime.now().timestamp()}"

    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_key,
        "device_identifier": dev_id_str,
        "device_name": "Samsung Galaxy S24",
    })
    assert enroll_resp.status_code == 200
    data = enroll_resp.json()
    assert "credential_id" in data
    assert "mobile_token" not in data  # R2: no bearer token
    assert data["auth_scheme"] == "challenge_response_pop"

    # Verify database contents
    with mobile_manager._get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM mobile_devices WHERE device_identifier = ?", (dev_id_str,))
        dev_row = cur.fetchone()
        assert dev_row is not None
        assert dev_row["parent_certificate_id"] == active_user_cert["id"]
        assert dev_row["status"] == "active"

        cur.execute("SELECT * FROM mobile_credentials WHERE mobile_device_id = ?", (dev_row["id"],))
        cred_row = cur.fetchone()
        assert cred_row is not None
        assert cred_row["public_key"].strip() == pub_key.strip()
        assert "private" not in cred_row["public_key"].lower()
        # R3: credential_token_hash is unused (None)
        assert cred_row["credential_token_hash"] is None

        # Verify audit entries
        cur.execute(
            "SELECT action FROM audit_log WHERE entity_type = 'mobile_device' AND entity_id = ?",
            (dev_row["id"],),
        )
        actions = [r["action"] for r in cur.fetchall()]
        assert "mobile.device_enrolled" in actions


# ---------------------------------------------------------------------------
# TEST 7 & 8: USER and OWNER role permission inheritance (R2 PoP)
# ---------------------------------------------------------------------------

def test_07_user_mobile_access_retains_user_permissions(user_headers):
    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    code = gen_resp.json()["pairing_code"]
    priv, pub_key = _gen_keypair()
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_key,
        "device_identifier": f"user-phone-{datetime.now().timestamp()}",
        "device_name": "User Phone",
    })
    credential_id = enroll_resp.json()["credential_id"]
    assert enroll_resp.json()["is_owner"] is False

    pop_headers = _get_pop_headers(credential_id, priv)
    me_resp = client.get("/api/mobile/me", headers=pop_headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["role"] == "USER"
    assert me_data["is_owner"] is False

    # Owner-only endpoint -> 403 Forbidden (new nonce required, signed for /api/mobile/owner-only)
    pop_headers2 = _get_pop_headers(credential_id, priv, path="/api/mobile/owner-only")
    owner_only_resp = client.get("/api/mobile/owner-only", headers=pop_headers2)
    assert owner_only_resp.status_code == 403
    assert "Owner permissions required" in owner_only_resp.json()["detail"]


def test_08_owner_mobile_access_receives_owner_permissions(owner_headers):
    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=owner_headers)
    code = gen_resp.json()["pairing_code"]
    priv, pub_key = _gen_keypair()
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_key,
        "device_identifier": f"owner-phone-{datetime.now().timestamp()}",
        "device_name": "Owner Phone",
    })
    credential_id = enroll_resp.json()["credential_id"]
    assert enroll_resp.json()["is_owner"] is True

    pop_headers = _get_pop_headers(credential_id, priv)
    me_resp = client.get("/api/mobile/me", headers=pop_headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["role"] == "OWNER"
    assert me_data["is_owner"] is True

    # Owner-only endpoint -> 200 OK (new nonce required, signed for /api/mobile/owner-only)
    pop_headers2 = _get_pop_headers(credential_id, priv, path="/api/mobile/owner-only")
    owner_only_resp = client.get("/api/mobile/owner-only", headers=pop_headers2)
    assert owner_only_resp.status_code == 200
    assert owner_only_resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# TEST 9: Payload role spoof escalation forbidden
# ---------------------------------------------------------------------------

def test_09_payload_role_spoofing_forbidden(user_headers):
    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    code = gen_resp.json()["pairing_code"]
    priv, pub_key = _gen_keypair()

    # Attacker injects role: OWNER in body
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_key,
        "device_identifier": f"spoof-phone-{datetime.now().timestamp()}",
        "device_name": "Spoof Phone",
        "role": "OWNER",
        "is_owner": True,
    })
    assert enroll_resp.status_code == 200
    data = enroll_resp.json()
    assert data["effective_role"] == "USER"
    assert data["is_owner"] is False
    credential_id = data["credential_id"]

    # Even with spoofed PoP headers, server enforces effective role
    pop_headers = _get_pop_headers(credential_id, priv)
    pop_headers["X-Client-Role"] = "OWNER"
    pop_headers["X-Auth-Is-Owner"] = "1"
    me_resp = client.get("/api/mobile/me", headers=pop_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "USER"
    assert me_resp.json()["is_owner"] is False

    # Owner-only route still rejects
    pop_headers2 = _get_pop_headers(credential_id, priv)
    owner_resp = client.get("/api/mobile/owner-only", headers=pop_headers2)
    assert owner_resp.status_code == 403


# ---------------------------------------------------------------------------
# TEST 10: Revoking parent certificate automatically blocks mobile credential
# ---------------------------------------------------------------------------

def test_10_parent_revoke_immediately_blocks_mobile_credential():
    cert = auth_manager.create_user_certificate("Parent Cert For Auto Revoke Test")
    headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": cert["serial_hex"],
        "x-client-cert-fingerprint": cert["fingerprint_sha256"],
    }
    priv, pub_key = _gen_keypair()
    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=headers)
    code = gen_resp.json()["pairing_code"]
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_key,
        "device_identifier": f"auto-revoke-dev-{datetime.now().timestamp()}",
        "device_name": "Auto Revoke Test Phone",
    })
    credential_id = enroll_resp.json()["credential_id"]

    # Step 1: Parent active -> Mobile auth PASS
    pop_hdrs = _get_pop_headers(credential_id, priv)
    step1_resp = client.get("/api/mobile/me", headers=pop_hdrs)
    assert step1_resp.status_code == 200

    # Step 2: Revoke parent certificate
    auth_manager.revoke_certificate(cert["id"])

    # Step 3: Same mobile credential (new challenge + correct sig) FAIL without app re-issue
    pop_hdrs_after = _get_pop_headers(credential_id, priv)
    step3_resp = client.get("/api/mobile/me", headers=pop_hdrs_after)
    assert step3_resp.status_code == 403
    assert "revoked" in step3_resp.json()["detail"].lower() or "parent" in step3_resp.json()["detail"].lower()

    # Verify audit log captures parent revoke rejection
    with mobile_manager._get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM audit_log WHERE action = 'mobile.auth_rejected_parent_revoked' ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        assert row is not None
        assert "revoked" in row["comment"].lower() or "missing" in row["comment"].lower()


# ---------------------------------------------------------------------------
# TEST 11: Revoking an individual mobile device blocks only that device
# ---------------------------------------------------------------------------

def test_11_revoke_single_device_blocks_only_that_device(user_headers, active_user_cert):
    priv_a, pub_a = _gen_keypair()
    priv_b, pub_b = _gen_keypair()

    # Enroll Device A
    gen_a = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    enroll_a = client.post("/api/mobile/enroll", json={
        "pairing_code": gen_a.json()["pairing_code"],
        "public_key": pub_a,
        "device_identifier": f"multi-dev-a-{datetime.now().timestamp()}",
        "device_name": "Phone A",
    }).json()

    # Enroll Device B
    gen_b = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    enroll_b = client.post("/api/mobile/enroll", json={
        "pairing_code": gen_b.json()["pairing_code"],
        "public_key": pub_b,
        "device_identifier": f"multi-dev-b-{datetime.now().timestamp()}",
        "device_name": "Phone B",
    }).json()

    cred_id_a = enroll_a["credential_id"]
    cred_id_b = enroll_b["credential_id"]
    dev_a_id = enroll_a["device_id"]

    # Both work initially
    assert client.get("/api/mobile/me", headers=_get_pop_headers(cred_id_a, priv_a)).status_code == 200
    assert client.get("/api/mobile/me", headers=_get_pop_headers(cred_id_b, priv_b)).status_code == 200

    # Revoke Device A
    revoke_resp = client.post(f"/admin-api/mobile/devices/{dev_a_id}/revoke", headers=user_headers)
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["status"] == "revoked"

    # Device A challenge is now blocked (credential revoked)
    ch_resp_a = client.get("/api/mobile/challenge", params={"credential_id": cred_id_a})
    assert ch_resp_a.status_code in (403, 400)

    # Device B continues to work normally
    resp_b_after = client.get("/api/mobile/me", headers=_get_pop_headers(cred_id_b, priv_b))
    assert resp_b_after.status_code == 200

    # Parent certificate is still ACTIVE
    parent_cert = auth_manager.get_certificate(active_user_cert["id"])
    assert parent_cert["status"] == "ACTIVE"


# ---------------------------------------------------------------------------
# TEST 12: Web page foundation (/android)
# ---------------------------------------------------------------------------

def test_12_android_web_page_access(owner_headers, user_headers):
    # Anonymous -> 403
    resp_anon = client.get("/android")
    assert resp_anon.status_code == 403

    # OWNER access -> 200 OK with MVP badge and disabled APK button
    resp_owner = client.get("/android", headers=owner_headers)
    assert resp_owner.status_code == 200
    assert "Android приложение" in resp_owner.text
    assert "MVP в разработке" in resp_owner.text
    assert "Подключить устройство" in resp_owner.text
    assert "Скачать APK (в разработке)" in resp_owner.text

    # USER access -> 200 OK
    resp_user = client.get("/android", headers=user_headers)
    assert resp_user.status_code == 200
    assert "Android приложение" in resp_user.text


# ---------------------------------------------------------------------------
# TEST 13 & 14: SQLite PRAGMA foreign_key_check and quick_check
# ---------------------------------------------------------------------------

def test_13_14_sqlite_pragmas():
    with mobile_manager._get_connection() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_key_check;")
        fk_violations = cur.fetchall()
        assert len(fk_violations) == 0, f"Foreign key violations found: {fk_violations}"

        cur.execute("PRAGMA quick_check;")
        qc = [tuple(r) for r in cur.fetchall()]
        assert qc == [("ok",)]
