"""
Stage01A R3 — Request Binding Security Tests

Verifies that mobile Proof of Possession (PoP) cryptographically binds
each request to its method, canonical path, body, credential_id, and nonce:
  1. valid signature for correct GET endpoint -> PASS
  2. signature for endpoint A used on endpoint B -> FAIL (403)
  3. signature for GET used for POST -> FAIL (403)
  4. signature for body A used with body B -> FAIL (403)
  5. same nonce repeated -> FAIL (403)
  6. nonce for credential A + signature for credential B -> FAIL (401/403)
  7. expired nonce -> FAIL (401)
  8. wrong private key -> FAIL (403)
  9. missing signature headers -> FAIL (401)
 10. atomic race-safety double-submit -> exactly 1 PASS, 1 FAIL (403)
 11. public key validation: SECP256R1 accepted -> PASS
 12. public key validation: RSA key rejected -> FAIL (400)
 13. public key validation: unsupported curve rejected -> FAIL (400)
 14. public key validation: malformed PEM rejected -> FAIL (400)
 15. public key validation: private key material rejected -> FAIL (400)
 16. public key validation: payload > 4096 bytes rejected -> FAIL (400)
 17. re-enrollment duplicate device supersedes old credentials -> PASS
 18. parent revoked -> FAIL (403)
 19. device revoked -> FAIL (403)
 20. USER cannot escalate to OWNER -> FAIL (403)
 21. query parameter alteration invalidates signature -> FAIL (403)
 22. SQLite PRAGMA foreign_key_check clean & quick_check ok
"""

import base64
import concurrent.futures
import hashlib
import sqlite3
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from cryptography.hazmat.primitives.asymmetric import ec, rsa, ed25519
from cryptography.hazmat.primitives import hashes, serialization

from app.main import app, auth_manager, mobile_manager
from app.mobile_manager import (
    build_canonical_signing_payload,
    compute_body_sha256,
    validate_and_canonicalize_public_key,
    PROTOCOL_VERSION,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gen_ec_keypair():
    """Generate ECDSA P-256 (SECP256R1) key pair."""
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return priv, pub_pem


def _sign_request(
    private_key,
    credential_id: str,
    nonce_hex: str,
    method: str = "GET",
    canonical_path: str = "/api/mobile/me",
    body: bytes = b"",
) -> str:
    """Sign canonical request payload with ECDSA P-256 SHA-256."""
    payload = build_canonical_signing_payload(
        credential_id=credential_id,
        nonce_hex=nonce_hex,
        method=method,
        canonical_path=canonical_path,
        body_sha256=compute_body_sha256(body),
    )
    sig = private_key.sign(payload, ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig).decode("utf-8")


def _enroll(headers, private_key, pub_pem, device_suffix=""):
    """Enroll a device with given public key."""
    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=headers)
    assert gen_resp.status_code == 200, gen_resp.text
    code = gen_resp.json()["pairing_code"]

    dev_id = f"r3-dev-{datetime.now(timezone.utc).timestamp()}{device_suffix}"
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_pem,
        "device_identifier": dev_id,
        "device_name": f"R3 Device {device_suffix}",
    })
    assert enroll_resp.status_code == 200, enroll_resp.text
    data = enroll_resp.json()
    return data["credential_id"], dev_id


def _get_pop_headers(
    credential_id: str,
    private_key,
    method: str = "GET",
    canonical_path: str = "/api/mobile/me",
    body: bytes = b"",
) -> dict:
    """Obtain challenge and generate valid request-bound PoP headers."""
    ch_resp = client.get("/api/mobile/challenge", params={"credential_id": credential_id})
    assert ch_resp.status_code == 200, ch_resp.text
    nonce_hex = ch_resp.json()["nonce"]
    sig = _sign_request(
        private_key=private_key,
        credential_id=credential_id,
        nonce_hex=nonce_hex,
        method=method,
        canonical_path=canonical_path,
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
def user_cert():
    cert = auth_manager.create_user_certificate(f"R3 User {datetime.now(timezone.utc).timestamp()}")
    return cert


@pytest.fixture
def user_headers(user_cert):
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": user_cert["serial_hex"],
        "x-client-cert-fingerprint": user_cert["fingerprint_sha256"],
    }


