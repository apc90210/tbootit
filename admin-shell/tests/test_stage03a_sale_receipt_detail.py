"""
Stage03A — Sale Receipt Detail Lazy-Load & Contract Tests.
Verifies that:
1. OWNER can fetch receipt.
2. USER can fetch receipt if USER has report access.
3. Unknown sale -> 404.
4. Revoked device -> deny.
5. Revoked parent -> deny.
6. Missing PoP -> deny.
7. Tampered sale_id path -> deny.
8. Receipt totals match stored sale.
9. Item lines match stored historical sale lines.
10. Payment method/label correct.
11. Status correct.
12. Canceled sale detail behavior correct.
13. Core/Admin-Shell contract parity.
14. No DB mutation.
"""

import sys
import os
import json
import sqlite3
import subprocess
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
import pytest
import httpx
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# Ensure admin-shell is loaded as 'app'
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
admin_shell_dir = os.path.join(project_root, "admin-shell")
core_dir = os.path.join(project_root, "core")

for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        sys.modules.pop(k, None)

if admin_shell_dir not in sys.path:
    sys.path.insert(0, admin_shell_dir)

from app.main import app, auth_manager, mobile_manager, CORE_API_URL
from app.mobile_manager import build_canonical_signing_payload, compute_body_sha256

client = TestClient(app)


def _get_canonical_receipt(sale_id: int) -> dict:
    """Fetch canonical core sale receipt directly from Core HTTP API or isolated test harness."""
    import urllib.request
    core_url = os.getenv("CORE_API_URL", "http://127.0.0.1:8000")
    headers = {"x-api-token": os.getenv("CORE_API_TOKEN", "dev-token")}
    try:
        req = urllib.request.Request(f"{core_url}/api/sales/{sale_id}/receipt", headers=headers)
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        pass

    # Test-harness isolated fallback if Core daemon is offline
    db_file = os.path.join(project_root, "data", "db", "technoreboot.db")
    if not os.path.exists(db_file):
        db_file = os.path.join(project_root, "technoreboot.db")

    script = f"""
import sys, json, os
sys.path.insert(0, {repr(core_dir)})
os.environ["DATABASE_URL"] = {repr(f"sqlite:///{db_file}")}
from app.database import SessionLocal
from app.routers.sales import get_sale_receipt

db = SessionLocal()
try:
    r = get_sale_receipt(sale_id={sale_id}, db=db)
    data = r.model_dump() if hasattr(r, 'model_dump') else r.dict()
    print(json.dumps(data, ensure_ascii=True, default=str))
finally:
    db.close()
"""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["DATABASE_URL"] = f"sqlite:///{db_file}"
    p = subprocess.run(
        [sys.executable, "-"],
        input=script,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=True,
    )
    return json.loads(p.stdout)


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


def _insert_test_sale_with_items(total_amount: float, status: str, payment_method: str, items: list, created_at_str: str = None) -> list:
    if created_at_str is None:
        created_at_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_paths = [
        os.path.join(project_root, "data", "db", "technoreboot.db"),
        os.path.join(project_root, "technoreboot.db"),
    ]
    ids = []
    for p in db_paths:
        if os.path.exists(p):
            conn = sqlite3.connect(p)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO sales (total_amount, status, payment_method, created_at) VALUES (?, ?, ?, ?)",
                (total_amount, status, payment_method, created_at_str),
            )
            sale_id = cur.lastrowid
            for it in items:
                cur.execute(
                    "INSERT INTO sale_items (sale_id, product_id, title, price, quantity, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (sale_id, it.get("product_id"), it.get("title"), it.get("price"), it.get("quantity"), created_at_str),
                )
            conn.commit()
            conn.close()
            ids.append((p, sale_id))
    return ids


def _delete_test_sales(inserted_ids: list):
    for p, sale_id in inserted_ids:
        if os.path.exists(p):
            conn = sqlite3.connect(p)
            cur = conn.cursor()
            cur.execute("DELETE FROM sale_items WHERE sale_id = ?", (sale_id,))
            cur.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
            conn.commit()
            conn.close()


@pytest.fixture
def enrolled_user():
    user_cert = auth_manager.create_user_certificate(f"Stage03A User {datetime.now(timezone.utc).timestamp()}")
    headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": user_cert["serial_hex"],
        "x-client-cert-fingerprint": user_cert["fingerprint_sha256"],
    }
    p_resp = client.post("/admin-api/mobile/pairing/generate", headers=headers)
    assert p_resp.status_code == 200
    pairing_code = p_resp.json()["pairing_code"]

    priv, pub_pem = _gen_android_keypair()
    dev_id = f"tr_dev_user_03a_{datetime.now(timezone.utc).timestamp()}"
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
    dev_id = f"tr_dev_owner_03a_{datetime.now(timezone.utc).timestamp()}"
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


# ===========================================================================
# 1. OWNER can fetch receipt
# ===========================================================================

