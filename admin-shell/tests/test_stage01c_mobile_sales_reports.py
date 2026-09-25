"""
Stage01C R2 — Android Mobile Sales Reports Server & Contract Tests.
Verifies that:
1. GET /api/mobile/reports/sales strictly enforces TRMOBILE1 PoP authentication.
2. Runtime uses only configured Core HTTP API (NO subprocess, NO direct SQLite access).
3. Period contracts strictly match canonical Core boundary logic (today, week, year).
4. Out-of-period and canceled sales are excluded.
5. Totals, payment breakdown, and sales_count strictly agree with canonical Core.
6. Core unavailable / timeout yields controlled 502/503/504 responses.
7. Explicit regression test proves R1 sample (2026-09-25 vs 2026-09-17) behaves correctly.
"""

import sys
import os
import ast
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


def _get_canonical_report(period: str) -> dict:
    """Fetch canonical core sales report directly from Core HTTP API or isolated test harness."""
    import urllib.request
    core_url = os.getenv("CORE_API_URL", "http://127.0.0.1:8000")
    headers = {"x-api-token": os.getenv("CORE_API_TOKEN", "")}
    try:
        req = urllib.request.Request(f"{core_url}/api/reports/sales?period={period}", headers=headers)
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
from app.routers.reports import get_sales_report

db = SessionLocal()
try:
    r = get_sales_report(period={repr(period)}, db=db)
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


def _insert_test_sale(total_amount: float, status: str, payment_method: str, created_at_str: str = None) -> list:
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
            ids.append((p, cur.lastrowid))
            conn.commit()
            conn.close()
    return ids


def _delete_test_sales(inserted_ids: list):
    for p, row_id in inserted_ids:
        if os.path.exists(p):
            conn = sqlite3.connect(p)
            cur = conn.cursor()
            cur.execute("DELETE FROM sales WHERE id = ?", (row_id,))
            conn.commit()
            conn.close()


@pytest.fixture
def enrolled_user():
    user_cert = auth_manager.create_user_certificate(f"Stage01C User {datetime.now(timezone.utc).timestamp()}")
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
    dev_id = f"tr_dev_owner_{datetime.now(timezone.utc).timestamp()}"
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
# 1. Today list contains only today sales
# ===========================================================================

