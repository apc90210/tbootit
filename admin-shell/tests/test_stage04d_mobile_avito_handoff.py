"""
Stage 04D - Mobile Avito Handoff Admin-Shell Tests.
Verifies Section 12 items (8-11) and mobile gateway contract:
- 1. OWNER can fetch handoff data (200 OK);
- 2. USER can fetch handoff data (200 OK);
- 3. Unauthenticated mobile request denied (401);
- 4. Missing PoP denied (401);
- 5. Revoked device denied (403);
- 6. Revoked parent denied (403);
- 7. Tampered sale path denied (signature verification failure);
- 8. Unknown sale (Core 404) forwarded as 404;
- 9. Core error handling (502/504).
"""

import sys
import os
import json
import base64
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
admin_shell_dir = os.path.join(project_root, "admin-shell")

for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        sys.modules.pop(k, None)

while admin_shell_dir in sys.path:
    sys.path.remove(admin_shell_dir)
sys.path.insert(0, admin_shell_dir)

import app.main as admin_main
from app.main import app, auth_manager, mobile_manager, CORE_API_URL
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


def _enroll_device(parent_cert_id: str, dev_id_str: str, dev_name: str):
    priv, pub_pem = _gen_android_keypair()
    res = mobile_manager.generate_pairing_code(parent_certificate_id=parent_cert_id, device_name=dev_name)
    code = res["pairing_code"]
    enroll_res = mobile_manager.enroll_device(
        pairing_code=code,
        public_key=pub_pem,
        device_identifier=dev_id_str,
        device_name=dev_name,
    )
    cred_id = enroll_res["credential_id"]
    return priv, cred_id, enroll_res


MOCK_HANDOFF_DATA = {
    "sale_id": 12,
    "items": [
        {
            "product_id": 229,
            "title": "МФУ HP LaserJet 3055",
            "remaining_stock": 0,
            "needs_manual_avito_removal": True,
            "listing_id": "7641905231",
            "listing_url": "https://www.avito.ru/ekaterinburg/orgtehnika_i_rashodniki/lazernoe_mfu_hp_laserjet_3055_garantiya_7641905231"
        }
    ]
}


def test_01_owner_can_fetch_handoff_data():
    """Section 12.8: OWNER can retrieve handoff data per normal mobile access."""
    priv, cred_id, _ = _enroll_device("owner", "test_owner_avito_dev_01", "Owner Galaxy S22")
    path = "/api/mobile/sales/12/avito-handoff"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_HANDOFF_DATA
        mock_get.return_value = mock_resp

        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        assert resp.json() == MOCK_HANDOFF_DATA


def test_02_user_can_fetch_handoff_data():
    """Section 12.8: USER can retrieve handoff data per normal mobile access."""
    users = [c for c in auth_manager.list_certificates() if not c.get("is_owner") and c.get("status") == "ACTIVE"]
    assert len(users) > 0, "At least one active USER certificate expected"
    user_cert = users[0]
    priv, cred_id, _ = _enroll_device(user_cert["id"], "test_user_avito_dev_02", "Staff Phone")

    path = "/api/mobile/sales/12/avito-handoff"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_HANDOFF_DATA
        mock_get.return_value = mock_resp

        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        assert resp.json() == MOCK_HANDOFF_DATA


def test_03_unauthenticated_request_denied():
    """Section 12.8: Missing auth headers denied."""
    resp = client.get("/api/mobile/sales/12/avito-handoff")
    assert resp.status_code in (401, 403)


def test_04_missing_pop_header_denied():
    """Section 12.8: Missing PoP header denied (missing nonce and signature)."""
    priv, cred_id, _ = _enroll_device("owner", "test_owner_avito_dev_04", "Owner Galaxy S22")
    resp = client.get(
        "/api/mobile/sales/12/avito-handoff",
        headers={"X-Mobile-Credential-Id": cred_id},
    )
    assert resp.status_code in (401, 403)


def test_05_revoked_device_denied():
    """Section 12.9: Revoked device denied."""
    priv, cred_id, enroll_res = _enroll_device("owner", "test_revoked_avito_dev_05", "Revoked Phone")
    dev_id = enroll_res["device_id"]

    path = "/api/mobile/sales/12/avito-handoff"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    mobile_manager.revoke_device(device_id=dev_id, actor_cert_id="owner", is_owner=True)

    resp = client.get(path, headers=headers)
    assert resp.status_code in (401, 403)


def test_06_revoked_parent_cert_denied():
    """Section 12.10: Revoked parent certificate denied."""
    users = [c for c in auth_manager.list_certificates() if not c.get("is_owner") and c.get("status") == "ACTIVE"]
    assert len(users) > 0
    parent_cert = users[0]
    priv, cred_id, _ = _enroll_device(parent_cert["id"], "test_parent_rev_avito_dev_06", "Seller Phone")

    path = "/api/mobile/sales/12/avito-handoff"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch.object(auth_manager, "get_certificate") as mock_cert:
        mock_cert.return_value = {"id": parent_cert["id"], "status": "REVOKED"}
        resp = client.get(path, headers=headers)
        assert resp.status_code in (401, 403)


def test_07_tampered_sale_path_denied():
    """Section 12.11: Tampered sale_id denied (path tampering invalidates PoP signature)."""
    priv, cred_id, _ = _enroll_device("owner", "test_tampered_avito_dev_07", "Tamper Phone")
    signed_path = "/api/mobile/sales/12/avito-handoff"
    headers = _get_pop_headers(cred_id, priv, "GET", signed_path)

    # Attack: send request to sale 99 instead of signed sale 12
    tampered_path = "/api/mobile/sales/99/avito-handoff"
    resp = client.get(tampered_path, headers=headers)
    assert resp.status_code in (401, 403)


def test_08_core_404_forwarding():
    """Section 12.7: Unknown sale from Core forwarded as 404."""
    priv, cred_id, _ = _enroll_device("owner", "test_core_404_avito_dev_08", "Owner Galaxy S22")
    path = "/api/mobile/sales/99999/avito-handoff"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        resp = client.get(path, headers=headers)
        assert resp.status_code == 404


def test_09_core_error_forwarding():
    """Core upstream errors handled cleanly (502 / 504)."""
    priv, cred_id, _ = _enroll_device("owner", "test_core_err_avito_dev_09", "Owner Galaxy S22")
    path = "/api/mobile/sales/12/avito-handoff"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Core timeout")

        resp = client.get(path, headers=headers)
        assert resp.status_code == 504
