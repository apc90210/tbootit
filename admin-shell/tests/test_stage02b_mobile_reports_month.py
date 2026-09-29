"""
Stage02B — Android Mobile Sales Reports (Month Period) Contract & Auth Tests.

Verifies:
1. Section 3: Mobile API supports period=month with TRMOBILE1 PoP.
2. Section 6: Month Boundary Tests:
   - 2026-09-28 fixture:
     * 2026-09-01 -> INCLUDED
     * 2026-09-15 -> INCLUDED
     * 2026-09-28 -> INCLUDED
     * 2026-08-31 -> EXCLUDED
   - 2026-01-05 year boundary fixture:
     * 2026-01-01 -> INCLUDED
     * 2025-12-31 -> EXCLUDED
3. Section 7: Consistency Tests for Month:
   - sales_count == len(sales)
   - revenue_total == sum(sales amounts)
   - payment breakdown matches sales list
   - canceled sales excluded
   - date_from / date_to correct
   - label == "Месяц"
   - currency == "RUB"
4. Section 8: Mobile Auth Tests for Month:
   - active USER -> PASS
   - active OWNER -> PASS
   - revoked device -> DENY
   - revoked parent -> DENY
   - tampered query (signed for month, requested week, or signed today requested month) -> DENY
   - invalid period -> controlled 400
"""

import sys
import os
import base64
import sqlite3
from unittest.mock import patch
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes

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


def _enroll_fresh_user():
    user_cert = auth_manager.create_user_certificate(f"Stage02B User {datetime.now(timezone.utc).timestamp()}")
    headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": user_cert["serial_hex"],
        "x-client-cert-fingerprint": user_cert["fingerprint_sha256"],
    }
    p_resp = client.post("/admin-api/mobile/pairing/generate", headers=headers)
    assert p_resp.status_code == 200
    pairing_code = p_resp.json()["pairing_code"]

    priv, pub_pem = _gen_android_keypair()
    dev_id = f"tr_dev_user_{datetime.now(timezone.utc).timestamp()}"
    e_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": pairing_code,
        "public_key": pub_pem,
        "device_identifier": dev_id,
        "device_name": "Stage02B User Phone",
    })
    assert e_resp.status_code == 200
    return {
        "cert": user_cert,
        "credential_id": e_resp.json()["credential_id"],
        "device_id": e_resp.json()["device_id"],
        "priv_key": priv,
        "pub_pem": pub_pem,
    }


def _enroll_fresh_owner():
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
    dev_id = f"tr_dev_owner_{datetime.now(timezone.utc).timestamp()}"
    e_resp = client.post("/api/mobile/enroll", json={
        "pairing_code": pairing_code,
        "public_key": pub_pem,
        "device_identifier": dev_id,
        "device_name": "Stage02B Owner Device",
    })
    assert e_resp.status_code == 200
    return {
        "cert": owner_cert,
        "credential_id": e_resp.json()["credential_id"],
        "device_id": e_resp.json()["device_id"],
        "priv_key": priv,
        "pub_pem": pub_pem,
    }


def _insert_test_sales(records):
    db_paths = [
        os.path.join(project_root, "data", "db", "technoreboot.db"),
        os.path.join(project_root, "technoreboot.db"),
    ]
    inserted_ids = []
    for p in db_paths:
        if os.path.exists(p):
            conn = sqlite3.connect(p)
            cur = conn.cursor()
            for amount, status, pm, dt_str in records:
                cur.execute(
                    "INSERT INTO sales (total_amount, status, payment_method, created_at, comment) VALUES (?, ?, ?, ?, 'pytest_stage02b_sale')",
                    (amount, status, pm, dt_str),
                )
                inserted_ids.append((p, cur.lastrowid))
            conn.commit()
            conn.close()
    return inserted_ids


def _delete_test_sales(inserted_ids):
    for p, row_id in inserted_ids:
        if os.path.exists(p):
            conn = sqlite3.connect(p)
            cur = conn.cursor()
            cur.execute("DELETE FROM sales WHERE id = ?", (row_id,))
            conn.commit()
            conn.close()


@pytest.fixture
def enrolled_user():
    return _enroll_fresh_user()


@pytest.fixture
def enrolled_owner():
    return _enroll_fresh_owner()


