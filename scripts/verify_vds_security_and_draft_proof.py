import ssl
import json
import httpx
import subprocess
from pathlib import Path

BASE_URL = "https://144.31.50.134"
AUTH_DIR = Path(r"C:\tbootit\data\auth\certificates")
OWNER_CERT = (str(AUTH_DIR / "owner.crt"), str(AUTH_DIR / "owner.key"))

print("==================================================================")
print("STAGE 08D-R1R4: LIVE VDS SECURITY, RBAC & DRAFT VERIFICATION")
print("Target:", BASE_URL)
print("==================================================================")

with httpx.Client(cert=OWNER_CERT, verify=True, timeout=15.0, trust_env=False) as client:
    # 1. Owner dashboard verification
    print("\n[Step 1] Loading dashboard with Owner certificate: GET /")
    r_dash = client.get(f"{BASE_URL}/")
    assert r_dash.status_code == 200, f"Dashboard load failed: {r_dash.status_code}"
    assert "Сбросить БД" in r_dash.text, "Owner dashboard must render 'Сбросить БД'"
    assert "Заполнить тестовыми данными" in r_dash.text, "Owner dashboard must render 'Заполнить тестовыми данными'"
    assert 'href="/backups"' in r_dash.text, "Owner dashboard must render backups link"
    assert 'href="/certificates"' in r_dash.text, "Owner dashboard must render certificates link"
    print("  [PASS] Owner dashboard renders all administrative controls and links")

    # 2. Production dev-reset guard verification
    print("\n[Step 2] Attempting dev-reset on production VDS with Owner certificate: POST /admin-api/dev-reset")
    r_reset = client.post(f"{BASE_URL}/admin-api/dev-reset")
    assert r_reset.status_code == 403, f"Expected 403 Forbidden, got {r_reset.status_code}: {r_reset.text}"
    detail = r_reset.json().get("detail", "")
    assert "strictly forbidden in production" in detail or "disabled in production" in detail, f"Unexpected detail: {detail}"
    print(f"  [PASS] Production guard blocked dev-reset: HTTP 403 '{detail}'")

    # 3. Product Draft transition workflow on production VDS
    print("\n[Step 3] Verifying product Draft transition workflow: PATCH /admin-api/products/1/status")
    # Fetch product 1 details
    r_det = client.get(f"{BASE_URL}/admin-api/products/1/details")
    assert r_det.status_code == 200, f"Failed getting details: {r_det.status_code} {r_det.text}"
    p_data = r_det.json()
    orig_status = p_data.get("status", "in_stock")
    print(f"  Product 1 current status: '{orig_status}'")

    # Move product to draft
    print("  Moving Product 1 to 'draft'...")
    r_draft = client.patch(f"{BASE_URL}/admin-api/products/1/status", json={"status": "draft"})
    assert r_draft.status_code == 200, f"Failed moving to draft: {r_draft.status_code} {r_draft.text}"
    assert r_draft.json().get("status") == "draft"
    print("  [PASS] Product 1 successfully transitioned to 'draft'")

    # Restore back to original status
    print(f"  Restoring Product 1 back to '{orig_status}'...")
    r_restore = client.patch(f"{BASE_URL}/admin-api/products/1/status", json={"status": orig_status})
    assert r_restore.status_code == 200, f"Failed restoring: {r_restore.status_code} {r_restore.text}"
    assert r_restore.json().get("status") == orig_status
    print(f"  [PASS] Product 1 successfully restored to '{orig_status}'")

# 4. Check business data counts on VDS
print("\n[Step 4] Verifying business data counts on VDS...")
py_cmd = (
    "python3 -c \""
    "import sqlite3; "
    "conn = sqlite3.connect('/srv/technoreboot/data/db/technoreboot.db'); "
    "cur = conn.cursor(); "
    "p = cur.execute('SELECT COUNT(*) FROM products').fetchone()[0]; "
    "s = cur.execute('SELECT COUNT(*) FROM sales').fetchone()[0]; "
    "r = cur.execute('SELECT COUNT(*) FROM repair_orders').fetchone()[0]; "
    "print(f'PRODUCTS={p} SALES={s} REPAIRS={r}')"
    "\""
)
check_cmd = [
    "ssh", "-i", r"C:\Users\Apc\.ssh\id_ed25519", "root@144.31.50.134", py_cmd
]
res = subprocess.run(check_cmd, capture_output=True, text=True, check=True)
counts = res.stdout.strip()
print(f"  Live VDS Counts: {counts}")
assert "PRODUCTS=149" in counts
assert "SALES=0" in counts
assert "REPAIRS=0" in counts
print("  [PASS] Production business data strictly preserved!")

print("\n==================================================================")
print("ALL LIVE VDS VERIFICATIONS PASSED!")
print("==================================================================")