def test_01_owner_can_fetch_receipt(enrolled_owner):
    items = [
        {"product_id": 148, "title": "Принтер Xerox", "price": 15000.0, "quantity": 1},
        {"product_id": None, "title": "Услуга настройки", "price": 1000.0, "quantity": 1},
    ]
    sale_entries = _insert_test_sale_with_items(16000.0, "completed", "card", items)
    sale_id = sale_entries[0][1]

    try:
        cred_id = enrolled_owner["credential_id"]
        priv = enrolled_owner["priv_key"]
        path = f"/api/mobile/sales/{sale_id}/receipt"
        headers = _get_pop_headers(cred_id, priv, "GET", path)

        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["sale_id"] == sale_id
        assert data["receipt_number"] == str(sale_id)
        assert data["total_amount"] == 16000.0
        assert data["status"] == "completed"
        assert len(data["items"]) == 2
    finally:
        _delete_test_sales(sale_entries)


# ===========================================================================
# 2. USER can fetch receipt if USER has report access
# ===========================================================================

def test_02_user_can_fetch_receipt_if_user_has_report_access(enrolled_user):
    items = [{"product_id": None, "title": "Кабель USB", "price": 350.0, "quantity": 2}]
    sale_entries = _insert_test_sale_with_items(700.0, "completed", "cash", items)
    sale_id = sale_entries[0][1]

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        path = f"/api/mobile/sales/{sale_id}/receipt"
        headers = _get_pop_headers(cred_id, priv, "GET", path)

        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["sale_id"] == sale_id
        assert data["total_amount"] == 700.0
    finally:
        _delete_test_sales(sale_entries)


# ===========================================================================
# 3. Unknown sale -> 404
# ===========================================================================

