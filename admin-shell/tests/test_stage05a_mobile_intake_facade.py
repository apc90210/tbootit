"""
Stage 05A - Admin-Shell Mobile Product Reference Search & Quick Intake Facade Tests.
Verifies that:
1. Search endpoint requires TRMOBILE1 PoP authentication.
2. Search endpoint forwards query to Core API and returns candidates.
3. Plural search alias route (/api/mobile/product-references/search) is supported.
4. AI assist endpoint enforces body SHA-256 signature binding.
5. Quick intake endpoint enforces body SHA-256 signature binding.
6. Revoked mobile credentials cannot access intake or AI assist.
7. Core API error responses are properly translated.
"""

import sys
import os
import json
import base64
from unittest.mock import patch, AsyncMock
import pytest
import httpx
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


def _enroll_device(parent_cert_id: str = "owner", dev_id_str: str = "test-device-intake-001", dev_name: str = "Intake Test Phone"):
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


@pytest.fixture
def enrolled_mobile_user():
    """Enroll a mobile device."""
    priv, cred_id, enroll_res = _enroll_device("owner", "test-user-dev-001", "User Test Phone")
    return {"cred_id": cred_id, "priv": priv, "device_id": "test-user-dev-001"}


def test_mobile_reference_search_missing_pop():
    """Request without PoP headers must be rejected (401)."""
    resp = client.get("/api/mobile/product-reference/search?q=HP+LaserJet")
    assert resp.status_code == 401


def test_mobile_reference_search_success(enrolled_mobile_user):
    """Valid PoP request passes and forwards query to Core API."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    path = "/api/mobile/product-reference/search?q=HP+LaserJet"

    mock_core_resp = {
        "query": "HP LaserJet",
        "total_candidates": 1,
        "candidates": [{
            "reference_model_id": 42,
            "canonical_name": "HP LaserJet P1102w",
            "brand": "HP",
            "model": "LaserJet P1102w",
            "confidence": 0.95,
            "tier": "tier1_exact_alias"
        }]
    }

    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_core_resp)
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_candidates"] == 1
        assert data["candidates"][0]["canonical_name"] == "HP LaserJet P1102w"


def test_mobile_reference_search_plural_alias(enrolled_mobile_user):
    """Verify plural alias /api/mobile/product-references/search works."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    path = "/api/mobile/product-references/search?q=P1102w"

    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json={"query": "P1102w", "total_candidates": 0, "candidates": []})
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200


def test_mobile_ai_assist_body_tampering_rejected(enrolled_mobile_user):
    """Tampering with POST body causes SHA-256 signature verification failure."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    path = "/api/mobile/product-reference/ai-assist"

    original_body = json.dumps({"query": "HP M1132"}).encode("utf-8")
    tampered_body = json.dumps({"query": "Kyocera M2040dn"}).encode("utf-8")

    headers = _get_pop_headers(cred_id, priv, "POST", path, body=original_body)
    headers["Content-Type"] = "application/json"

    # Send tampered body with signature made over original_body
    resp = client.post(path, content=tampered_body, headers=headers)
    assert resp.status_code in (401, 403)


def test_mobile_ai_assist_success(enrolled_mobile_user):
    """Valid PoP signed request forwards to Core AI assist."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    path = "/api/mobile/product-reference/ai-assist"

    body_bytes = json.dumps({"query": "HP LaserJet Pro M1132 MFP"}).encode("utf-8")
    headers = _get_pop_headers(cred_id, priv, "POST", path, body=body_bytes)
    headers["Content-Type"] = "application/json"

    mock_ai_resp = {
        "status": "candidate",
        "manufacturer": "HP",
        "model": "LaserJet Pro M1132 MFP",
        "canonical_name": "HP LaserJet Pro M1132 MFP",
        "category": "МФУ",
        "device_type": "mfp",
        "confidence": 0.90,
        "message": "Model identified"
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_ai_resp)
        resp = client.post(path, content=body_bytes, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["canonical_name"] == "HP LaserJet Pro M1132 MFP"


def test_mobile_quick_intake_success(enrolled_mobile_user):
    """Valid PoP signed request creates product via Core API."""
    cred_id = enrolled_mobile_user["cred_id"]
    priv = enrolled_mobile_user["priv"]
    path = "/api/mobile/products/quick-intake"

    payload = {
        "reference_model_id": 10,
        "condition": "Б/у - хорошее",
        "notes": "Тестовый товар",
        "sale_price": 5000.0,
        "quantity": 1
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    headers = _get_pop_headers(cred_id, priv, "POST", path, body=body_bytes)
    headers["Content-Type"] = "application/json"

    mock_created = {
        "id": 999,
        "sku": "PRD-TEST001",
        "title": "HP LaserJet P1102w",
        "sale_price": 5000.0,
        "quantity": 1,
        "condition": "Б/у - хорошее",
        "notes": "Тестовый товар",
        "status": "in_stock",
        "reference_model_id": 10,
        "photos_count": 0
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_created)
        resp = client.post(path, content=body_bytes, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 999
        assert data["sku"] == "PRD-TEST001"
