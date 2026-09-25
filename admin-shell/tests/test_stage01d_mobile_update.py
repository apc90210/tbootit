"""
Stage01D — Mobile In-App Update API Server Tests.
Verifies all 13 server-side update requirements:
1. Active USER manifest access PASS
2. Active OWNER manifest access PASS
3. Missing PoP DENY (401)
4. Revoked parent DENY (403)
5. Revoked device DENY (403)
6. Manifest version metadata valid
7. Manifest SHA-256 matches actual APK
8. Missing APK -> controlled failure (404/503)
9. APK endpoint streams correct bytes
10. Arbitrary path traversal impossible
11. Request for non-advertised version rejected
12. No arbitrary external download URL
13. Core/report functionality unaffected
"""

import sys
import os
import json
import hashlib
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# Ensure admin-shell is loaded as 'app'
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
admin_shell_dir = os.path.join(project_root, "admin-shell")

for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        sys.modules.pop(k, None)

if admin_shell_dir not in sys.path:
    sys.path.insert(0, admin_shell_dir)

from app.main import app, auth_manager, mobile_manager
from app.mobile_manager import build_canonical_signing_payload, compute_body_sha256

client = TestClient(app)


def _gen_android_keypair():
    priv = ec.generate_private_key(ec.SECP256R1())
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return priv, pub_pem


def _sign_payload(priv, payload_bytes: bytes) -> str:
    from cryptography.hazmat.primitives import hashes
    import base64
    der = priv.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(der).decode("ascii")


def _get_pop_headers(credential_id: str, priv, method: str, canonical_path: str, body: bytes = b"") -> dict:
    ch = client.get("/api/mobile/challenge", params={"credential_id": credential_id})
    assert ch.status_code == 200, ch.text
    nonce = ch.json()["nonce"]
    payload_bytes = build_canonical_signing_payload(
        credential_id=credential_id,
        nonce_hex=nonce,
        method=method,
        canonical_path=canonical_path,
        body_sha256=compute_body_sha256(body),
    )
    sig_b64 = _sign_payload(priv, payload_bytes)
    return {
        "X-Mobile-Credential-Id": credential_id,
        "X-Mobile-Nonce": nonce,
        "X-Mobile-Signature": sig_b64,
    }


@pytest.fixture
def enrolled_user():
    user_cert = auth_manager.create_user_certificate(f"Stage01D User {datetime.now(timezone.utc).timestamp()}")
    headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": user_cert["serial_hex"],
        "x-client-cert-fingerprint": user_cert["fingerprint_sha256"],
    }
    p_resp = client.post("/admin-api/mobile/pairing/generate", headers=headers)
    assert p_resp.status_code == 200
    pairing_code = p_resp.json()["pairing_code"]

    priv, pub_pem = _gen_android_keypair()
    dev_id = f"tr_dev_user_01d_{datetime.now(timezone.utc).timestamp()}"
    e_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": pairing_code,
        "public_key": pub_pem,
        "device_identifier": dev_id,
        "device_name": "User Phone",
    })
    assert e_resp.status_code == 200
    return {
        "cert": user_cert,
        "credential_id": e_resp.json()["credential_id"],
        "device_id": e_resp.json()["device_id"],
        "priv_key": priv,
        "pub_pem": pub_pem,
    }


@pytest.fixture
def enrolled_owner():
    owner_cert = auth_manager.get_certificate("owner")
    headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }
    p_resp = client.post("/admin-api/mobile/pairing/generate", headers=headers)
    assert p_resp.status_code == 200
    pairing_code = p_resp.json()["pairing_code"]

    priv, pub_pem = _gen_android_keypair()
    dev_id = f"tr_dev_owner_01d_{datetime.now(timezone.utc).timestamp()}"
    e_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": pairing_code,
        "public_key": pub_pem,
        "device_identifier": dev_id,
        "device_name": "Owner Tablet",
    })
    assert e_resp.status_code == 200
    return {
        "cert": owner_cert,
        "credential_id": e_resp.json()["credential_id"],
        "device_id": e_resp.json()["device_id"],
        "priv_key": priv,
        "pub_pem": pub_pem,
    }


@pytest.fixture
def release_fixture(tmp_path, monkeypatch):
    """Sets up a valid mock release directory with manifest.json and APK file."""
    rel_dir = tmp_path / "mobile_releases"
    rel_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.main.MOBILE_APP_RELEASE_DIR", str(rel_dir))

    apk_content = b"PK\x03\x04\x14\x00MockTechnorebootApkBinaryDataV2Package"
    apk_sha = hashlib.sha256(apk_content).hexdigest().lower()
    apk_file = rel_dir / "app-v2.apk"
    apk_file.write_bytes(apk_content)

    manifest_data = {
        "application_id": "com.technoreboot.mobile",
        "version_code": 2,
        "version_name": "1.0.1",
        "min_sdk": 26,
        "apk_size": len(apk_content),
        "sha256": apk_sha,
        "signing_cert_sha256": "4b68e923e4d588c83b8a1ec56291a27df37119ff94a2fa423d2400f012345678",
        "release_notes": "Stage01D in-app update support",
        "mandatory": False,
        "apk_filename": "app-v2.apk",
    }
    manifest_file = rel_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")

    return {
        "dir": rel_dir,
        "apk_file": apk_file,
        "apk_bytes": apk_content,
        "apk_sha": apk_sha,
        "manifest": manifest_data,
    }


# ===========================================================================
# 1-2. USER and OWNER Manifest Access PASS
# ===========================================================================