def test_03_unknown_sale_returns_404(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/sales/99999999/receipt"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 404, resp.text
    assert "not found" in resp.json()["detail"].lower()


# ===========================================================================
# 4. Revoked device -> deny
# ===========================================================================

def test_04_revoked_device_denied(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    dev_id = enrolled_user["device_id"]
    priv = enrolled_user["priv_key"]
    parent_id = enrolled_user["cert"]["id"]

    path = "/api/mobile/sales/1/receipt"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    # Revoke device
    rev = mobile_manager.revoke_device(device_id=dev_id, actor_cert_id=parent_id, is_owner=False)
    assert rev is not None and rev.get("status") == "revoked"

    resp = client.get(path, headers=headers)
    assert resp.status_code in (401, 403), f"Expected 401/403 for revoked device, got {resp.status_code}"



# ===========================================================================
# 5. Revoked parent -> deny
# ===========================================================================

def test_05_revoked_parent_denied(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    cert = enrolled_user["cert"]

    # Revoke parent certificate
    auth_manager.revoke_certificate(cert["id"])

    path = "/api/mobile/sales/1/receipt"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code in (401, 403), f"Expected 401/403 for revoked parent, got {resp.status_code}"


# ===========================================================================
# 6. Missing PoP -> deny
# ===========================================================================

def test_06_missing_pop_headers_denied():
    resp = client.get("/api/mobile/sales/1/receipt")
    assert resp.status_code in (401, 403)


# ===========================================================================
# 7. Tampered sale_id path -> deny
# ===========================================================================

def test_07_tampered_sale_id_path_denied(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]

    signed_path = "/api/mobile/sales/1/receipt"
    headers = _get_pop_headers(cred_id, priv, "GET", signed_path)

    # Attack: tamper with sale_id in request URL after signing
    tampered_path = "/api/mobile/sales/2/receipt"
    resp = client.get(tampered_path, headers=headers)
    assert resp.status_code in (401, 403), f"Expected tamper rejection, got {resp.status_code}"


# ===========================================================================
# 8. Receipt totals match stored sale
# ===========================================================================

def test_08_receipt_totals_match_stored_sale(enrolled_user):
    items = [
        {"product_id": None, "title": "Товар 1", "price": 1250.50, "quantity": 2},
        {"product_id": None, "title": "Товар 2", "price": 499.00, "quantity": 1},
    ]
    total = 1250.50 * 2 + 499.00
    sale_entries = _insert_test_sale_with_items(total, "completed", "cash", items)
    sale_id = sale_entries[0][1]

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        path = f"/api/mobile/sales/{sale_id}/receipt"
        headers = _get_pop_headers(cred_id, priv, "GET", path)

        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_amount"] == total
        calc_total = sum(it["line_total"] for it in data["items"])
        assert abs(calc_total - total) < 0.01
    finally:
        _delete_test_sales(sale_entries)


# ===========================================================================
# 9. Item lines match stored historical sale lines
# ===========================================================================

def test_09_item_lines_match_stored_historical_sale_lines(enrolled_user):
    items = [
        {"product_id": 148, "title": "Историческое наименование товара", "price": 1234.50, "quantity": 3},
    ]
    sale_entries = _insert_test_sale_with_items(3703.50, "completed", "transfer", items)
    sale_id = sale_entries[0][1]

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        path = f"/api/mobile/sales/{sale_id}/receipt"
        headers = _get_pop_headers(cred_id, priv, "GET", path)

        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        assert len(data["items"]) == 1
        it = data["items"][0]
        assert it["title"] == "Историческое наименование товара"
        assert it["unit_price"] == 1234.50
        assert it["quantity"] == 3
        assert it["line_total"] == 3703.50
        assert it["product_id"] == 148
    finally:
        _delete_test_sales(sale_entries)


# ===========================================================================
# 10. Payment method / label correct
# ===========================================================================

def test_10_payment_method_label_correct(enrolled_user):
    for method, expected_label in [
        ("cash", "Наличные"),
        ("card", "Безнал / карта"),
        ("transfer", "Перевод"),
        ("sbp", "СБП"),
        ("legal_entity_account", "Счёт юрлица"),
        ("mixed", "Смешанная оплата"),
        ("other", "Другое"),
    ]:
        items = [{"product_id": None, "title": "Тестовая позиция", "price": 100.0, "quantity": 1}]
        sale_entries = _insert_test_sale_with_items(100.0, "completed", method, items)
        sale_id = sale_entries[0][1]

        try:
            cred_id = enrolled_user["credential_id"]
            priv = enrolled_user["priv_key"]
            path = f"/api/mobile/sales/{sale_id}/receipt"
            headers = _get_pop_headers(cred_id, priv, "GET", path)

            resp = client.get(path, headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["payment_method"] == method
            assert data["payment_label"] == expected_label
        finally:
            _delete_test_sales(sale_entries)


# ===========================================================================
# 11. Status correct
# ===========================================================================

def test_11_status_correct(enrolled_user):
    for st in ["completed", "reissued", "superseded"]:
        items = [{"product_id": None, "title": "Тест статус", "price": 500.0, "quantity": 1}]
        sale_entries = _insert_test_sale_with_items(500.0, st, "cash", items)
        sale_id = sale_entries[0][1]

        try:
            cred_id = enrolled_user["credential_id"]
            priv = enrolled_user["priv_key"]
            path = f"/api/mobile/sales/{sale_id}/receipt"
            headers = _get_pop_headers(cred_id, priv, "GET", path)

            resp = client.get(path, headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == st
        finally:
            _delete_test_sales(sale_entries)


# ===========================================================================
# 12. Canceled sale detail behavior correct
# ===========================================================================

def test_12_canceled_sale_detail_behavior_correct(enrolled_user):
    items = [{"product_id": None, "title": "Отменённый товар", "price": 2500.0, "quantity": 1}]
    sale_entries = _insert_test_sale_with_items(2500.0, "canceled", "card", items)
    sale_id = sale_entries[0][1]

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        path = f"/api/mobile/sales/{sale_id}/receipt"
        headers = _get_pop_headers(cred_id, priv, "GET", path)

        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["sale_id"] == sale_id
        assert data["status"] == "canceled"
        assert data["total_amount"] == 2500.0
        assert len(data["items"]) == 1
    finally:
        _delete_test_sales(sale_entries)


# ===========================================================================
# 13. Core / Admin-Shell contract parity
# ===========================================================================

def test_13_core_admin_shell_contract_parity(enrolled_user):
    # Fetch real sale 1 via canonical Core
    canonical = _get_canonical_receipt(1)

    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/sales/1/receipt"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    mobile = resp.json()

    assert mobile["sale_id"] == canonical["sale_id"]
    assert mobile["receipt_number"] == canonical["receipt_number"]
    assert mobile["status"] == canonical["status"]
    assert mobile["total_amount"] == canonical["total_amount"]
    assert mobile["payment_method"] == canonical["payment_method"]
    assert mobile["payment_label"] == canonical["payment_label"]
    assert len(mobile["items"]) == len(canonical["items"])
    for m_it, c_it in zip(mobile["items"], canonical["items"]):
        assert m_it["title"] == c_it["title"]
        assert m_it["unit_price"] == c_it["unit_price"]
        assert m_it["quantity"] == c_it["quantity"]
        assert m_it["line_total"] == c_it["line_total"]


# ===========================================================================
# 14. No DB mutation
# ===========================================================================

def test_14_no_db_mutation(enrolled_user):
    db_file = os.path.join(project_root, "data", "db", "technoreboot.db")
    if not os.path.exists(db_file):
        db_file = os.path.join(project_root, "technoreboot.db")

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sales")
    sales_count_before = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM sale_items")
    items_count_before = cur.fetchone()[0]
    cur.execute("SELECT total_amount, status, payment_method FROM sales WHERE id = 1")
    sale_1_before = cur.fetchone()
    conn.close()

    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/sales/1/receipt"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sales")
    sales_count_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM sale_items")
    items_count_after = cur.fetchone()[0]
    cur.execute("SELECT total_amount, status, payment_method FROM sales WHERE id = 1")
    sale_1_after = cur.fetchone()
    conn.close()

    assert sales_count_before == sales_count_after
    assert items_count_before == items_count_after
    assert sale_1_before == sale_1_after
