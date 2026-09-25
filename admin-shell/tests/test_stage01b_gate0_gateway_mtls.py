"""
Technoreboot Stage01B Gate 0 & Gateway/mTLS Verification Tests.
Verifies the gateway architecture:
1. Browser routes without client certificate -> 401/403 DENY
2. Browser routes with valid USER/OWNER certificate -> 200 PASS
3. /api/mobile/enroll without browser cert -> gateway passthrough
4. /api/mobile/challenge without browser cert -> gateway passthrough
5. /api/mobile/me without PoP -> 401/403 DENY
6. /api/mobile/me with valid PoP -> 200 PASS
7. Revoked parent cert -> 403 DENY
8. Revoked device -> 403 DENY
9. Exact byte-for-byte protocol vector verification with docs/mobile_auth_protocol_TRMOBILE1.md
"""

import base64
import hashlib
import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app, auth_manager, mobile_manager
from app.mobile_manager import (
    build_canonical_signing_payload,
    compute_body_sha256,
)
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

client = TestClient(app)


def _gen_ec_keypair():
    priv = ec.generate_private_key(ec.SECP256R1())
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return priv, pub_pem


def _sign_payload(private_key, payload_bytes: bytes) -> str:
    sig = private_key.sign(
        payload_bytes,
        ec.ECDSA(hashes.SHA256()),
    )
    return base64.b64encode(sig).decode("ascii")


def _get_pop_headers(credential_id: str, private_key, method: str = "GET", canonical_path: str = "/api/mobile/me", body: bytes = b"") -> dict:
    ch_resp = client.get("/api/mobile/challenge", params={"credential_id": credential_id})
    assert ch_resp.status_code == 200, ch_resp.text
    nonce = ch_resp.json()["nonce"]
    payload = build_canonical_signing_payload(
        credential_id=credential_id,
        nonce_hex=nonce,
        method=method,
        canonical_path=canonical_path,
        body_sha256=compute_body_sha256(body),
    )
    sig_b64 = _sign_payload(private_key, payload)
    return {
        "x-mobile-credential-id": credential_id,
        "x-mobile-nonce": nonce,
        "x-mobile-signature": sig_b64,
    }


@pytest.fixture
def owner_headers():
    owner = auth_manager.get_certificate("owner")
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner["serial_hex"],
        "x-client-cert-fingerprint": owner["fingerprint_sha256"],
    }


@pytest.fixture
def user_headers():
    cert = auth_manager.create_user_certificate(f"Gate0 User {datetime.now(timezone.utc).timestamp()}")
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": cert["serial_hex"],
        "x-client-cert-fingerprint": cert["fingerprint_sha256"],
    }


# ===========================================================================
# 1. Gate 0: Browser Route without Client Cert -> DENIED
# ===========================================================================

def test_gate0_01_browser_no_cert_denied():
    resp = client.get("/internal-auth/verify")
    assert resp.status_code in (401, 403)
    assert "client certificate" in resp.json()["detail"].lower()


# ===========================================================================
# 2. Gate 0: Browser Route with Valid Cert -> ALLOWED
# ===========================================================================

def test_gate0_02_browser_valid_cert_allowed(user_headers, owner_headers):
    # User cert
    resp_user = client.get("/internal-auth/verify", headers=user_headers)
    assert resp_user.status_code == 200
    assert resp_user.json()["status"] == "ok"
    assert resp_user.headers["x-auth-is-owner"] == "0"

    # Owner cert
    resp_owner = client.get("/internal-auth/verify", headers=owner_headers)
    assert resp_owner.status_code == 200
    assert resp_owner.json()["status"] == "ok"
    assert resp_owner.headers["x-auth-is-owner"] == "1"


# ===========================================================================
# 3. Gate 0: Mobile Enroll Gateway Passthrough without Browser Cert
# ===========================================================================

