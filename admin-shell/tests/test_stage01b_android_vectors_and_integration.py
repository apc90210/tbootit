"""
Stage01B Android Client Protocol Vectors & Client Integration Tests.
Verifies cross-platform compatibility between Android client specifications
and the Technoreboot backend gateway.
"""

import base64
import hashlib
import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

from app.main import app, auth_manager, mobile_manager
from app.mobile_manager import (
    build_canonical_signing_payload,
    compute_body_sha256,
)

client = TestClient(app)


def _gen_android_keystore_p256_key():
    """Simulates Android Keystore P-256 (secp256r1) keypair generation and SPKI PEM export."""
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return priv, pub_pem


def _sign_canonical_payload(private_key, payload_bytes: bytes) -> str:
    """Signs canonical payload with SHA256withECDSA and returns Base64 DER."""
    sig_der = private_key.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig_der).decode("ascii")


def _get_pop_headers(credential_id: str, private_key, method: str, canonical_path: str, body: bytes = b"") -> dict:
    ch_resp = client.get("/api/mobile/challenge", params={"credential_id": credential_id})
    assert ch_resp.status_code == 200, ch_resp.text
    nonce = ch_resp.json()["nonce"]

    payload_bytes = build_canonical_signing_payload(
        credential_id=credential_id,
        nonce_hex=nonce,
        method=method,
        canonical_path=canonical_path,
        body_sha256=compute_body_sha256(body),
    )
    sig_b64 = _sign_canonical_payload(private_key, payload_bytes)
    return {
        "X-Mobile-Credential-Id": credential_id,
        "X-Mobile-Nonce": nonce,
        "X-Mobile-Signature": sig_b64,
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
    cert = auth_manager.create_user_certificate(f"Stage01B User {datetime.now(timezone.utc).timestamp()}")
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": cert["serial_hex"],
        "x-client-cert-fingerprint": cert["fingerprint_sha256"],
    }


# ===========================================================================
# 1. Android Vector Compatibility Tests
# ===========================================================================

def test_android_vector_1_get_no_query():
    p = build_canonical_signing_payload(
        credential_id="mcred_test001",
        nonce_hex="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        method="GET",
        canonical_path="/api/mobile/me",
        body_sha256=compute_body_sha256(b""),
    )
    expected = (
        "TRMOBILE1\n"
        "mcred_test001\n"
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef\n"
        "GET\n"
        "/api/mobile/me\n"
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    ).encode("utf-8")
    assert p == expected


def test_android_vector_2_get_with_query_sorting():
    p = build_canonical_signing_payload(
        credential_id="mcred_test002",
        nonce_hex="fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
        method="GET",
        canonical_path="/api/mobile/status?filter=active&limit=10&offset=0",
        body_sha256=compute_body_sha256(b""),
    )
    expected = (
        "TRMOBILE1\n"
        "mcred_test002\n"
        "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210\n"
        "GET\n"
        "/api/mobile/status?filter=active&limit=10&offset=0\n"
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    ).encode("utf-8")
    assert p == expected


def test_android_vector_3_post_json():
    body = b'{"action": "ping", "client": "android"}'
    p = build_canonical_signing_payload(
        credential_id="mcred_test003",
        nonce_hex="111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000",
        method="POST",
        canonical_path="/api/mobile/test-post",
        body_sha256=compute_body_sha256(body),
    )
    expected = (
        "TRMOBILE1\n"
        "mcred_test003\n"
        "111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000\n"
        "POST\n"
        "/api/mobile/test-post\n"
        "1b6100e0c542e44b2ec7bd5bf55ab175410f67259a77577319f5170f6a6b8db0"
    ).encode("utf-8")
    assert p == expected


