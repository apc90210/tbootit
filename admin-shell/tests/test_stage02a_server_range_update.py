"""
Stage02A Server Range & Resumable APK Update Tests.

Validates:
1. full APK -> 200
2. Accept-Ranges present
3. valid Range -> 206
4. correct Content-Range
5. correct returned bytes
6. resume from middle
7. last-byte range
8. invalid range -> 416
9. malformed range safe
10. unauthenticated range denied
11. revoked device denied
12. revoked parent denied
13. wrong version denied
14. path traversal impossible
15. ETag stable for same APK
16. changed APK changes ETag
17. If-Range match -> 206
18. If-Range mismatch -> safe full/restart
19. previous update tests remain PASS
"""

import os
import sys
import json
import hashlib
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

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
def enrolled_device():
    user_cert = auth_manager.create_user_certificate(f"Stage02A Device {datetime.now(timezone.utc).timestamp()}")
    headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": user_cert["serial_hex"],
        "x-client-cert-fingerprint": user_cert["fingerprint_sha256"],
    }
    p_resp = client.post("/admin-api/mobile/pairing/generate", headers=headers)
    assert p_resp.status_code == 200
    pairing_code = p_resp.json()["pairing_code"]

    priv, pub_pem = _gen_android_keypair()
    device_id = f"test_device_{datetime.now(timezone.utc).timestamp()}"
    e_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": pairing_code,
        "public_key": pub_pem,
        "device_identifier": device_id,
        "device_name": "Test Samsung S22 Ultra",
    })
    assert e_resp.status_code == 200, e_resp.text
    return {
        "credential_id": e_resp.json()["credential_id"],
        "device_id": e_resp.json()["device_id"],
        "priv_key": priv,
        "cert": user_cert,
        "device_identifier": device_id,
    }



@pytest.fixture
def staged_release(tmp_path, monkeypatch):
    release_dir = tmp_path / "mobile_releases"
    release_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MOBILE_APP_RELEASE_DIR", str(release_dir))

    # Synthetic binary APK payload of 100,000 bytes
    apk_content = bytes([(i * 31 + 17) % 256 for i in range(100000)])
    apk_file = release_dir / "app-release-v2.apk"
    apk_file.write_bytes(apk_content)
    apk_sha256 = hashlib.sha256(apk_content).hexdigest()

    manifest_data = {
        "application_id": "com.technoreboot.mobile",
        "version_code": 2,
        "version_name": "1.0.1",
        "min_sdk": 26,
        "apk_filename": "app-release-v2.apk",
        "apk_size": len(apk_content),
        "sha256": apk_sha256,
        "signing_cert_sha256": "741ffd5582e3ab46aee12a746a3aae7454fcaa79553b9702102bf3a4ec47bcd1",
        "release_notes": "Stage02A Resumable update test",
        "mandatory": False,
    }
    manifest_file = release_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    return {
        "dir": release_dir,
        "apk_file": apk_file,
        "apk_content": apk_content,
        "apk_sha256": apk_sha256,
        "manifest": manifest_data,
        "size": len(apk_content),
    }