# ===========================================================================
# 1. Valid signature for correct GET endpoint -> PASS
# ===========================================================================

def test_01_valid_signature_correct_get_pass(user_headers):
    priv, pub_pem = _gen_ec_keypair()
    credential_id, _ = _enroll(user_headers, priv, pub_pem, "-t01")

    headers = _get_pop_headers(credential_id, priv, method="GET", canonical_path="/api/mobile/me")
    resp = client.get("/api/mobile/me", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "authenticated"
    assert data["protocol_version"] == PROTOCOL_VERSION
    assert data["role"] == "USER"


# ===========================================================================
# 2. Signature for endpoint A used on endpoint B -> FAIL
# ===========================================================================

def test_02_signature_for_endpoint_a_used_on_endpoint_b_fail(user_headers):
    """
    Attacker captures signature constructed for /api/mobile/me and tries to replay it
    on /api/mobile/owner-only or /api/mobile/status.
    Server computes canonical payload with the actual target path -> signature mismatch -> 403.
    """
    priv, pub_pem = _gen_ec_keypair()
    credential_id, _ = _enroll(user_headers, priv, pub_pem, "-t02")

    # Sign explicitly for /api/mobile/me
    headers_for_me = _get_pop_headers(credential_id, priv, method="GET", canonical_path="/api/mobile/me")

    # Attempt to send to /api/mobile/owner-only
    resp = client.get("/api/mobile/owner-only", headers=headers_for_me)
    assert resp.status_code == 403, f"Expected 403 path substitution rejection, got {resp.status_code}"
    assert "signature" in resp.json()["detail"].lower() or "proof of possession" in resp.json()["detail"].lower()


# ===========================================================================
# 3. Signature for GET used for POST -> FAIL
# ===========================================================================

def test_03_signature_for_get_used_for_post_fail(user_headers):
    """
    Attacker captures a GET signature and tries to use it on a POST endpoint.
    Method in signature ('GET') != server method ('POST') -> 403.
    """
    priv, pub_pem = _gen_ec_keypair()
    credential_id, _ = _enroll(user_headers, priv, pub_pem, "-t03")

    # Sign for GET /api/mobile/test-post
    headers_get = _get_pop_headers(credential_id, priv, method="GET", canonical_path="/api/mobile/test-post")

    # Send POST with those headers
    resp = client.post("/api/mobile/test-post", headers=headers_get, content=b"")
    assert resp.status_code == 403, f"Expected 403 method substitution rejection, got {resp.status_code}"
    assert "signature" in resp.json()["detail"].lower() or "proof of possession" in resp.json()["detail"].lower()


# ===========================================================================
# 4. Signature for body A used with body B -> FAIL
# ===========================================================================

def test_04_signature_for_body_a_used_with_body_b_fail(user_headers):
    """
    Attacker signs a request with body A (e.g. b'{"action": "safe_action"}'), but modifies the body
    in transit to body B (e.g. b'{"action": "malicious_tampered_action"}').
    Server computes body_sha256 of body B -> mismatch with signed payload -> 403.
    """
    priv, pub_pem = _gen_ec_keypair()
    credential_id, _ = _enroll(user_headers, priv, pub_pem, "-t04")

    body_a = b'{"action": "safe_action"}'
    body_b = b'{"action": "malicious_tampered_action"}'

    # Sign for body A
    headers_for_a = _get_pop_headers(
        credential_id,
        priv,
        method="POST",
        canonical_path="/api/mobile/test-post",
        body=body_a,
    )

    # Send body B with signature produced for body A
    resp = client.post("/api/mobile/test-post", headers=headers_for_a, content=body_b)
    assert resp.status_code == 403, f"Expected 403 body tampering rejection, got {resp.status_code}"
    assert "signature" in resp.json()["detail"].lower() or "proof of possession" in resp.json()["detail"].lower()

    # Now verify that sending body A with signature produced for body A succeeds:
    headers_for_a_fresh = _get_pop_headers(
        credential_id,
        priv,
        method="POST",
        canonical_path="/api/mobile/test-post",
        body=body_a,
    )
    resp_ok = client.post("/api/mobile/test-post", headers=headers_for_a_fresh, content=body_a)
    assert resp_ok.status_code == 200, resp_ok.text
    assert resp_ok.json()["body_received_len"] == len(body_a)


# ===========================================================================
# 5. Same nonce repeated -> FAIL (Replay Protection)
# ===========================================================================

def test_05_same_nonce_repeated_fail(user_headers):
    """Once consumed, replaying the same nonce fails with 403."""
    priv, pub_pem = _gen_ec_keypair()
    credential_id, _ = _enroll(user_headers, priv, pub_pem, "-t05")

    headers = _get_pop_headers(credential_id, priv, method="GET", canonical_path="/api/mobile/me")
    resp1 = client.get("/api/mobile/me", headers=headers)
    assert resp1.status_code == 200

    resp2 = client.get("/api/mobile/me", headers=headers)
    assert resp2.status_code in (403, 401)
    assert "replay" in resp2.json()["detail"].lower() or "used" in resp2.json()["detail"].lower()


# ===========================================================================
# 6. Nonce for credential A + signature for credential B -> FAIL
# ===========================================================================

def test_06_nonce_for_cred_a_with_cred_b_fail(user_headers):
    """
    Challenge nonce issued for credential A cannot be used with credential B.
    """
    priv_a, pub_a = _gen_ec_keypair()
    priv_b, pub_b = _gen_ec_keypair()

    cred_a, _ = _enroll(user_headers, priv_a, pub_a, "-t06a")
    cred_b, _ = _enroll(user_headers, priv_b, pub_b, "-t06b")

    # Get nonce bound to credential A
    ch_resp = client.get("/api/mobile/challenge", params={"credential_id": cred_a})
    nonce_hex = ch_resp.json()["nonce"]

    # Sign with credential B's key, sending cred_b
    sig_b = _sign_request(priv_b, credential_id=cred_b, nonce_hex=nonce_hex, method="GET", canonical_path="/api/mobile/me")

    resp = client.get("/api/mobile/me", headers={
        "X-Mobile-Credential-Id": cred_b,
        "X-Mobile-Nonce": nonce_hex,
        "X-Mobile-Signature": sig_b,
    })
    # Server looks up nonce bound to cred_b -> not found -> 401
    assert resp.status_code in (401, 403)


# ===========================================================================
# 7. Expired nonce -> FAIL
# ===========================================================================

def test_07_expired_nonce_fail(user_headers):
    """Nonce past expires_at is rejected with 401."""
    priv, pub_pem = _gen_ec_keypair()
    credential_id, _ = _enroll(user_headers, priv, pub_pem, "-t07")

    ch_resp = client.get("/api/mobile/challenge", params={"credential_id": credential_id})
    nonce_hex = ch_resp.json()["nonce"]

    # Manually expire the challenge in the DB
    with mobile_manager._get_connection() as conn:
        conn.execute(
            "UPDATE mobile_challenges SET expires_at = '2020-01-01T00:00:00+00:00' WHERE nonce_hex = ?",
            (nonce_hex,),
        )
        conn.commit()

    sig = _sign_request(priv, credential_id, nonce_hex, "GET", "/api/mobile/me")
    resp = client.get("/api/mobile/me", headers={
        "X-Mobile-Credential-Id": credential_id,
        "X-Mobile-Nonce": nonce_hex,
        "X-Mobile-Signature": sig,
    })
    assert resp.status_code in (401, 403)
    assert "expired" in resp.json()["detail"].lower()


# ===========================================================================
# 8. Wrong private key -> FAIL
# ===========================================================================

def test_08_wrong_private_key_fail(user_headers):
    """Request signed with an arbitrary private key is rejected with 403."""
    priv_legit, pub_pem_legit = _gen_ec_keypair()
    priv_attacker, _ = _gen_ec_keypair()
    credential_id, _ = _enroll(user_headers, priv_legit, pub_pem_legit, "-t08")

    headers_attacker = _get_pop_headers(credential_id, priv_attacker, method="GET", canonical_path="/api/mobile/me")
    resp = client.get("/api/mobile/me", headers=headers_attacker)
    assert resp.status_code == 403
    assert "signature" in resp.json()["detail"].lower() or "proof" in resp.json()["detail"].lower()


# ===========================================================================
# 9. Missing signature -> FAIL
# ===========================================================================

def test_09_missing_signature_headers_fail():
    """Missing any PoP header returns 401."""
    resp1 = client.get("/api/mobile/me")
    assert resp1.status_code == 401

    resp2 = client.get("/api/mobile/me", headers={"X-Mobile-Credential-Id": "mcred_xyz"})
    assert resp2.status_code == 401

    resp3 = client.get("/api/mobile/me", headers={"X-Mobile-Credential-Id": "mcred_xyz", "X-Mobile-Nonce": "1234"})
    assert resp3.status_code == 401


# ===========================================================================
# 10. Atomic Race-Safety Double-Submit -> Exactly 1 PASS, 1 FAIL
# ===========================================================================

def test_10_atomic_race_condition_double_submit_safe(user_headers):
    """
    Two concurrent requests with the identical valid nonce and signature:
    atomic conditional update (WHERE used = 0) ensures exactly one succeeds (200)
    and the other receives 403 Replay detected.
    """
    priv, pub_pem = _gen_ec_keypair()
    credential_id, _ = _enroll(user_headers, priv, pub_pem, "-t10")

    headers = _get_pop_headers(credential_id, priv, method="GET", canonical_path="/api/mobile/me")

    def _send_req():
        return client.get("/api/mobile/me", headers=headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(_send_req)
        f2 = executor.submit(_send_req)
        r1 = f1.result()
        r2 = f2.result()

    statuses = sorted([r1.status_code, r2.status_code])
    assert statuses == [200, 403], f"Expected exactly one 200 and one 403, got {statuses}"


# ===========================================================================
# 11-16. Public Key Validation on Enrollment
# ===========================================================================

def test_11_public_key_secp256r1_pass(user_headers):
    """Standard EC SECP256R1 key is successfully accepted."""
    priv, pub_pem = _gen_ec_keypair()
    canonical = validate_and_canonicalize_public_key(pub_pem)
    assert "BEGIN PUBLIC KEY" in canonical
    assert "END PUBLIC KEY" in canonical


def test_12_public_key_rsa_rejected(user_headers):
    """RSA keys are rejected with ValueError."""
    rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_pem = rsa_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    with pytest.raises(ValueError, match="Only ECDSA EC public keys are supported"):
        validate_and_canonicalize_public_key(rsa_pem)

    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    code = gen_resp.json()["pairing_code"]
    resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": rsa_pem,
        "device_identifier": "dev-rsa",
    })
    assert resp.status_code == 400
    assert "only ecdsa" in resp.json()["detail"].lower()