def test_android_vector_4_unicode_cyrillic():
    body = '{"message": "Привет мир"}'.encode("utf-8")
    p = build_canonical_signing_payload(
        credential_id="mcred_test004",
        nonce_hex="aaaa0000bbbb1111cccc2222dddd3333eeee4444ffff5555aaaa6666bbbb7777",
        method="POST",
        canonical_path="/api/mobile/test-post",
        body_sha256=compute_body_sha256(body),
    )
    expected = (
        "TRMOBILE1\n"
        "mcred_test004\n"
        "aaaa0000bbbb1111cccc2222dddd3333eeee4444ffff5555aaaa6666bbbb7777\n"
        "POST\n"
        "/api/mobile/test-post\n"
        "be5b87df4682482bae7bdec3e0706d65f4bca632fc74914d7e8ab2e1999a1d46"
    ).encode("utf-8")
    assert p == expected


# ===========================================================================
# 2. End-to-End Android Client Flow Simulation
# ===========================================================================

def test_android_client_e2e_user_flow(user_headers):
    """
    Simulates:
    1. Pairing code creation on web
    2. Android client generating Keystore P-256 key
    3. Enrollment POST /api/mobile/enroll
    4. Retrieval of credential_id
    5. Proof-of-Possession GET /api/mobile/me
    6. Role validation: USER
    7. Owner-only endpoint blocked for USER
    """
    priv_key, pub_pem = _gen_android_keystore_p256_key()

    # 1. Web pairing generation
    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    assert gen_resp.status_code == 200
    pairing_code = gen_resp.json()["pairing_code"]

    # 2. Android enrollment
    dev_uuid = f"tr_android_{datetime.now(timezone.utc).timestamp()}"
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": pairing_code,
        "public_key": pub_pem,
        "device_identifier": dev_uuid,
        "device_name": "Google Pixel 8 Pro",
    })
    assert enroll_resp.status_code == 200
    enroll_data = enroll_resp.json()
    cred_id = enroll_data["credential_id"]
    assert enroll_data["effective_role"] == "USER"
    assert enroll_data["is_owner"] is False

    # Pairing code cannot be reused
    re_enroll = client.post("/api/mobile/enroll", json={
        "pairing_code": pairing_code,
        "public_key": pub_pem,
        "device_identifier": dev_uuid,
    })
    assert re_enroll.status_code in (400, 403)

    # 3. GET /api/mobile/me with PoP
    pop_headers = _get_pop_headers(cred_id, priv_key, "GET", "/api/mobile/me")
    me_resp = client.get("/api/mobile/me", headers=pop_headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["status"] == "authenticated"
    assert me_data["role"] == "USER"
    assert me_data["is_owner"] is False
    assert me_data["protocol_version"] == "TRMOBILE1"

    # 4. User cannot access owner-only
    owner_pop_headers = _get_pop_headers(cred_id, priv_key, "GET", "/api/mobile/owner-only")
    owner_resp = client.get("/api/mobile/owner-only", headers=owner_pop_headers)
    assert owner_resp.status_code == 403
    assert "Owner permissions required" in owner_resp.json()["detail"]


def test_android_client_e2e_owner_flow(owner_headers):
    """
    Simulates enrollment from owner web session:
    Role is inherited as OWNER and owner-only endpoints are accessible.
    """
    priv_key, pub_pem = _gen_android_keystore_p256_key()

    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=owner_headers)
    assert gen_resp.status_code == 200
    pairing_code = gen_resp.json()["pairing_code"]

    dev_uuid = f"tr_android_owner_{datetime.now(timezone.utc).timestamp()}"
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": pairing_code,
        "public_key": pub_pem,
        "device_identifier": dev_uuid,
        "device_name": "Owner Work Tablet",
    })
    assert enroll_resp.status_code == 200
    enroll_data = enroll_resp.json()
    cred_id = enroll_data["credential_id"]
    assert enroll_data["effective_role"] == "OWNER"
    assert enroll_data["is_owner"] is True

    # Owner accesses owner-only endpoint
    owner_pop_headers = _get_pop_headers(cred_id, priv_key, "GET", "/api/mobile/owner-only")
    owner_resp = client.get("/api/mobile/owner-only", headers=owner_pop_headers)
    assert owner_resp.status_code == 200
    assert owner_resp.json()["status"] == "ok"