def test_gate0_03_mobile_enroll_passthrough_without_cert():
    resp = client.get("/internal-auth/verify", headers={"x-original-uri": "/api/mobile/enroll"})
    assert resp.status_code == 200
    assert resp.json()["mode"] == "mobile_passthrough"
    assert resp.headers["x-auth-subject"] == "mobile_client"


# ===========================================================================
# 4. Gate 0: Mobile Challenge Gateway Passthrough without Browser Cert
# ===========================================================================

def test_gate0_04_mobile_challenge_passthrough_without_cert():
    resp = client.get("/internal-auth/verify", headers={"x-original-uri": "/api/mobile/challenge?credential_id=mcred_123"})
    assert resp.status_code == 200
    assert resp.json()["mode"] == "mobile_passthrough"
    assert resp.headers["x-auth-subject"] == "mobile_client"


# ===========================================================================
# 5. Gate 0: Mobile Protected Route Gateway Passthrough without Browser Cert
# ===========================================================================

def test_gate0_05_mobile_me_passthrough_without_cert():
    resp = client.get("/internal-auth/verify", headers={"x-original-uri": "/api/mobile/me"})
    assert resp.status_code == 200
    assert resp.json()["mode"] == "mobile_passthrough"


# ===========================================================================
# 6. Gate 0: Mobile Me without PoP -> DENIED at Application Layer
# ===========================================================================

def test_gate0_06_mobile_me_without_pop_denied():
    resp = client.get("/api/mobile/me")
    assert resp.status_code in (401, 403)
    assert "Proof of Possession" in resp.json()["detail"] or "signature" in resp.json()["detail"].lower()


# ===========================================================================
# 7. Gate 0: Mobile Me with Valid PoP -> PASS
# ===========================================================================

def test_gate0_07_mobile_me_with_valid_pop_pass(user_headers):
    priv, pub_pem = _gen_ec_keypair()
    # 1. Admin/Web creates pairing code
    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    assert gen_resp.status_code == 200
    code = gen_resp.json()["pairing_code"]

    # 2. Android device enrolls (without client cert, via public endpoint)
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_pem,
        "device_identifier": f"gate0-dev-{datetime.now(timezone.utc).timestamp()}",
        "device_name": "Gate0 Test Device",
    })
    assert enroll_resp.status_code == 200
    cred_id = enroll_resp.json()["credential_id"]

    # 3. Android signs challenge and calls /api/mobile/me
    pop_headers = _get_pop_headers(cred_id, priv, method="GET", canonical_path="/api/mobile/me")
    me_resp = client.get("/api/mobile/me", headers=pop_headers)
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["status"] == "authenticated"
    assert data["protocol_version"] == "TRMOBILE1"
    assert data["role"] == "USER"
    assert data["is_owner"] is False


# ===========================================================================
# 8. Gate 0: Revoked Parent Certificate -> DENIED
# ===========================================================================

def test_gate0_08_revoked_parent_denied():
    cert = auth_manager.create_user_certificate(f"Gate0 Parent {datetime.now(timezone.utc).timestamp()}")
    headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": cert["serial_hex"],
        "x-client-cert-fingerprint": cert["fingerprint_sha256"],
    }
    priv, pub_pem = _gen_ec_keypair()
    gen = client.post("/admin-api/mobile/pairing/generate", headers=headers)
    assert gen.status_code == 200
    code = gen.json()["pairing_code"]
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_pem,
        "device_identifier": f"gate0-parent-{datetime.now(timezone.utc).timestamp()}",
    })
    assert enroll_resp.status_code == 200
    cred_id = enroll_resp.json()["credential_id"]

    # Obtain challenge before revoke
    pop_h = _get_pop_headers(cred_id, priv, method="GET", canonical_path="/api/mobile/me")

    # Revoke parent cert
    auth_manager.revoke_certificate(cert["id"])

    # In-flight request rejected with 403
    resp = client.get("/api/mobile/me", headers=pop_h)
    assert resp.status_code == 403
    assert "parent" in resp.json()["detail"].lower()