def test_13_public_key_unsupported_curve_rejected(user_headers):
    """SECP384R1 or Ed25519 keys are rejected."""
    key_384 = ec.generate_private_key(ec.SECP384R1())
    pem_384 = key_384.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    with pytest.raises(ValueError, match="Only SECP256R1"):
        validate_and_canonicalize_public_key(pem_384)


def test_14_public_key_malformed_pem_rejected(user_headers):
    """Garbage / malformed PEM is rejected."""
    with pytest.raises(ValueError, match="Malformed or unparseable"):
        validate_and_canonicalize_public_key("-----BEGIN PUBLIC KEY-----\nNOT_VALID_BASE64\n-----END PUBLIC KEY-----")

    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    code = gen_resp.json()["pairing_code"]
    resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": "garbage-not-a-key",
        "device_identifier": "dev-garbage",
    })
    assert resp.status_code == 400


def test_15_public_key_private_key_material_rejected(user_headers):
    """Private key material is strictly rejected."""
    priv = ec.generate_private_key(ec.SECP256R1())
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    with pytest.raises(ValueError, match="Private key material is forbidden"):
        validate_and_canonicalize_public_key(priv_pem)

    gen_resp = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    code = gen_resp.json()["pairing_code"]
    resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": priv_pem,
        "device_identifier": "dev-priv-leak",
    })
    assert resp.status_code == 400
    assert "private key" in resp.json()["detail"].lower()


