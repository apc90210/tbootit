"""
Stage 06B Admin-Shell Mobile Sales Reports Drill-down Integration Tests.
Verifies:
1. /api/mobile/reports/sales strictly enforces TRMOBILE1 PoP authentication.
2. Today transition: summary + receipts list.
3. Week transition: week summary + days list with sales, amounts, and payment breakdown.
4. Month transition: month summary + days list directly (NO week level), amounts and counts invariant.
5. Year transition: year summary + months list with amounts and payment breakdown.
6. Month drill-down: date_from/date_to for a month returns days list matching month summary.
7. Day drill-down: date_from=date_to for a day returns exact receipts list matching day summary.
8. Mathematical invariants: sum(children.amount) == parent.amount, sum(children.count) == parent.count.
9. Validation: 400 on invalid period or malformed date strings.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
import base64
import urllib.parse

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
    sig = _sign_payload(priv, payload_bytes)
    return {
        "x-mobile-credential-id": credential_id,
        "x-mobile-nonce": nonce,
        "x-mobile-signature": sig,
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
def enrolled_user():
    priv, cred_id = _enroll_device("owner", "test-dev-stage06b-001", "Stage06B Test Phone")
    return {
        "credential_id": cred_id,
        "priv_key": priv,
    }


def test_01_pop_auth_enforced_on_reports_sales():
    resp = client.get("/api/mobile/reports/sales?period=today")
    assert resp.status_code == 401


def test_02_today_scheme(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/reports/sales?period=today"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["period"] == "today"
    assert "revenue_total" in data
    assert "sales_count" in data
    assert "payment_methods" in data
    assert "sales" in data
    assert "days" in data
    assert "months" in data

    # Check payment methods match revenue
    pm_sum = round(sum(pm["amount"] for pm in data["payment_methods"]), 2)
    assert abs(pm_sum - round(data["revenue_total"], 2)) < 0.01


def test_03_week_scheme_days_list(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/reports/sales?period=week"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["period"] == "week"
    assert "days" in data
    days = data["days"]

    # Invariants for week
    if days:
        day_amount_sum = round(sum(d["amount"] for d in days), 2)
        day_count_sum = sum(d["sales_count"] for d in days)
        assert abs(day_amount_sum - round(data["revenue_total"], 2)) < 0.01
        assert day_count_sum == data["sales_count"]

        # Check each day has required fields
        for d in days:
            assert "date" in d
            assert "label" in d
            assert "day_of_week" in d
            assert "amount" in d
            assert "sales_count" in d
            assert "payment_methods" in d


def test_04_month_scheme_direct_days_no_weeks(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/reports/sales?period=month"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["period"] == "month"
    assert "days" in data
    assert "weeks" not in data  # STRICT REQUIREMENT: NO WEEKS IN MONTH

    days = data["days"]
    assert len(days) >= 1  # October has sales on 01.10 and 02.10

    # Invariant: sum of days = month total
    day_amount_sum = round(sum(d["amount"] for d in days), 2)
    day_count_sum = sum(d["sales_count"] for d in days)
    assert abs(day_amount_sum - round(data["revenue_total"], 2)) < 0.01
    assert day_count_sum == data["sales_count"]

    # Invariant: each day payment methods sum = day amount
    for d in days:
        d_pm_sum = round(sum(pm["amount"] for pm in d["payment_methods"]), 2)
        assert abs(d_pm_sum - round(d["amount"], 2)) < 0.01


def test_05_year_scheme_months_level(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/reports/sales?period=year"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["period"] == "year"
    assert "months" in data
    months = data["months"]
    assert len(months) >= 2  # Has October and September 2026

    # Invariant: sum of months = year total
    month_amount_sum = round(sum(m["amount"] for m in months), 2)
    month_count_sum = sum(m["sales_count"] for m in months)
    assert abs(month_amount_sum - round(data["revenue_total"], 2)) < 0.01
    assert month_count_sum == data["sales_count"]

    for m in months:
        assert "month_key" in m
        assert "label" in m
        assert "amount" in m
        assert "sales_count" in m
        assert "payment_methods" in m
        m_pm_sum = round(sum(pm["amount"] for pm in m["payment_methods"]), 2)
        assert abs(m_pm_sum - round(m["amount"], 2)) < 0.01


def test_06_drilldown_month_to_days(enrolled_user):
    # Drill-down into September 2026: 2026-09-01 to 2026-09-30
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    # Query parameters must be sorted lexicographically: date_from, date_to, period
    canonical_path = "/api/mobile/reports/sales?date_from=2026-09-01&date_to=2026-09-30&period=custom"
    headers = _get_pop_headers(cred_id, priv, "GET", canonical_path)

    resp = client.get(canonical_path, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["sales_count"] == 57
    assert data["revenue_total"] == 251280.0
    assert "days" in data
    assert len(data["days"]) > 0

    # Invariant: sum of days = September total
    day_amount_sum = round(sum(d["amount"] for d in data["days"]), 2)
    day_count_sum = sum(d["sales_count"] for d in data["days"])
    assert abs(day_amount_sum - 251280.0) < 0.01
    assert day_count_sum == 57


def test_07_drilldown_day_to_receipts(enrolled_user):
    # Drill-down into specific day: 2026-10-01
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    # Sorted query params: date_from, date_to, period
    canonical_path = "/api/mobile/reports/sales?date_from=2026-10-01&date_to=2026-10-01&period=custom"
    headers = _get_pop_headers(cred_id, priv, "GET", canonical_path)

    resp = client.get(canonical_path, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["sales_count"] == 4
    assert data["revenue_total"] == 14500.0
    assert len(data["sales"]) == 4

    # Invariant: receipts sum == day total
    receipt_sum = round(sum(s["amount"] for s in data["sales"]), 2)
    assert abs(receipt_sum - 14500.0) < 0.01


def test_08_invalid_queries_validation(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]

    # 1. Invalid period
    p1 = "/api/mobile/reports/sales?period=decade"
    h1 = _get_pop_headers(cred_id, priv, "GET", p1)
    r1 = client.get(p1, headers=h1)
    assert r1.status_code == 400

    # 2. Invalid date_from
    p2 = "/api/mobile/reports/sales?date_from=invalid-date&date_to=2026-10-01&period=custom"
    h2 = _get_pop_headers(cred_id, priv, "GET", p2)
    r2 = client.get(p2, headers=h2)
    assert r2.status_code == 400
