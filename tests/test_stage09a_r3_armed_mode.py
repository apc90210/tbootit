import os
import sys
import json
import sqlite3
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent

# Clean sys.path and sys.modules for admin-shell import
for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        mod = sys.modules[k]
        if hasattr(mod, "__file__") and mod.__file__ and "admin-shell" not in mod.__file__:
            sys.modules.pop(k, None)

admin_shell_path = str(REPO_ROOT / "admin-shell")
if admin_shell_path in sys.path:
    sys.path.remove(admin_shell_path)
sys.path.insert(0, admin_shell_path)

import app.main as admin_main
app = admin_main.app
auth_manager = admin_main.auth_manager
client = TestClient(app)

DB_PATH = REPO_ROOT / "data" / "db" / "technoreboot.db"

@pytest.fixture
def owner_headers():
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": "1001",
        "x-auth-subject": "Technoreboot Owner",
        "x-auth-is-owner": "true"
    }

def test_stage09a_r3_armed_contract_and_security(owner_headers):
    """Verify Section 13 Armed mode requirements: approved task, domain blocking, auto-disarm."""
    # 1. Armed API Endpoints via Admin-Shell Gateway
    disarm_resp = client.post("/admin-api/avito-extension/disarm", headers=owner_headers)
    assert disarm_resp.status_code == 200
    assert disarm_resp.json()["armed_listing_id"] is None
    assert disarm_resp.json()["mode"] == "dry_run"

    # Status check
    status_resp = client.get("/admin-api/avito-extension/armed-status", headers=owner_headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["armed"] is False

    # Arm specifically for approved Avito ID 7353766377
    arm_resp = client.post("/admin-api/avito-extension/arm-task/7353766377", headers=owner_headers)
    assert arm_resp.status_code == 200
    assert arm_resp.json()["armed_listing_id"] == "7353766377"

    status_resp2 = client.get("/admin-api/avito-extension/armed-status", headers=owner_headers)
    assert status_resp2.json()["armed"] is True
    assert status_resp2.json()["armed_listing_id"] == "7353766377"

    # Reset with disarm
    disarm_resp2 = client.post("/admin-api/avito-extension/disarm", headers=owner_headers)
    assert disarm_resp2.status_code == 200
    assert disarm_resp2.json()["armed_listing_id"] is None



def test_stage09a_r3_extension_service_worker_contract():
    """Verify Service Worker script enforces dry-run auto-restoration and dual action tolerance."""
    sw_path = os.path.join(REPO_ROOT, "chrome-extension", "technoreboot-avito", "service_worker.js")
    with open(sw_path, "r", encoding="utf-8") as f:
        sw_code = f.read()

    # Must contain armed listing helpers
    assert "getArmedListingId" in sw_code
    assert "setArmedListingId" in sw_code
    assert "arm_specific_listing" in sw_code
    assert "approved_for_real_execution" in sw_code

    # Must contain auto-restoration of dry-run mode
    assert "setDryRunMode(true)" in sw_code
    assert "setArmedListingId(null)" in sw_code

    # Must accept both actions
    assert '"deactivate_listing"' in sw_code
    assert '"deactivate"' in sw_code
    assert "Unsupported action:" in sw_code


def test_stage09a_r3_extension_content_script_contract():
    """Verify Content Script enforces external inactive confirmation and modal handling."""
    cs_path = os.path.join(REPO_ROOT, "chrome-extension", "technoreboot-avito", "content.js")
    with open(cs_path, "r", encoding="utf-8") as f:
        cs_code = f.read()

    assert "extractAvitoItemId" in cs_code
    assert "handleDeactivationModalIfPresent" in cs_code
    assert "waitForConfirmedInactiveState" in cs_code
    assert "checkListingAlreadyInactive" in cs_code
    assert "продал на авито" in cs_code
    assert "inactive_state_confirmed" in cs_code
    assert "showDryRunPageBanner" in cs_code


def test_stage09a_r3_server_success_post_conditions():
    """Verify server task, listing, and business state integrity in local SQLite DB."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    try:
        # Check Task #2 in DB
        task = cur.execute("SELECT id, sale_id, product_id, avito_listing_id, action FROM avito_post_sale_tasks WHERE id = 2").fetchone()
        assert task is not None
        assert task[3] == "7353766377"

        # Check linked listing in product_external_listings
        listing = cur.execute("SELECT id, product_id, external_item_id, remote_status FROM product_external_listings WHERE external_item_id = '7353766377'").fetchone()
        assert listing is not None
        assert listing[1] == task[2]

        # Verify sale #1 integrity
        sale = cur.execute("SELECT id, total_amount, payment_method FROM sales WHERE id = 1").fetchone()
        assert sale is not None
        assert sale[1] > 0

        # Verify product #141 integrity
        product = cur.execute("SELECT id, title, quantity FROM products WHERE id = ?", (task[2],)).fetchone()
        assert product is not None
    finally:
        conn.close()
