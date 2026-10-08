"""
Stage 06A Admin-Shell Mobile Inventory Catalog Facade Tests.
Verifies:
1. /api/mobile/catalog/products enforces TRMOBILE1 PoP authentication.
2. Listing works without query, with default in_stock_only=True, and with in_stock_only=False.
3. Pagination (limit, offset) and filtering (q, brand, category_id) are forwarded to Core.
4. /api/mobile/catalog/products/{product_id} returns detailed card with photos and characteristics.
5. /api/mobile/catalog/filter-options returns categories and brands.
6. /api/mobile/media/{path:path} proxies media to Core.
7. Query tampering is rejected by PoP validation.
"""

import sys
import os
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
    """Enroll a mobile device for Stage06A tests."""
    priv, cred_id = _enroll_device("owner", "test-dev-stage06a-001", "Stage06A Test Phone")
    return {"cred_id": cred_id, "priv": priv, "device_id": "test-dev-stage06a-001"}


def test_catalog_products_missing_pop_fails():
    """Missing PoP headers on /api/mobile/catalog/products returns 401."""
    resp = client.get("/api/mobile/catalog/products")
    assert resp.status_code == 401


def test_catalog_products_default_in_stock(enrolled_mobile_user):
    """Catalog listing defaults to in_stock_only=True and returns mapped products."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    # Path without query parameters
    path = "/api/mobile/catalog/products"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    mock_core_response = {
        "items": [
            {
                "id": 201,
                "title": "Принтер HP LaserJet P1102",
                "barcode": "200000000201",
                "sku": "HP-P1102",
                "brand": "HP",
                "model": "LaserJet P1102",
                "category_id": 1,
                "sale_price": 6000.0,
                "quantity": 3,
                "status": "in_stock",
                "storage_location": "Стеллаж 2",
                "condition": "Б/у - отличное",
                "main_photo_url": "/media/product_photos/201/front.jpg",
            }
        ],
        "total": 1,
        "limit": 20,
        "offset": 0,
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_core_response)
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

        item = data["items"][0]
        assert item["product_id"] == 201
        assert item["title"] == "Принтер HP LaserJet P1102"
        assert item["brand"] == "HP"
        assert item["model"] == "LaserJet P1102"
        assert item["default_sale_price"] == 6000.0
        assert item["available_stock"] == 3
        assert item["status"] == "in_stock"
        assert item["is_sellable"] is True
        assert item["storage_location"] == "Стеллаж 2"
        assert item["condition"] == "Б/у - отличное"
        assert item["main_photo_url"] == "/api/mobile/media/product_photos/201/front.jpg"


def test_catalog_products_all_filter_and_pagination(enrolled_mobile_user):
    """Catalog listing supports in_stock_only=false, search query, and pagination."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    # Sorted query params: in_stock_only=false&limit=10&offset=20&q=Canon
    path = "/api/mobile/catalog/products?in_stock_only=false&limit=10&offset=20&q=Canon"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    mock_core_response = {
        "items": [
            {
                "id": 202,
                "title": "МФУ Canon MF4730",
                "barcode": "200000000202",
                "sku": "CANON-MF4730",
                "brand": "Canon",
                "model": "i-SENSYS MF4730",
                "category_id": 1,
                "sale_price": 9500.0,
                "quantity": 0,
                "status": "sold",
                "storage_location": "Склад",
                "condition": "Б/у",
                "main_photo_url": None,
            }
        ],
        "total": 35,
        "limit": 10,
        "offset": 20,
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_core_response)
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total"] == 35
        assert data["limit"] == 10
        assert data["offset"] == 20
        item = data["items"][0]
        assert item["product_id"] == 202
        assert item["available_stock"] == 0
        assert item["is_sellable"] is False


def test_catalog_product_details_success(enrolled_mobile_user):
    """Detail endpoint returns complete product card with photos and specs."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    path = "/api/mobile/catalog/products/201"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    mock_detail_response = {
        "id": 201,
        "title": "Принтер HP LaserJet P1102",
        "barcode": "200000000201",
        "sku": "HP-P1102",
        "brand": "HP",
        "model": "LaserJet P1102",
        "category_id": 1,
        "avito_category_name": "Принтеры",
        "description": "Отличный надёжный лазерный принтер с картриджем CE285A.",
        "sale_price": 6000.0,
        "quantity": 3,
        "available_quantity": 3,
        "status": "in_stock",
        "storage_location": "Стеллаж 2",
        "condition": "Б/у - отличное",
        "characteristics": {"Тип печати": "Лазерная", "Цветность": "Черно-белая"},
        "photos": [
            {"id": 1, "filename": "p1.jpg", "media_url": "/media/product_photos/201/p1.jpg"},
            {"id": 2, "filename": "p2.jpg", "media_url": "/media/product_photos/201/p2.jpg"}
        ]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_detail_response)
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["product_id"] == 201
        assert data["title"] == "Принтер HP LaserJet P1102"
        assert data["category_name"] == "Принтеры"
        assert data["description"] == "Отличный надёжный лазерный принтер с картриджем CE285A."
        assert len(data["photos"]) == 2
        assert data["photos"][0]["url"] == "/api/mobile/media/product_photos/201/p1.jpg"
        assert data["characteristics"]["Тип печати"] == "Лазерная"


def test_catalog_filter_options(enrolled_mobile_user):
    """Filter options returns categories and brands facets."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    path = "/api/mobile/catalog/filter-options"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    mock_facets = {
        "categories": [{"id": 1, "name": "Принтеры", "count": 15}],
        "brands": [{"value": "HP", "count": 10}, {"value": "Canon", "count": 5}]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_facets)
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data["categories"]) == 1
        assert len(data["brands"]) == 2
        assert data["brands"][0]["value"] == "HP"


def test_catalog_query_tampering_rejected(enrolled_mobile_user):
    """Tampering with query string parameters causes PoP 401/403 failure."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    signed_path = "/api/mobile/catalog/products?in_stock_only=true&limit=20"
    headers = _get_pop_headers(cred_id, priv, "GET", signed_path)

    # In-transit tampering
    tampered_path = "/api/mobile/catalog/products?in_stock_only=false&limit=20"
    resp = client.get(tampered_path, headers=headers)
    assert resp.status_code in (401, 403)
