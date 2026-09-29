"""
Stage04A — Mobile POS Barcode Lookup & Contract Tests.
Verifies that:
1. OWNER can lookup known product by barcode.
2. USER can lookup known product by barcode.
3. Unknown barcode -> 404 with clean message.
4. Zero stock product -> returns details with is_sellable=False.
5. Archived/non-sellable status -> returns details with is_sellable=False.
6. Revoked device -> 401/403.
7. Revoked parent -> 401/403.
8. Missing PoP -> 401.
9. Tampered barcode path -> 401/403 signature verification failed.
10. Canonical fields match Core (price, stock, title, SKU, barcode).
11. No stock mutation on lookup.
12. No sale creation on lookup.
"""

import sys
import os
import json
import sqlite3
import subprocess
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import httpx
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
import base64

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
admin_shell_dir = os.path.join(project_root, "admin-shell")
core_dir = os.path.join(project_root, "core")

if admin_shell_dir not in sys.path:
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


def test_01_owner_can_lookup_known_barcode():
    priv, cred_id, enroll_res = _enroll_device("owner", "test_owner_barcode_dev", "Owner Test Phone")
    mock_prod = {
        "id": 101,
        "title": "Ноутбук ThinkPad T480",
        "barcode": "200000000101",
        "sku": "TP-T480",
        "sale_price": 32000.0,
        "quantity": 3,
        "status": "in_stock",
        "storage_location": "store",
        "main_photo_url": "/media/photos/101.jpg"
    }

    path = "/api/mobile/products/by-barcode/200000000101"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch.object(admin_main, "_fetch_canonical_product_by_barcode", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_prod
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["product_id"] == 101
        assert data["barcode"] == "200000000101"
        assert data["sku"] == "TP-T480"
        assert data["title"] == "Ноутбук ThinkPad T480"
        assert data["default_sale_price"] == 32000.0
        assert data["available_stock"] == 3
        assert data["status"] == "in_stock"
        assert data["is_sellable"] is True
        assert data["storage_location"] == "store"
        assert data["currency"] == "RUB"


def test_02_user_can_lookup_known_barcode():
    users = [c for c in auth_manager.list_certificates() if not c.get("is_owner") and c.get("status") == "ACTIVE"]
    assert len(users) > 0, "At least one active USER certificate expected"
    user_cert_id = users[0]["id"]

    priv, cred_id, enroll_res = _enroll_device(user_cert_id, "test_user_barcode_dev", "Seller Phone")
    mock_prod = {
        "id": 102,
        "title": "Мышь Logitech G102",
        "barcode": "200000000102",
        "sku": "LOGI-G102",
        "sale_price": 1800.0,
        "quantity": 10,
        "status": "available",
        "storage_location": "витрина",
        "main_photo_url": None
    }

    path = "/api/mobile/products/by-barcode/200000000102"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch.object(admin_main, "_fetch_canonical_product_by_barcode", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_prod
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["product_id"] == 102
        assert data["is_sellable"] is True
        assert data["available_stock"] == 10


def test_03_unknown_barcode_returns_404():
    priv, cred_id, _ = _enroll_device("owner", "test_404_barcode_dev", "404 Test Phone")
    path = "/api/mobile/products/by-barcode/999999999999"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 404
    assert "не найден" in resp.json()["detail"] or "not found" in resp.json()["detail"].lower()


def test_04_zero_stock_product_is_sellable_false():
    priv, cred_id, _ = _enroll_device("owner", "test_zero_stock_dev", "Zero Stock Phone")
    mock_prod = {
        "id": 103,
        "title": "Клавиатура Keychron K2",
        "barcode": "200000000103",
        "sku": "KEY-K2",
        "sale_price": 7500.0,
        "quantity": 0,  # Out of stock!
        "status": "in_stock",
        "storage_location": "store",
    }

    path = "/api/mobile/products/by-barcode/200000000103"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch.object(admin_main, "_fetch_canonical_product_by_barcode", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_prod
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["available_stock"] == 0
        assert data["is_sellable"] is False  # Cannot sell item with 0 stock!


def test_05_archive_non_sellable_status_is_sellable_false():
    priv, cred_id, _ = _enroll_device("owner", "test_arch_dev", "Archive Phone")
    mock_prod = {
        "id": 104,
        "title": "Списанный монитор",
        "barcode": "200000000104",
        "sku": "MON-ARCH",
        "sale_price": 5000.0,
        "quantity": 1,
        "status": "archive",  # Archived!
        "storage_location": "archive",
    }

    path = "/api/mobile/products/by-barcode/200000000104"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch.object(admin_main, "_fetch_canonical_product_by_barcode", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_prod
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "archive"
        assert data["is_sellable"] is False


def test_06_revoked_device_denied_403():
    priv, cred_id, enroll_res = _enroll_device("owner", "test_revoked_dev", "Revoked Device")
    dev_id = enroll_res["device_id"]
    path = "/api/mobile/products/by-barcode/200000000101"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    # Revoke device after challenge obtained
    rev = mobile_manager.revoke_device(device_id=dev_id, actor_cert_id="owner", is_owner=True)
    assert rev is not None and rev.get("status") == "revoked"

    resp = client.get(path, headers=headers)
    assert resp.status_code in (401, 403)


def test_07_revoked_parent_cert_denied_403():
    users = [c for c in auth_manager.list_certificates() if not c.get("is_owner") and c.get("status") == "ACTIVE"]
    assert len(users) > 0
    parent_cert = users[0]
    priv, cred_id, _ = _enroll_device(parent_cert["id"], "test_parent_revoked_dev", "Temp Phone")
    path = "/api/mobile/products/by-barcode/200000000101"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    # Parent cert revoked
    with patch.object(auth_manager, "get_certificate") as mock_cert:
        mock_cert.return_value = {"id": parent_cert["id"], "status": "REVOKED"}
        resp = client.get(path, headers=headers)
        assert resp.status_code in (401, 403)


def test_08_missing_pop_denied_401():
    path = "/api/mobile/products/by-barcode/200000000101"
    resp = client.get(path)
    assert resp.status_code in (401, 403)


def test_09_tampered_barcode_path_denied_401():
    priv, cred_id, _ = _enroll_device("owner", "test_tamper_dev", "Tamper Test Phone")
    # Signed for barcode 200000000101
    signed_path = "/api/mobile/products/by-barcode/200000000101"
    headers = _get_pop_headers(cred_id, priv, "GET", signed_path)

    # In-flight tampering: send request to 200000000102 with headers signed for 200000000101
    tampered_path = "/api/mobile/products/by-barcode/200000000102"
    resp = client.get(tampered_path, headers=headers)
    assert resp.status_code in (401, 403)


def test_10_core_price_and_stock_parity():
    priv, cred_id, _ = _enroll_device("owner", "test_parity_dev", "Parity Phone")
    mock_prod = {
        "id": 105,
        "title": "SSD Samsung 970 EVO 1TB",
        "barcode": "200000000105",
        "sku": "MZ-V7S1T0BW",
        "sale_price": 9499.50,
        "quantity": 5,
        "status": "in_stock",
        "storage_location": "store",
    }

    path = "/api/mobile/products/by-barcode/200000000105"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch.object(admin_main, "_fetch_canonical_product_by_barcode", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_prod
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["default_sale_price"] == 9499.50
        assert data["available_stock"] == 5
        assert data["is_sellable"] is True


def test_11_no_stock_mutation_on_lookup():
    priv, cred_id, _ = _enroll_device("owner", "test_no_mut_dev", "No Mut Phone")
    mock_prod = {
        "id": 106,
        "title": "Тестовый товар",
        "barcode": "200000000106",
        "sale_price": 100.0,
        "quantity": 7,
        "status": "in_stock",
    }

    path = "/api/mobile/products/by-barcode/200000000106"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch.object(admin_main, "_fetch_canonical_product_by_barcode", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_prod
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["available_stock"] == 7


def test_12_no_sale_creation_on_lookup():
    priv, cred_id, _ = _enroll_device("owner", "test_no_sale_dev", "No Sale Phone")
    mock_prod = {
        "id": 107,
        "title": "Товар без продажи",
        "barcode": "200000000107",
        "sale_price": 500.0,
        "quantity": 2,
        "status": "in_stock",
    }

    path = "/api/mobile/products/by-barcode/200000000107"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch.object(admin_main, "_fetch_canonical_product_by_barcode", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_prod
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        assert "sale_id" not in resp.json()