def test_16_public_key_oversized_payload_rejected(user_headers):
    """Payloads exceeding 4096 bytes are rejected."""
    oversized = "-----BEGIN PUBLIC KEY-----\n" + ("A" * 5000) + "\n-----END PUBLIC KEY-----"
    with pytest.raises(ValueError, match="too large"):
        validate_and_canonicalize_public_key(oversized)


# ===========================================================================
# 17. Re-enrollment Duplicate Device Semantics
# ===========================================================================

def test_17_re_enrollment_supersedes_old_credentials(user_headers):
    """
    When a device re-enrolls with a fresh keypair, its previous credentials
    are marked 'superseded' and cannot be used, while the new credential works.
    """
    priv1, pub_pem1 = _gen_ec_keypair()
    priv2, pub_pem2 = _gen_ec_keypair()

    dev_identifier = f"re-enroll-dev-{datetime.now().timestamp()}"

    # First enrollment
    gen1 = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    code1 = gen1.json()["pairing_code"]
    resp1 = client.post("/api/mobile/enroll", json={
        "pairing_code": code1,
        "public_key": pub_pem1,
        "device_identifier": dev_identifier,
        "device_name": "Device V1",
    })
    cred1 = resp1.json()["credential_id"]

    # Works with key 1
    h1 = _get_pop_headers(cred1, priv1, "GET", "/api/mobile/me")
    assert client.get("/api/mobile/me", headers=h1).status_code == 200

    # Pre-obtain valid PoP headers for cred1 BEFORE re-enrollment
    h1_pending = _get_pop_headers(cred1, priv1, "GET", "/api/mobile/me")

    # Second enrollment (same device_identifier, new key)
    gen2 = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    code2 = gen2.json()["pairing_code"]
    resp2 = client.post("/api/mobile/enroll", json={
        "pairing_code": code2,
        "public_key": pub_pem2,
        "device_identifier": dev_identifier,
        "device_name": "Device V2",
    })
    cred2 = resp2.json()["credential_id"]

    # Key 2 works
    h2 = _get_pop_headers(cred2, priv2, "GET", "/api/mobile/me")
    assert client.get("/api/mobile/me", headers=h2).status_code == 200

    # Old credential 1 was superseded:
    # 1) In-flight request fails at PoP verification with 403
    resp_superseded = client.get("/api/mobile/me", headers=h1_pending)
    assert resp_superseded.status_code == 403

    # 2) New challenge request for old credential is also rejected with 403
    ch_resp = client.get("/api/mobile/challenge", params={"credential_id": cred1})
    assert ch_resp.status_code == 403
    assert "not active" in ch_resp.json()["detail"].lower()