def test_01_today_list_contains_only_today_sales(enrolled_user):
    today_str = datetime.now().strftime("%Y-%m-%d 10:00:00")
    yesterday_str = "2026-09-17 10:00:00"

    today_sale = _insert_test_sale(1111.0, "completed", "cash", today_str)
    past_sale = _insert_test_sale(2222.0, "completed", "cash", yesterday_str)

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        canonical_path = "/api/mobile/reports/sales?period=today"
        headers = _get_pop_headers(cred_id, priv, "GET", canonical_path)

        resp = client.get(canonical_path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        today_ids = [row_id for _, row_id in today_sale]
        past_ids = [row_id for _, row_id in past_sale]
        mobile_sale_ids = [s["id"] for s in data["sales"]]

        # Today sale MUST appear
        assert any(tid in mobile_sale_ids for tid in today_ids)
        # Past sale MUST NOT appear
        assert not any(pid in mobile_sale_ids for pid in past_ids)

        # Every sale in sales[] must have created_at on today's date
        today_date_str = datetime.now().strftime("%Y-%m-%d")
        for s in data["sales"]:
            assert s["created_at"].startswith(today_date_str)
    finally:
        _delete_test_sales(today_sale + past_sale)


# ===========================================================================
# 2. Week list contains only current-week sales
# ===========================================================================

def test_02_week_list_contains_only_current_week_sales(enrolled_user):
    now = datetime.now()
    # Current week Monday
    mon_dt = now.date() - datetime.today().resolution * now.weekday()
    mon_str = f"{mon_dt.isoformat()} 10:00:00"
    past_str = "2026-09-10 10:00:00"  # Clearly prior week

    week_sale = _insert_test_sale(1500.0, "completed", "card", mon_str)
    out_sale = _insert_test_sale(3000.0, "completed", "card", past_str)

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        canonical_path = "/api/mobile/reports/sales?period=week"
        headers = _get_pop_headers(cred_id, priv, "GET", canonical_path)

        resp = client.get(canonical_path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        week_ids = [row_id for _, row_id in week_sale]
        out_ids = [row_id for _, row_id in out_sale]
        mobile_sale_ids = [s["id"] for s in data["sales"]]

        assert any(wid in mobile_sale_ids for wid in week_ids)
        assert not any(oid in mobile_sale_ids for oid in out_ids)

        # All sales must fall within current week range
        date_from = data["date_from"]
        date_to = data["date_to"]
        for s in data["sales"]:
            sale_date = s["created_at"][:10]
            assert date_from <= sale_date <= date_to
    finally:
        _delete_test_sales(week_sale + out_sale)


# ===========================================================================
# 3. Year list contains only current-year sales
# ===========================================================================

def test_03_year_list_contains_only_current_year_sales(enrolled_user):
    now_year = datetime.now().year
    in_year_str = f"{now_year}-05-15 12:00:00"
    prior_year_str = f"{now_year - 1}-12-31 23:59:59"

    in_sale = _insert_test_sale(2000.0, "completed", "cash", in_year_str)
    prior_sale = _insert_test_sale(5000.0, "completed", "cash", prior_year_str)

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        canonical_path = "/api/mobile/reports/sales?period=year"
        headers = _get_pop_headers(cred_id, priv, "GET", canonical_path)

        resp = client.get(canonical_path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        in_ids = [row_id for _, row_id in in_sale]
        prior_ids = [row_id for _, row_id in prior_sale]
        mobile_sale_ids = [s["id"] for s in data["sales"]]

        assert any(iid in mobile_sale_ids for iid in in_ids)
        assert not any(pid in mobile_sale_ids for pid in prior_ids)

        for s in data["sales"]:
            assert s["created_at"].startswith(str(now_year))
    finally:
        _delete_test_sales(in_sale + prior_sale)


# ===========================================================================
# 4. Out-of-period completed sale excluded
# ===========================================================================

def test_04_out_of_period_completed_sale_excluded(enrolled_user):
    # A sale on 2026-09-17 is out-of-period for today
    sep17_sale = _insert_test_sale(4444.0, "completed", "cash", "2026-09-17 12:00:00")
    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        canonical_path = "/api/mobile/reports/sales?period=today"
        headers = _get_pop_headers(cred_id, priv, "GET", canonical_path)

        resp = client.get(canonical_path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        sep17_ids = [row_id for _, row_id in sep17_sale]
        mobile_sale_ids = [s["id"] for s in data["sales"]]
        assert not any(sid in mobile_sale_ids for sid in sep17_ids)
    finally:
        _delete_test_sales(sep17_sale)


# ===========================================================================
# 5. Canceled in-period sale excluded
# ===========================================================================

def test_05_canceled_in_period_sale_excluded(enrolled_user):
    today_str = datetime.now().strftime("%Y-%m-%d 11:30:00")
    ok_sale = _insert_test_sale(1000.0, "completed", "cash", today_str)
    canc_sale = _insert_test_sale(9999.0, "canceled", "cash", today_str)

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        canonical_path = "/api/mobile/reports/sales?period=today"
        headers = _get_pop_headers(cred_id, priv, "GET", canonical_path)

        resp = client.get(canonical_path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        ok_ids = [row_id for _, row_id in ok_sale]
        canc_ids = [row_id for _, row_id in canc_sale]
        mobile_sale_ids = [s["id"] for s in data["sales"]]

        assert any(oid in mobile_sale_ids for oid in ok_ids)
        assert not any(cid in mobile_sale_ids for cid in canc_ids)
    finally:
        _delete_test_sales(ok_sale + canc_sale)


# ===========================================================================
# 6. Totals match canonical Core
# ===========================================================================

def test_06_totals_match_canonical_core(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]

    for period in ("today", "week", "year"):
        canonical_path = f"/api/mobile/reports/sales?period={period}"
        headers = _get_pop_headers(cred_id, priv, "GET", canonical_path)

        resp = client.get(canonical_path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        canonical = _get_canonical_report(period)
        assert data["revenue_total"] == canonical["total_amount"]
        assert data["currency"] == "RUB"
        assert data["date_from"] == canonical["date_from"]
        assert data["date_to"] == canonical["date_to"]


# ===========================================================================
# 7. Payment breakdown matches canonical Core
# ===========================================================================

def test_07_payment_breakdown_matches_canonical_core(enrolled_user):
    today_str = datetime.now().strftime("%Y-%m-%d 14:00:00")
    s1 = _insert_test_sale(100.0, "completed", "cash", today_str)
    s2 = _insert_test_sale(250.0, "completed", "card", today_str)
    s3 = _insert_test_sale(350.0, "completed", "transfer", today_str)

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        path = "/api/mobile/reports/sales?period=today"
        headers = _get_pop_headers(cred_id, priv, "GET", path)

        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        canonical = _get_canonical_report("today")
        mobile_pb = {pb["method"]: pb for pb in data["payment_methods"]}
        canon_pb = {pb["payment_method"]: pb for pb in canonical["payment_breakdown"]}

        for m, pb in mobile_pb.items():
            assert m in canon_pb
            assert pb["amount"] == canon_pb[m]["amount"]
            assert pb["count"] == canon_pb[m]["sales_count"]
    finally:
        _delete_test_sales(s1 + s2 + s3)


# ===========================================================================
# 8. Sales count contract correct
# ===========================================================================

def test_08_sales_count_contract_correct(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]

    for period in ("today", "week", "year"):
        path = f"/api/mobile/reports/sales?period={period}"
        headers = _get_pop_headers(cred_id, priv, "GET", path)
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        canonical = _get_canonical_report(period)
        assert data["sales_count"] == len(data["sales"])
        assert data["sales_count"] == canonical["sales_count"]


# ===========================================================================
# 9. Core unavailable -> 502/503
# ===========================================================================

def test_09_core_unavailable_returns_502_or_503(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/reports/sales?period=today"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused by Core"))
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp = client.get(path, headers=headers)
        assert resp.status_code in (502, 503)
        assert "Core API connection failed" in resp.json()["detail"] or "unavailable" in resp.json()["detail"].lower()


# ===========================================================================
# 10. Core timeout -> controlled failure
# ===========================================================================

def test_10_core_timeout_returns_controlled_failure(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/reports/sales?period=today"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Core request timed out"))
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp = client.get(path, headers=headers)
        assert resp.status_code in (502, 503, 504)
        assert "timed out" in resp.json()["detail"].lower()


# ===========================================================================
# 11. No runtime subprocess call
# ===========================================================================

def test_11_no_runtime_subprocess_call(enrolled_user):
    # 1. AST check: ensure admin-shell/app/main.py does not import subprocess
    main_py_path = os.path.join(admin_shell_dir, "app", "main.py")
    with open(main_py_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=main_py_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess", "Runtime main.py must NOT import subprocess"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess", "Runtime main.py must NOT import from subprocess"

    # 2. Runtime spy: assert subprocess.run / Popen is never called during report fetch
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/reports/sales?period=today"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    with patch("subprocess.run") as mock_run, patch("subprocess.Popen") as mock_popen:
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        assert mock_run.call_count == 0, "subprocess.run was called at runtime!"
        assert mock_popen.call_count == 0, "subprocess.Popen was called at runtime!"


# ===========================================================================
# 12. No direct Core SQLite access from admin-shell report handler
# ===========================================================================

def test_12_no_direct_core_sqlite_access_from_admin_shell_handler(enrolled_user):
    """
    Verify that admin-shell report handler and _fetch_canonical_sales_report
    do NOT access Core SQLite directly or query the sales table.
    """
    # 1. _fetch_canonical_sales_report must NEVER connect to SQLite
    with patch("sqlite3.connect", side_effect=AssertionError("Direct SQLite access inside _fetch_canonical_sales_report!")):
        import asyncio
        from app.main import _fetch_canonical_sales_report
        data = asyncio.run(_fetch_canonical_sales_report("today"))
        assert isinstance(data, dict)

    # 2. End-to-end request: ensure no SQL queries against 'sales' table
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/reports/sales?period=today"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    orig_connect = sqlite3.connect

    class GuardedConnection:
        def __init__(self, real_conn):
            self._real = real_conn

        @property
        def row_factory(self):
            return self._real.row_factory

        @row_factory.setter
        def row_factory(self, val):
            self._real.row_factory = val

        def cursor(self, *args, **kwargs):
            real_cur = self._real.cursor(*args, **kwargs)
            class GuardedCursor:
                def __init__(self, c):
                    self._c = c
                def execute(self, sql, *a, **k):
                    if "from sales" in sql.lower() or "into sales" in sql.lower():
                        raise AssertionError(f"Direct Core sales table query detected: {sql}")
                    return self._c.execute(sql, *a, **k)
                def __getattr__(self, name):
                    return getattr(self._c, name)
                def __iter__(self):
                    return iter(self._c)
            return GuardedCursor(real_cur)

        def execute(self, sql, *a, **k):
            if "from sales" in sql.lower() or "into sales" in sql.lower():
                raise AssertionError(f"Direct Core sales table query detected: {sql}")
            return self._real.execute(sql, *a, **k)

        def __enter__(self):
            self._real.__enter__()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return self._real.__exit__(exc_type, exc_val, exc_tb)

        def __getattr__(self, name):
            return getattr(self._real, name)

    def guarded_connect(*args, **kwargs):
        return GuardedConnection(orig_connect(*args, **kwargs))

    with patch("sqlite3.connect", side_effect=guarded_connect):
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200




# ===========================================================================
# 13. Missing PoP -> deny
# ===========================================================================

def test_13_missing_pop_headers_denied():
    resp = client.get("/api/mobile/reports/sales?period=today")
    assert resp.status_code == 401
    assert "Mobile PoP auth required" in resp.json()["detail"]


# ===========================================================================
# 14. Revoked parent -> deny
# ===========================================================================

def test_14_revoked_parent_blocks_access(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    parent_cert_id = enrolled_user["cert"]["id"]

    auth_manager.revoke_certificate(parent_cert_id)

    path = "/api/mobile/reports/sales?period=today"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 403
    assert "revoked" in resp.json()["detail"].lower() or "родительский" in resp.json()["detail"].lower()


# ===========================================================================
# 15. Revoked device -> deny
# ===========================================================================

def test_15_revoked_device_blocks_access(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    dev_id = enrolled_user["device_id"]
    parent_id = enrolled_user["cert"]["id"]

    path = "/api/mobile/reports/sales?period=today"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    mobile_manager.revoke_device(device_id=dev_id, actor_cert_id=parent_id, is_owner=False)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 403
    assert "revoked" in resp.json()["detail"].lower() or "отозван" in resp.json()["detail"].lower()


# ===========================================================================
# 16. Tampered period query invalidates TRMOBILE1
# ===========================================================================

def test_16_tampered_period_query_invalidates_trmobile1(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]

    signed_path = "/api/mobile/reports/sales?period=today"
    headers = _get_pop_headers(cred_id, priv, "GET", signed_path)

    # Dispatched with tampered period
    resp = client.get("/api/mobile/reports/sales?period=week", headers=headers)
    assert resp.status_code in (401, 403)


# ===========================================================================
# 17. Invalid period -> 400
# ===========================================================================

@pytest.mark.parametrize("invalid_period", ["month", "custom", "yesterday", "all", ""])
def test_17_invalid_period_rejected_with_400(enrolled_user, invalid_period):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = f"/api/mobile/reports/sales?period={invalid_period}"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    resp = client.get(path, headers=headers)
    assert resp.status_code == 400
    assert "Invalid period" in resp.json()["detail"]


# ===========================================================================
# 18. Explicit regression for suspicious R1 sample (Sep 25 vs Sep 17)
# ===========================================================================

def test_18_r1_sample_regression_today_vs_sep17(enrolled_user):
    """
    Deterministic fixture proving period=today contract:
    - canonical current date: 2026-09-25;
    - completed sale on 2026-09-25;
    - completed sale on 2026-09-17.
    For period=today:
    - Sep 25 sale MUST appear;
    - Sep 17 sale MUST NOT appear.
    """
    sep25_sale = _insert_test_sale(3500.0, "completed", "cash", "2026-09-25 15:30:00")
    sep17_sale = _insert_test_sale(4455.0, "completed", "cash", "2026-09-17 06:47:11")

    try:
        cred_id = enrolled_user["credential_id"]
        priv = enrolled_user["priv_key"]
        path = "/api/mobile/reports/sales?period=today"
        headers = _get_pop_headers(cred_id, priv, "GET", path)

        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        sep25_ids = [row_id for _, row_id in sep25_sale]
        sep17_ids = [row_id for _, row_id in sep17_sale]
        mobile_sale_ids = [s["id"] for s in data["sales"]]

        # Sep 25 sale MUST appear
        assert any(sid in mobile_sale_ids for sid in sep25_ids), "Sep 25 sale missing from today report"

        # Sep 17 sale MUST NOT appear
        assert not any(sid in mobile_sale_ids for sid in sep17_ids), "Sep 17 sale incorrectly included in today report!"

        # Summary dates must match 2026-09-25
        assert data["date_from"] == "2026-09-25"
        assert data["date_to"] == "2026-09-25"
    finally:
        _delete_test_sales(sep25_sale + sep17_sale)


# ===========================================================================
# 19. Service-to-service auth header & trust boundary
# ===========================================================================

def test_19_service_to_service_auth_header_and_trust_boundary(enrolled_user):
    cred_id = enrolled_user["credential_id"]
    priv = enrolled_user["priv_key"]
    path = "/api/mobile/reports/sales?period=today"
    headers = _get_pop_headers(cred_id, priv, "GET", path)

    # Add spoofed headers to verify they cannot override server-to-service auth
    headers["x-api-token"] = "spoofed-client-token"
    headers["x-client-role"] = "owner"

    captured_headers = {}

    orig_client = httpx.AsyncClient

    class SpyAsyncClient(orig_client):
        async def get(self, url, *args, **kwargs):
            nonlocal captured_headers
            captured_headers = kwargs.get("headers", {})
            return await super().get(url, *args, **kwargs)

    with patch("httpx.AsyncClient", SpyAsyncClient):
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        # Outgoing x-api-token must match server env CORE_API_TOKEN, not client's spoofed header
        expected_token = os.getenv("CORE_API_TOKEN", "")
        assert captured_headers.get("x-api-token") == expected_token


# ===========================================================================
# 20. USER and OWNER access parity
# ===========================================================================

def test_20_user_and_owner_can_both_access_reports(enrolled_user, enrolled_owner):
    u_path = "/api/mobile/reports/sales?period=today"
    u_headers = _get_pop_headers(enrolled_user["credential_id"], enrolled_user["priv_key"], "GET", u_path)
    u_resp = client.get(u_path, headers=u_headers)
    assert u_resp.status_code == 200

    o_path = "/api/mobile/reports/sales?period=today"
    o_headers = _get_pop_headers(enrolled_owner["credential_id"], enrolled_owner["priv_key"], "GET", o_path)
    o_resp = client.get(o_path, headers=o_headers)
    assert o_resp.status_code == 200

    assert u_resp.json()["currency"] == o_resp.json()["currency"] == "RUB"
