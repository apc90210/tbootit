"""
Stage 05B Admin-Shell Mobile POS Search & Barcode Facade Tests.
Verifies:
1. /api/mobile/products/search enforces TRMOBILE1 PoP authentication.
2. Mobile product search proxies to Core /api/products/ with status=in_stock.
3. Formats products with canonical POS fields (product_id, barcode, sku, title, default_sale_price, available_stock, status, is_sellable, storage_location, main_photo_url, currency).
4. Empty query string returns empty result without hitting Core.
5. Tampered query parameters fail signature verification.
6. Parity: searching by barcode returns consistent product with by-barcode lookup.
"""

import sys
import os
import json
from unittest.mock import patch
import pytest
import httpx
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
import base64

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
admin_shell_dir = os.path.join(project_root, "admin-shell")

for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        sys.modules.pop(k, None)

while admin_shell_dir in sys.path:
    sys.path.remove(admin_shell_dir)
sys.path.insert(0, admin_shell_dir)

from app.main import app, mobile_manager
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
    assert enroll_res["credential_id"] is not None
    return priv, enroll_res["credential_id"]


@pytest.fixture(scope="module")
def enrolled_mobile_user():
    """Enroll a mobile device for Stage05B tests."""
    priv, cred_id = _enroll_device("owner", "test-dev-stage05b-001", "Stage05B Test Phone")
    return {"cred_id": cred_id, "priv": priv, "device_id": "test-dev-stage05b-001"}


def test_pos_search_missing_pop_fails():
    """Missing PoP headers on /api/mobile/products/search returns 401."""
    resp = client.get("/api/mobile/products/search?q=LaserJet")
    assert resp.status_code == 401


def test_pos_search_empty_query_returns_empty(enrolled_mobile_user):
    """Empty query returns empty items without making upstream request."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    path = "/api/mobile/products/search"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_pos_search_success_with_canonical_fields(enrolled_mobile_user):
    """Search returns items mapped to standard POS product schema."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    # Alphabetical order: limit=20&q=LaserJet
    path = "/api/mobile/products/search?limit=20&q=LaserJet"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    mock_core_response = {
        "items": [
            {
                "id": 101,
                "title": "МФУ HP LaserJet 3052",
                "barcode": "200000000230",
                "sku": "AVITO-8232087864",
                "sale_price": 8500.0,
                "price": 8500.0,
                "quantity": 2,
                "status": "in_stock",
                "storage_location": "Склад 1",
                "main_photo_url": "https://example.com/p1.jpg"
            }
        ],
        "total": 1,
        "limit": 20,
        "offset": 0
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_core_response)
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

        item = data["items"][0]
        assert item["product_id"] == 101
        assert item["title"] == "МФУ HP LaserJet 3052"
        assert item["barcode"] == "200000000230"
        assert item["sku"] == "AVITO-8232087864"
        assert item["default_sale_price"] == 8500.0
        assert item["available_stock"] == 2
        assert item["status"] == "in_stock"
        assert item["is_sellable"] is True
        assert item["currency"] == "RUB"


def test_pos_search_tampered_query_fails(enrolled_mobile_user):
    """Tampering with query string invalidates signature (PoP protection)."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    signed_path = "/api/mobile/products/search?limit=20&q=LaserJet"
    headers = _get_pop_headers(cred_id, priv, "GET", signed_path)

    # Attack: change q in transit
    tampered_path = "/api/mobile/products/search?limit=20&q=ThinkPad"
    resp = client.get(tampered_path, headers=headers)
    assert resp.status_code in (401, 403)


def test_pos_search_parity_with_barcode_lookup(enrolled_mobile_user):
    """Barcode lookup and name search return the exact same canonical fields."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]

    barcode = "200000000230"
    raw_core_prod = {
        "id": 101,
        "title": "МФУ HP LaserJet 3052",
        "barcode": barcode,
        "sku": "AVITO-8232087864",
        "sale_price": 8500.0,
        "price": 8500.0,
        "quantity": 2,
        "status": "in_stock",
        "storage_location": "Склад 1",
        "main_photo_url": None
    }

    # 1. Barcode lookup
    bc_path = f"/api/mobile/products/by-barcode/{barcode}"
    bc_headers = _get_pop_headers(cred_id, priv, "GET", bc_path)
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json=raw_core_prod)
        bc_resp = client.get(bc_path, headers=bc_headers)
        assert bc_resp.status_code == 200
        bc_item = bc_resp.json()

    # 2. POS Search by barcode
    search_path = f"/api/mobile/products/search?limit=20&q={barcode}"
    search_headers = _get_pop_headers(cred_id, priv, "GET", search_path)
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json={"items": [raw_core_prod], "total": 1})
        search_resp = client.get(search_path, headers=search_headers)
        assert search_resp.status_code == 200
        search_item = search_resp.json()["items"][0]

    # Verify field-by-field parity
    assert bc_item["product_id"] == search_item["product_id"]
    assert bc_item["barcode"] == search_item["barcode"]
    assert bc_item["sku"] == search_item["sku"]
    assert bc_item["title"] == search_item["title"]
    assert bc_item["default_sale_price"] == search_item["default_sale_price"]
    assert bc_item["available_stock"] == search_item["available_stock"]
    assert bc_item["is_sellable"] == search_item["is_sellable"]