# ===========================================================================
# 18. Parent Revoked -> FAIL
# ===========================================================================

def test_18_parent_revocation_blocks_access():
    cert = auth_manager.create_user_certificate(f"R3 Revoke Parent {datetime.now().timestamp()}")
    headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": cert["serial_hex"],
        "x-client-cert-fingerprint": cert["fingerprint_sha256"],
    }
    priv, pub_pem = _gen_ec_keypair()
    cred_id, _ = _enroll(headers, priv, pub_pem, "-t18")

    # Works before revoke
    h = _get_pop_headers(cred_id, priv, "GET", "/api/mobile/me")
    assert client.get("/api/mobile/me", headers=h).status_code == 200

    # Revoke parent
    auth_manager.revoke_certificate(cert["id"])

    # Fails after revoke
    h_after = _get_pop_headers(cred_id, priv, "GET", "/api/mobile/me")
    resp_after = client.get("/api/mobile/me", headers=h_after)
    assert resp_after.status_code == 403
    assert "parent" in resp_after.json()["detail"].lower()


# ===========================================================================
# 19. Device Revoked -> FAIL
# ===========================================================================

def test_19_device_revocation_blocks_access(owner_headers):
    priv, pub_pem = _gen_ec_keypair()
    gen = client.post("/admin-api/mobile/pairing/generate", headers=owner_headers)
    code = gen.json()["pairing_code"]
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_pem,
        "device_identifier": f"t19-dev-{datetime.now().timestamp()}",
    })
    cred_id = enroll_resp.json()["credential_id"]
    dev_id = enroll_resp.json()["device_id"]

    # Works before revoke
    h = _get_pop_headers(cred_id, priv, "GET", "/api/mobile/me")
    assert client.get("/api/mobile/me", headers=h).status_code == 200

    # Pre-obtain headers with challenge before revoke
    h_pending = _get_pop_headers(cred_id, priv, "GET", "/api/mobile/me")

    # Revoke device
    rev_resp = client.post(f"/admin-api/mobile/devices/{dev_id}/revoke", headers=owner_headers)
    assert rev_resp.status_code == 200

    # Fails after revoke: in-flight request fails with 403
    resp_after = client.get("/api/mobile/me", headers=h_pending)
    assert resp_after.status_code == 403
    assert "revoked" in resp_after.json()["detail"].lower()

    # New challenge request also rejected with 403
    ch_resp = client.get("/api/mobile/challenge", params={"credential_id": cred_id})
    assert ch_resp.status_code == 403