def test_01_full_apk_returns_200(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    headers = _get_pop_headers(cred_id, priv, "GET", path)
    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    assert resp.content == staged_release["apk_content"]
    assert resp.headers["content-length"] == str(staged_release["size"])
    assert resp.headers.get("accept-ranges") == "bytes"
    assert resp.headers.get("etag") == f'"{staged_release["apk_sha256"]}"'


def test_02_accept_ranges_header_present(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    headers = _get_pop_headers(cred_id, priv, "GET", path)
    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    assert "accept-ranges" in resp.headers
    assert resp.headers["accept-ranges"].lower() == "bytes"


def test_03_valid_range_returns_206(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    headers = _get_pop_headers(cred_id, priv, "GET", path)
    headers["Range"] = "bytes=0-499"
    resp = client.get(path, headers=headers)
    assert resp.status_code == 206
    assert resp.headers["content-length"] == "500"
    assert resp.headers["content-range"] == f"bytes 0-499/{staged_release['size']}"
    assert resp.content == staged_release["apk_content"][:500]


def test_04_correct_content_range_header(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    headers = _get_pop_headers(cred_id, priv, "GET", path)
    headers["Range"] = "bytes=1000-4999"
    resp = client.get(path, headers=headers)
    assert resp.status_code == 206
    assert resp.headers["content-range"] == f"bytes 1000-4999/{staged_release['size']}"
    assert resp.headers["content-length"] == "4000"


def test_05_correct_returned_bytes_slice(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    headers = _get_pop_headers(cred_id, priv, "GET", path)
    headers["Range"] = "bytes=10000-19999"
    resp = client.get(path, headers=headers)
    assert resp.status_code == 206
    expected_slice = staged_release["apk_content"][10000:20000]
    assert resp.content == expected_slice


def test_06_resume_from_middle(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    # Simulated resume from 45,000 bytes already downloaded
    headers = _get_pop_headers(cred_id, priv, "GET", path)
    headers["Range"] = "bytes=45000-"
    resp = client.get(path, headers=headers)
    assert resp.status_code == 206
    expected_content = staged_release["apk_content"][45000:]
    assert resp.content == expected_content
    assert resp.headers["content-range"] == f"bytes 45000-{staged_release['size'] - 1}/{staged_release['size']}"
    assert resp.headers["content-length"] == str(len(expected_content))


def test_07_last_byte_and_suffix_range(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    # Explicit last byte
    last_idx = staged_release["size"] - 1
    headers = _get_pop_headers(cred_id, priv, "GET", path)
    headers["Range"] = f"bytes={last_idx}-{last_idx}"
    resp = client.get(path, headers=headers)
    assert resp.status_code == 206
    assert resp.headers["content-length"] == "1"
    assert resp.headers["content-range"] == f"bytes {last_idx}-{last_idx}/{staged_release['size']}"
    assert resp.content == staged_release["apk_content"][-1:]

    # Suffix range: last 100 bytes (bytes=-100)
    headers2 = _get_pop_headers(cred_id, priv, "GET", path)
    headers2["Range"] = "bytes=-100"
    resp2 = client.get(path, headers=headers2)
    assert resp2.status_code == 206
    assert resp2.headers["content-length"] == "100"
    assert resp2.headers["content-range"] == f"bytes {staged_release['size'] - 100}-{last_idx}/{staged_release['size']}"
    assert resp2.content == staged_release["apk_content"][-100:]


def test_08_invalid_range_returns_416(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    # Beyond EOF
    headers = _get_pop_headers(cred_id, priv, "GET", path)
    headers["Range"] = f"bytes={staged_release['size'] + 5000}-"
    resp = client.get(path, headers=headers)
    assert resp.status_code == 416
    assert resp.headers["content-range"] == f"bytes */{staged_release['size']}"

    # Inverted range
    headers2 = _get_pop_headers(cred_id, priv, "GET", path)
    headers2["Range"] = "bytes=5000-1000"
    resp2 = client.get(path, headers=headers2)
    assert resp2.status_code == 416
    assert resp2.headers["content-range"] == f"bytes */{staged_release['size']}"


def test_09_malformed_range_handled_safely(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    malformed_examples = [
        "not_bytes=100-200",
        "bytes=abc-def",
        "bytes=-",
        "bytes=---",
        "bytes=10-20,30-40",
    ]
    for bad_range in malformed_examples:
        headers = _get_pop_headers(cred_id, priv, "GET", path)
        headers["Range"] = bad_range
        resp = client.get(path, headers=headers)
        assert resp.status_code == 416
        assert resp.headers["content-range"] == f"bytes */{staged_release['size']}"


def test_10_unauthenticated_range_denied(staged_release):
    path = "/api/mobile/app/update/apk?version_code=2"
    resp = client.get(path, headers={"Range": "bytes=0-500"})
    assert resp.status_code == 401
    assert "Mobile PoP auth required" in resp.json()["detail"]


def test_11_revoked_device_denied_range(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    device_id = enrolled_device["device_id"]
    parent_id = enrolled_device["cert"]["id"]
    path = "/api/mobile/app/update/apk?version_code=2"

    headers = _get_pop_headers(cred_id, priv, "GET", path)
    headers["Range"] = "bytes=0-500"

    mobile_manager.revoke_device(device_id=device_id, actor_cert_id=parent_id, is_owner=False)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 403
    assert "revoked" in resp.json()["detail"].lower() or "отозван" in resp.json()["detail"].lower()



def test_12_revoked_parent_denied_range(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    parent_cert_id = enrolled_device["cert"]["id"]
    path = "/api/mobile/app/update/apk?version_code=2"

    auth_manager.revoke_certificate(parent_cert_id)

    headers = _get_pop_headers(cred_id, priv, "GET", path)
    headers["Range"] = "bytes=0-500"
    resp = client.get(path, headers=headers)
    assert resp.status_code == 403
    assert "revoked" in resp.json()["detail"].lower() or "parent certificate" in resp.json()["detail"].lower()



def test_13_wrong_version_denied(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=999"

    headers = _get_pop_headers(cred_id, priv, "GET", path)
    headers["Range"] = "bytes=0-500"
    resp = client.get(path, headers=headers)
    assert resp.status_code == 404
    assert "не совпадает с актуальным релизом" in resp.json()["detail"]


def test_14_arbitrary_path_traversal_impossible(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=../../etc/passwd"

    headers = {
        "X-Mobile-Credential-Id": cred_id,
        "X-Mobile-Nonce": "fake",
        "X-Mobile-Signature": "fake",
        "Range": "bytes=0-100",
    }
    resp = client.get(path, headers=headers)
    # FastAPI schema validation catches non-integer Query(...)
    assert resp.status_code == 422


def test_15_etag_stable_for_same_apk(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    headers1 = _get_pop_headers(cred_id, priv, "GET", path)
    resp1 = client.get(path, headers=headers1)
    etag1 = resp1.headers.get("etag")

    headers2 = _get_pop_headers(cred_id, priv, "GET", path)
    headers2["Range"] = "bytes=0-100"
    resp2 = client.get(path, headers=headers2)
    etag2 = resp2.headers.get("etag")

    assert etag1 is not None
    assert etag1 == etag2
    assert etag1 == f'"{staged_release["apk_sha256"]}"'


def test_16_changed_apk_changes_etag(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    headers1 = _get_pop_headers(cred_id, priv, "GET", path)
    resp1 = client.get(path, headers=headers1)
    original_etag = resp1.headers["etag"]

    # Modify the APK on disk and update manifest
    new_apk_content = staged_release["apk_content"] + b"EXTRA_BYTES"
    staged_release["apk_file"].write_bytes(new_apk_content)
    new_sha = hashlib.sha256(new_apk_content).hexdigest()
    staged_release["manifest"]["sha256"] = new_sha
    staged_release["manifest"]["apk_size"] = len(new_apk_content)
    (staged_release["dir"] / "manifest.json").write_text(json.dumps(staged_release["manifest"]), encoding="utf-8")

    headers2 = _get_pop_headers(cred_id, priv, "GET", path)
    resp2 = client.get(path, headers=headers2)
    new_etag = resp2.headers["etag"]

    assert original_etag != new_etag
    assert new_etag == f'"{new_sha}"'


def test_17_if_range_match_returns_206(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    etag = f'"{staged_release["apk_sha256"]}"'
    headers = _get_pop_headers(cred_id, priv, "GET", path)
    headers["Range"] = "bytes=0-499"
    headers["If-Range"] = etag

    resp = client.get(path, headers=headers)
    assert resp.status_code == 206
    assert resp.headers["content-length"] == "500"
    assert resp.headers["content-range"] == f"bytes 0-499/{staged_release['size']}"
    assert resp.content == staged_release["apk_content"][:500]


def test_18_if_range_mismatch_safely_returns_200_full(enrolled_device, staged_release):
    cred_id = enrolled_device["credential_id"]
    priv = enrolled_device["priv_key"]
    path = "/api/mobile/app/update/apk?version_code=2"

    stale_etag = '"0000000000000000000000000000000000000000000000000000000000000000"'
    headers = _get_pop_headers(cred_id, priv, "GET", path)
    headers["Range"] = "bytes=1000-2000"
    headers["If-Range"] = stale_etag

    # Per RFC 7233 Section 3.2: If the representation has changed, the server sends 200 (OK) with full representation.
    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-length"] == str(staged_release["size"])
    assert resp.content == staged_release["apk_content"]
