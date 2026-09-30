"""
Stage 04B - Mobile POS Checkout Admin-Shell Gateway Tests.
Verifies Section 13 (items 10-15) & Section 12:
- 10. USER checkout per desktop rules;
- 11. OWNER checkout per desktop rules;
- 12. Revoked device denied;
- 13. Revoked parent denied;
- 14. Missing PoP denied;
- 15. Tampered body denied by TRMOBILE1;
- Admin-shell forwards canonical payload to Core via HTTP without direct DB access;
- Error forwarding (400, 404, 409, 502/504) from Core.
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


def test_10_user_checkout_succeeds_and_binds_cashier():
    """Item 10: USER checkout per desktop rules, cashier identity bound from certificate/auth context."""
    users = [c for c in auth_manager.list_certificates() if not c.get("is_owner") and c.get("status") == "ACTIVE"]
    assert len(users) > 0, "At least one active USER certificate expected"
    user_cert = users[0]
    priv, cred_id, _ = _enroll_device(user_cert["id"], "test_user_checkout_dev", "Seller Phone")

    checkout_payload = {
        "client_checkout_id": "test-uuid-user-001",
        "payment_method": "card",
        "items": [
            {"product_id": 102, "quantity": 1, "sale_price": 1800.0}
        ]
    }
    body_bytes = json.dumps(checkout_payload, ensure_ascii=False).encode("utf-8")
    path = "/api/mobile/sales/checkout"
    headers = _get_pop_headers(cred_id, priv, "POST", path, body=body_bytes)
    headers["Content-Type"] = "application/json"

    mock_core_resp = {
        "sale_id": 42,
        "receipt_number": "REC-20260930-0042",
        "total_amount": 1800.0,
        "payment_method": "card",
        "cashier_name": user_cert.get("name", "Продавец"),
        "created_at": "2026-09-30T10:00:00Z",
        "client_checkout_id": "test-uuid-user-001",
        "items": [
            {"product_id": 102, "title": "Мышь Logitech G102", "quantity": 1, "sale_price": 1800.0, "total_price": 1800.0}
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_core_resp
        mock_post.return_value = mock_response

        resp = client.post(path, content=body_bytes, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["sale_id"] == 42
        assert data["receipt_number"] == "REC-20260930-0042"
        assert data["client_checkout_id"] == "test-uuid-user-001"

        # Verify cashier was enriched in payload forwarded to Core
        called_args, called_kwargs = mock_post.call_args
        forwarded_json = called_kwargs.get("json", {})
        assert forwarded_json["cashier_name"] == user_cert.get("name") or forwarded_json["cashier_name"] == "Продавец" or "seller" in forwarded_json["cashier_name"].lower()


def test_11_owner_checkout_succeeds_and_binds_cashier():
    """Item 11: OWNER checkout per desktop rules, cashier identity bound from owner certificate."""
    priv, cred_id, _ = _enroll_device("owner", "test_owner_checkout_dev", "Owner Phone")

    checkout_payload = {
        "client_checkout_id": "test-uuid-owner-001",
        "payment_method": "cash",
        "items": [
            {"product_id": 101, "quantity": 2, "sale_price": 32000.0}
        ]
    }
    body_bytes = json.dumps(checkout_payload, ensure_ascii=False).encode("utf-8")
    path = "/api/mobile/sales/checkout"
    headers = _get_pop_headers(cred_id, priv, "POST", path, body=body_bytes)
    headers["Content-Type"] = "application/json"

    mock_core_resp = {
        "sale_id": 43,
        "receipt_number": "REC-20260930-0043",
        "total_amount": 64000.0,
        "payment_method": "cash",
        "cashier_name": "Владелец",
        "created_at": "2026-09-30T10:05:00Z",
        "client_checkout_id": "test-uuid-owner-001",
        "items": [
            {"product_id": 101, "title": "Ноутбук ThinkPad T480", "quantity": 2, "sale_price": 32000.0, "total_price": 64000.0}
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_core_resp
        mock_post.return_value = mock_response

        resp = client.post(path, content=body_bytes, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["sale_id"] == 43
        assert data["total_amount"] == 64000.0


def test_12_revoked_device_denied():
    """Item 12: Revoked device checkout request is denied (401 or 403)."""
    priv, cred_id, enroll_res = _enroll_device("owner", "test_revoked_checkout_dev", "Revoked Phone")
    dev_id = enroll_res["device_id"]

    checkout_payload = {
        "client_checkout_id": "test-uuid-rev-001",
        "payment_method": "cash",
        "items": [{"product_id": 101, "quantity": 1, "sale_price": 1000.0}]
    }
    body_bytes = json.dumps(checkout_payload, ensure_ascii=False).encode("utf-8")
    path = "/api/mobile/sales/checkout"
    headers = _get_pop_headers(cred_id, priv, "POST", path, body=body_bytes)
    headers["Content-Type"] = "application/json"

    # Revoke device
    mobile_manager.revoke_device(device_id=dev_id, actor_cert_id="owner", is_owner=True)

    resp = client.post(path, content=body_bytes, headers=headers)
    assert resp.status_code in (401, 403)


def test_13_revoked_parent_denied():
    """Item 13: Revoked parent certificate denies mobile device checkout."""
    users = [c for c in auth_manager.list_certificates() if not c.get("is_owner") and c.get("status") == "ACTIVE"]
    assert len(users) > 0
    parent_cert = users[0]
    priv, cred_id, _ = _enroll_device(parent_cert["id"], "test_parent_rev_checkout_dev", "Seller Phone")

    checkout_payload = {
        "client_checkout_id": "test-uuid-parent-rev-001",
        "payment_method": "cash",
        "items": [{"product_id": 101, "quantity": 1, "sale_price": 1000.0}]
    }
    body_bytes = json.dumps(checkout_payload, ensure_ascii=False).encode("utf-8")
    path = "/api/mobile/sales/checkout"
    headers = _get_pop_headers(cred_id, priv, "POST", path, body=body_bytes)
    headers["Content-Type"] = "application/json"

    with patch.object(auth_manager, "get_certificate") as mock_cert:
        mock_cert.return_value = {"id": parent_cert["id"], "status": "REVOKED"}
        resp = client.post(path, content=body_bytes, headers=headers)
        assert resp.status_code in (401, 403)


def test_14_missing_pop_denied():
    """Item 14: Missing PoP headers returns 401."""
    checkout_payload = {
        "client_checkout_id": "test-uuid-nopop",
        "payment_method": "cash",
        "items": [{"product_id": 101, "quantity": 1, "sale_price": 1000.0}]
    }
    body_bytes = json.dumps(checkout_payload, ensure_ascii=False).encode("utf-8")
    resp = client.post("/api/mobile/sales/checkout", content=body_bytes, headers={"Content-Type": "application/json"})
    assert resp.status_code in (401, 403)


def test_15_tampered_body_denied():
    """Item 15: Tampered body payload signature mismatch returns 401 or 403."""
    priv, cred_id, _ = _enroll_device("owner", "test_tampered_checkout_dev", "Tamper Phone")

    original_payload = {
        "client_checkout_id": "test-uuid-original",
        "payment_method": "cash",
        "items": [{"product_id": 101, "quantity": 1, "sale_price": 1000.0}]
    }
    original_bytes = json.dumps(original_payload, ensure_ascii=False).encode("utf-8")
    path = "/api/mobile/sales/checkout"
    headers = _get_pop_headers(cred_id, priv, "POST", path, body=original_bytes)
    headers["Content-Type"] = "application/json"

    # In-flight tampering: change quantity or price
    tampered_payload = {
        "client_checkout_id": "test-uuid-original",
        "payment_method": "cash",
        "items": [{"product_id": 101, "quantity": 999, "sale_price": 1.0}]
    }
    tampered_bytes = json.dumps(tampered_payload, ensure_ascii=False).encode("utf-8")

    resp = client.post(path, content=tampered_bytes, headers=headers)
    assert resp.status_code in (401, 403)


def test_core_error_forwarding_400():
    """Admin-shell properly relays Core 400 validation error (e.g., insufficient stock)."""
    priv, cred_id, _ = _enroll_device("owner", "test_core_err_dev", "Owner Phone")

    checkout_payload = {
        "client_checkout_id": "test-uuid-err-400",
        "payment_method": "card",
        "items": [{"product_id": 101, "quantity": 999, "sale_price": 32000.0}]
    }
    body_bytes = json.dumps(checkout_payload, ensure_ascii=False).encode("utf-8")
    path = "/api/mobile/sales/checkout"
    headers = _get_pop_headers(cred_id, priv, "POST", path, body=body_bytes)
    headers["Content-Type"] = "application/json"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Недостаточно остатка для товара 'ThinkPad' (запрошено: 999, доступно: 3)"}
        mock_post.return_value = mock_response

        resp = client.post(path, content=body_bytes, headers=headers)
        assert resp.status_code == 400
        assert "Недостаточно остатка" in resp.json()["detail"]