# ===========================================================================
# 9. Gate 0: Revoked Device -> DENIED
# ===========================================================================

def test_gate0_09_revoked_device_denied(owner_headers):
    priv, pub_pem = _gen_ec_keypair()
    gen = client.post("/admin-api/mobile/pairing/generate", headers=owner_headers)
    assert gen.status_code == 200
    code = gen.json()["pairing_code"]
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_pem,
        "device_identifier": f"gate0-dev-rev-{datetime.now(timezone.utc).timestamp()}",
    })
    assert enroll_resp.status_code == 200
    cred_id = enroll_resp.json()["credential_id"]
    dev_id = enroll_resp.json()["device_id"]

    # Obtain challenge before revoke
    h_pending = _get_pop_headers(cred_id, priv, method="GET", canonical_path="/api/mobile/me")

    # Revoke device
    rev_resp = client.post(f"/admin-api/mobile/devices/{dev_id}/revoke", headers=owner_headers)
    assert rev_resp.status_code == 200

    # In-flight request rejected
    resp = client.get("/api/mobile/me", headers=h_pending)
    assert resp.status_code == 403
    assert "revoked" in resp.json()["detail"].lower()


# ===========================================================================
# 10. Protocol Test Vectors Byte-for-Byte Compatibility
# ===========================================================================

def test_gate0_10_protocol_vectors_exact_match():
    # Vector 1: Standard GET
    p1 = build_canonical_signing_payload(
        credential_id="mcred_test001",
        nonce_hex="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        method="GET",
        canonical_path="/api/mobile/me",
        body_sha256=compute_body_sha256(b""),
    )
    expected_p1 = (
        "TRMOBILE1\n"
        "mcred_test001\n"
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef\n"
        "GET\n"
        "/api/mobile/me\n"
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert p1 == expected_p1.encode("utf-8")

    # Vector 2: GET with query
    p2 = build_canonical_signing_payload(
        credential_id="mcred_test002",
        nonce_hex="fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
        method="GET",
        canonical_path="/api/mobile/status?filter=active&limit=10&offset=0",
        body_sha256=compute_body_sha256(b""),
    )
    expected_p2 = (
        "TRMOBILE1\n"
        "mcred_test002\n"
        "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210\n"
        "GET\n"
        "/api/mobile/status?filter=active&limit=10&offset=0\n"
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert p2 == expected_p2.encode("utf-8")

    # Vector 3: POST JSON
    body3 = b'{"action": "ping", "client": "android"}'
    p3 = build_canonical_signing_payload(
        credential_id="mcred_test003",
        nonce_hex="111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000",
        method="POST",
        canonical_path="/api/mobile/test-post",
        body_sha256=compute_body_sha256(body3),
    )
    expected_p3 = (
        "TRMOBILE1\n"
        "mcred_test003\n"
        "111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000\n"
        "POST\n"
        "/api/mobile/test-post\n"
        "1b6100e0c542e44b2ec7bd5bf55ab175410f67259a77577319f5170f6a6b8db0"
    )
    assert p3 == expected_p3.encode("utf-8")

    # Vector 4: Unicode body
    body4 = '{"message": "Привет мир"}'.encode("utf-8")
    p4 = build_canonical_signing_payload(
        credential_id="mcred_test004",
        nonce_hex="aaaa0000bbbb1111cccc2222dddd3333eeee4444ffff5555aaaa6666bbbb7777",
        method="POST",
        canonical_path="/api/mobile/test-post",
        body_sha256=compute_body_sha256(body4),
    )
    expected_p4 = (
        "TRMOBILE1\n"
        "mcred_test004\n"
        "aaaa0000bbbb1111cccc2222dddd3333eeee4444ffff5555aaaa6666bbbb7777\n"
        "POST\n"
        "/api/mobile/test-post\n"
        "be5b87df4682482bae7bdec3e0706d65f4bca632fc74914d7e8ab2e1999a1d46"
    )
    assert p4 == expected_p4.encode("utf-8")