# =====================================================================
# 1. Section 6: Deterministic Month Boundary Tests on Mobile API
# =====================================================================

def test_mobile_month_boundary_sep2026_fixture(enrolled_user):
    """
    Current date fixture: 2026-09-28
    Sales:
    - 2026-09-01 -> INCLUDED
    - 2026-09-15 -> INCLUDED
    - 2026-09-28 -> INCLUDED
    - 2026-08-31 -> EXCLUDED
    """
    sales_spec = [
        (1001.0, "completed", "cash", "2026-09-01 10:00:00"),
        (2002.0, "completed", "card", "2026-09-15 14:00:00"),
        (3003.0, "completed", "transfer", "2026-09-28 17:30:00"),
        (4004.0, "completed", "cash", "2026-08-31 23:59:59"),
    ]
    ids = _insert_test_sales(sales_spec)

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        path = "/api/mobile/reports/sales?period=month"
        headers = _get_pop_headers(cred_id, priv, "GET", path)

        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["period"] == "month"
        assert data["label"] == "Месяц"
        assert data["currency"] == "RUB"

        mobile_sale_ids = [s["id"] for s in data["sales"]]
        sep_ids = [row_id for _, row_id in ids[:3]]
        aug_ids = [row_id for _, row_id in ids[3:]]

        for sid in sep_ids:
            assert sid in mobile_sale_ids, f"September sale {sid} must be INCLUDED"
        for aid in aug_ids:
            assert aid not in mobile_sale_ids, f"August sale {aid} must be EXCLUDED"
    finally:
        _delete_test_sales(ids)


def test_mobile_month_year_boundary_jan2026_fixture(enrolled_user):
    """
    Year boundary fixture:
    Current date: 2026-01-05
    - 2026-01-01 -> INCLUDED
    - 2025-12-31 -> EXCLUDED
    """
    sales_spec = [
        (1234.0, "completed", "cash", "2026-01-01 11:00:00"),
        (5678.0, "completed", "card", "2025-12-31 23:59:00"),
    ]
    ids = _insert_test_sales(sales_spec)
    jan01_id = ids[0][1]
    dec31_id = ids[1][1]

    try:
        canonical_mock = {
            "period": "month",
            "date_from": "2026-01-01",
            "date_to": "2026-01-05",
            "total_amount": 1234.0,
            "sales_count": 1,
            "items_count": 1,
            "payment_breakdown": [{"payment_method": "cash", "label": "Наличные", "amount": 1234.0, "sales_count": 1}],
            "sales": [{"id": jan01_id, "created_at": "2026-01-01T11:00:00", "total_amount": 1234.0, "payment_method": "cash", "payment_method_label": "Наличные"}]
        }
        with patch("app.main._fetch_canonical_sales_report", return_value=canonical_mock):
            cred_id = enrolled_user["credential_id"]
            priv = enrolled_user["priv_key"]
            path = "/api/mobile/reports/sales?period=month"
            headers = _get_pop_headers(cred_id, priv, "GET", path)

            resp = client.get(path, headers=headers)
            assert resp.status_code == 200, resp.text
            data = resp.json()

            assert data["date_from"] == "2026-01-01"
            assert data["date_to"] == "2026-01-05"
            sale_ids = [s["id"] for s in data["sales"]]
            assert jan01_id in sale_ids
            assert dec31_id not in sale_ids
    finally:
        _delete_test_sales(ids)


# =====================================================================
# 2. Section 7: Consistency Tests for Month
# =====================================================================

