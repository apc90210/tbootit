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
    print("\n[Step 3] Verifying product Draft transition workflow: GET /api/products/")
    r_prods = client.get(f"{BASE_URL}/api/products/?limit=1")
    assert r_prods.status_code == 200, f"Products fetch failed: {r_prods.status_code}"
    items = r_prods.json().get("items", [])
    if items:
        p = items[0]
        pid = p["id"]
        orig_status = p.get("status", "in_stock")
        print(f"  Selected Product ID {pid} (current status: '{orig_status}')")

        # Move to draft
        print("  Moving product to 'draft'...")
        r_to_draft = client.post(f"{BASE_URL}/api/products/{pid}/status", json={"status": "draft"})
        assert r_to_draft.status_code == 200, f"Failed moving to draft: {r_to_draft.status_code} {r_to_draft.text}"
        assert r_to_draft.json().get("status") == "draft"
        print("  [PASS] Product successfully moved to 'draft'")

        # Restore back to original status
        print(f"  Restoring product back to '{orig_status}'...")
        r_restore = client.post(f"{BASE_URL}/api/products/{pid}/status", json={"status": orig_status})
        assert r_restore.status_code == 200, f"Failed restoring status: {r_restore.status_code} {r_restore.text}"
        assert r_restore.json().get("status") == orig_status
        print(f"  [PASS] Product successfully restored to '{orig_status}'")
    else:
        print("  [SKIP] No products present to test status transition on VDS")

# 4. Check business data counts on VDS
print("\n[Step 4] Verifying business data counts on VDS...")
check_cmd = [
    "ssh", "-i", r"C:\Users\Apc\.ssh\id_ed25519", "root@144.31.50.134",
    "sqlite3 /srv/technoreboot/data/db/technoreboot.db \"SELECT 'PRODUCTS=' || count(*) FROM products; SELECT 'SALES=' || count(*) FROM sales; SELECT 'REPAIRS=' || count(*) FROM repairs;\""
]
res = subprocess.run(check_cmd, capture_output=True, text=True, check=True)
counts = res.stdout.strip().replace("\n", " ")
print(f"  Live VDS Counts: {counts}")
assert "PRODUCTS=149" in counts
assert "SALES=0" in counts
assert "REPAIRS=0" in counts
print("  [PASS] Production business data strictly preserved!")

print("\n==================================================================")
print("ALL LIVE VDS VERIFICATIONS PASSED!")
print("==================================================================")