# ===========================================================================
# 20. USER Cannot Escalate to OWNER
# ===========================================================================

def test_20_user_cannot_escalate_to_owner(user_headers):
    priv, pub_pem = _gen_ec_keypair()
    gen = client.post("/admin-api/mobile/pairing/generate", headers=user_headers)
    code = gen.json()["pairing_code"]
    enroll_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": code,
        "public_key": pub_pem,
        "device_identifier": f"t20-user-{datetime.now().timestamp()}",
        "role": "OWNER",  # Attempt spoofing role in payload
    })
    cred_id = enroll_resp.json()["credential_id"]
    assert enroll_resp.json()["effective_role"] == "USER"
    assert enroll_resp.json()["is_owner"] is False

    # Attempt to access owner-only endpoint
    h = _get_pop_headers(cred_id, priv, "GET", "/api/mobile/owner-only")
    resp = client.get("/api/mobile/owner-only", headers=h)
    assert resp.status_code == 403
    assert "Owner permissions required" in resp.json()["detail"]


# ===========================================================================
# 21. Query Parameter Alteration Invalidates Signature -> FAIL
# ===========================================================================

def test_21_query_parameter_alteration_invalidates_signature(user_headers):
    """
    If query parameters are present, altering them changes the canonical path
    and invalidates the PoP signature.
    """
    priv, pub_pem = _gen_ec_keypair()
    credential_id, _ = _enroll(user_headers, priv, pub_pem, "-t21")

    # Sign for /api/mobile/status?filter=all
    h = _get_pop_headers(credential_id, priv, method="GET", canonical_path="/api/mobile/status?filter=all")

    # Tamper query to filter=admin
    resp = client.get("/api/mobile/status?filter=admin", headers=h)
    assert resp.status_code == 403
    assert "signature" in resp.json()["detail"].lower() or "proof of possession" in resp.json()["detail"].lower()


# ===========================================================================
# 22. SQLite Integrity PRAGMAs
# ===========================================================================

def test_22_sqlite_pragmas():
    with mobile_manager._get_connection() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_key_check;")
        fk = cur.fetchall()
        assert fk == [], f"Foreign key check failed: {fk}"

        cur.execute("PRAGMA quick_check;")
        qc = [tuple(r) for r in cur.fetchall()]
        assert qc == [("ok",)], f"Quick check failed: {qc}"