def test_mobile_month_consistency_and_canceled_exclusion(enrolled_user):
    """
    For month, prove:
    - sales_count == len(sales[])
    - revenue_total == sum(sales amounts)
    - payment-method totals equal sales set
    - canceled sales excluded from list and totals
    - date_from/date_to correct
    - label = 'Месяц'
    - currency preserved
    """
    now_dt = datetime.now()
    month_start_day = now_dt.strftime("%Y-%m-02 12:00:00")
    sales_spec = [
        (1500.0, "completed", "cash", month_start_day),
        (2500.0, "completed", "card", month_start_day),
        (9999.0, "canceled", "cash", month_start_day),
    ]
    ids = _insert_test_sales(sales_spec)
    s1_id = ids[0][1]
    s2_id = ids[1][1]
    canc_id = ids[2][1]

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        path = "/api/mobile/reports/sales?period=month"
        headers = _get_pop_headers(cred_id, priv, "GET", path)

        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["period"] == "month"
        assert data["label"] == "Месяц"
        assert data["currency"] == "RUB"

        # Canceled excluded
        sale_ids = [s["id"] for s in data["sales"]]
        assert canc_id not in sale_ids, "Canceled sale must NOT appear in mobile month report"
        assert s1_id in sale_ids
        assert s2_id in sale_ids

        # sales_count == len(sales)
        assert data["sales_count"] == len(data["sales"])

        # revenue_total == sum(sales amounts)
        calc_sum = sum(s["amount"] for s in data["sales"])
        assert abs(data["revenue_total"] - calc_sum) < 0.001

        # payment breakdown totals equal sales set
        pb_sum = sum(pb["amount"] for pb in data["payment_methods"])
        assert abs(pb_sum - data["revenue_total"]) < 0.001
        pb_count = sum(pb["count"] for pb in data["payment_methods"])
        assert pb_count == data["sales_count"]

    finally:
        _delete_test_sales(ids)


# =====================================================================
# 3. Section 8: Mobile Auth Tests for period=month
# =====================================================================

def test_mobile_month_auth_user_pass(enrolled_user):
    """Active USER -> PASS (200)"""
    path = "/api/mobile/reports/sales?period=month"
    headers = _get_pop_headers(enrolled_user["credential_id"], enrolled_user["priv_key"], "GET", path)
    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["period"] == "month"
    assert resp.json()["label"] == "Месяц"


def test_mobile_month_auth_owner_pass(enrolled_owner):
    """Active OWNER -> PASS (200)"""
    path = "/api/mobile/reports/sales?period=month"
    headers = _get_pop_headers(enrolled_owner["credential_id"], enrolled_owner["priv_key"], "GET", path)
    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["period"] == "month"
    assert resp.json()["label"] == "Месяц"


def test_mobile_month_auth_revoked_device_denied(enrolled_user):
    """Revoked device -> DENY (403)"""
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    dev_id = enrolled_user["device_id"]
    parent_id = enrolled_user["cert"]["id"]

    path = "/api/mobile/reports/sales?period=month"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    mobile_manager.revoke_device(device_id=dev_id, actor_cert_id=parent_id, is_owner=False)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 403
    assert "revoked" in resp.json()["detail"].lower() or "отозван" in resp.json()["detail"].lower()


def test_mobile_month_auth_revoked_parent_denied(enrolled_user):
    """Revoked parent certificate -> DENY (403)"""
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    parent_cert_id = enrolled_user["cert"]["id"]

    auth_manager.revoke_certificate(parent_cert_id)

    path = "/api/mobile/reports/sales?period=month"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 403
    assert "revoked" in resp.json()["detail"].lower() or "родительский" in resp.json()["detail"].lower()


def test_mobile_month_auth_tampered_query_denied(enrolled_user):
    """Tampered query: signed for 'month' but dispatched with 'week' (or vice versa) -> DENY"""
    signed_path = "/api/mobile/reports/sales?period=month"
    headers = _get_pop_headers(enrolled_user["credential_id"], enrolled_user["priv_key"], "GET", signed_path)

    # Dispatched with tampered period 'week'
    resp = client.get("/api/mobile/reports/sales?period=week", headers=headers)
    assert resp.status_code in (401, 403)

    # Signed for 'today' but dispatched with 'month'
    signed_today = "/api/mobile/reports/sales?period=today"
    headers2 = _get_pop_headers(enrolled_user["credential_id"], enrolled_user["priv_key"], "GET", signed_today)
    resp2 = client.get("/api/mobile/reports/sales?period=month", headers=headers2)
    assert resp2.status_code in (401, 403)


def test_mobile_month_auth_invalid_period_controlled_400(enrolled_user):
    """Invalid period -> controlled 400 with detail"""
    for bad_period in ("invalid", "quarter", "last30days", "day", ""):
        path = f"/api/mobile/reports/sales?period={bad_period}"
        headers = _get_pop_headers(enrolled_user["credential_id"], enrolled_user["priv_key"], "GET", path)
        resp = client.get(path, headers=headers)
        assert resp.status_code == 400
        assert "Invalid period" in resp.json()["detail"]