def test_01_active_user_manifest_access_pass(enrolled_user, release_fixture):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/app/update/manifest"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["application_id"] == "com.technoreboot.mobile"
    assert data["version_code"] == 2
    assert data["version_name"] == "1.0.1"
    assert data["sha256"] == release_fixture["apk_sha"]


def test_02_active_owner_manifest_access_pass(enrolled_owner, release_fixture):
    cred_id = enrolled_owner["credential_id"]
    priv = enrolled_owner["priv_key"]
    path = "/api/mobile/app/update/manifest"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["version_code"] == 2
    assert data["version_name"] == "1.0.1"


# ===========================================================================
# 3. Missing PoP DENY (401)
# ===========================================================================

def test_03_missing_pop_denied(release_fixture):
    resp = client.get("/api/mobile/app/update/manifest")
    assert resp.status_code == 401
    assert "Mobile PoP auth required" in resp.json()["detail"]

    apk_resp = client.get("/api/mobile/app/update/apk?version_code=2")
    assert apk_resp.status_code == 401
    assert "Mobile PoP auth required" in apk_resp.json()["detail"]


# ===========================================================================
# 4. Revoked Parent DENY (403)
# ===========================================================================

def test_04_revoked_parent_denied(enrolled_user, release_fixture):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    parent_cert_id = enrolled_user["cert"]["id"]

    auth_manager.revoke_certificate(parent_cert_id)

    path = "/api/mobile/app/update/manifest"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 403
    assert "revoked" in resp.json()["detail"].lower() or "родительский" in resp.json()["detail"].lower()


# ===========================================================================
# 5. Revoked Device DENY (403)
# ===========================================================================

def test_05_revoked_device_denied(enrolled_user, release_fixture):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    dev_id = enrolled_user["device_id"]
    parent_id = enrolled_user["cert"]["id"]

    path = "/api/mobile/app/update/manifest"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    mobile_manager.revoke_device(device_id=dev_id, actor_cert_id=parent_id, is_owner=False)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 403
    assert "revoked" in resp.json()["detail"].lower() or "отозван" in resp.json()["detail"].lower()


# ===========================================================================
# 6. Manifest Version Metadata Valid
# ===========================================================================

def test_06_manifest_version_metadata_valid(enrolled_user, release_fixture):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/app/update/manifest"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert isinstance(data["version_code"], int)
    assert data["version_code"] > 0
    assert isinstance(data["version_name"], str)
    assert len(data["version_name"]) > 0
    assert data["min_sdk"] == 26
    assert data["apk_size"] == len(release_fixture["apk_bytes"])
    assert len(data["sha256"]) == 64


# ===========================================================================
# 7. Manifest SHA-256 Matches Actual APK
# ===========================================================================

def test_07_manifest_sha256_matches_actual_apk(enrolled_user, release_fixture):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/app/update/manifest"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    manifest_sha = resp.json()["sha256"]

    actual_file_sha = hashlib.sha256(release_fixture["apk_file"].read_bytes()).hexdigest().lower()
    assert manifest_sha == actual_file_sha


# ===========================================================================
# 8. Missing APK -> Controlled Failure (404/503)
# ===========================================================================

def test_08_missing_apk_controlled_failure(enrolled_user, release_fixture):
    # Remove the APK file while leaving manifest intact
    release_fixture["apk_file"].unlink()

    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/app/update/manifest"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    # Server must not advertise broken release
    resp = client.get(path, headers=headers)
    assert resp.status_code in (404, 503)
    assert "не найден" in resp.json()["detail"].lower() or "missing" in resp.json()["detail"].lower()


# ===========================================================================
# 9. APK Endpoint Streams Correct Bytes
# ===========================================================================

def test_09_apk_endpoint_streams_correct_bytes(enrolled_user, release_fixture):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.android.package-archive"
    assert resp.content == release_fixture["apk_bytes"]

    # Verify SHA-256 of downloaded body
    downloaded_sha = hashlib.sha256(resp.content).hexdigest().lower()
    assert downloaded_sha == release_fixture["apk_sha"]


# ===========================================================================
# 10. Arbitrary Path Traversal Impossible
# ===========================================================================

def test_10_arbitrary_path_traversal_impossible(enrolled_user, release_fixture):
    # Try modifying manifest to contain path traversal in apk_filename
    manifest_path = release_fixture["dir"] / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["apk_filename"] = "../../etc/passwd"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/app/update/manifest"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code in (403, 503)
    assert "недопустимое" in resp.json()["detail"].lower() or "traversal" in resp.json()["detail"].lower()


# ===========================================================================
# 11. Request for Non-Advertised Version Rejected
# ===========================================================================

def test_11_request_for_non_advertised_version_rejected(enrolled_user, release_fixture):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    # Requesting version 999 while version 2 is advertised
    path = "/api/mobile/app/update/apk?version_code=999"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 404
    assert "999" in resp.json()["detail"]


# ===========================================================================
# 12. No Arbitrary External Download URL
# ===========================================================================

def test_12_no_arbitrary_external_download_url(enrolled_user, release_fixture):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/app/update/manifest"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Manifest MUST NOT contain external download URLs (prevent arbitrary URL redirect)
    assert "download_url" not in data
    assert "url" not in data
    assert "apk_url" not in data


# ===========================================================================
# 13. Core / Report Functionality Unaffected
# ===========================================================================

def test_13_core_report_functionality_unaffected(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/reports/sales?period=today"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "today"
    assert "revenue_total" in data
    assert "sales" in data
