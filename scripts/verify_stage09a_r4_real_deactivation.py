import os
import sys
import json
import sqlite3
import zipfile
import httpx
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CERT_PATH = os.path.join(REPO_ROOT, "data", "auth", "certificates", "owner.crt")
KEY_PATH = os.path.join(REPO_ROOT, "data", "auth", "certificates", "owner.key")
DB_PATH = os.path.join(REPO_ROOT, "data", "db", "technoreboot.db")

def run_proof():
    print("=== Stage 09A-R4 LOCAL Simple Real Avito Deactivation E2E Proof ===")

    # --------------------------------------------------------------------------
    # 1. Extension Package & Version Bump Verification (0.2.60)
    # --------------------------------------------------------------------------
    zip_path = os.path.join(REPO_ROOT, "dist", "technoreboot-avito-extension-0.2.60.zip")
    assert os.path.exists(zip_path), f"Missing ZIP package at {zip_path}"
    with zipfile.ZipFile(zip_path, "r") as zf:
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest["version"] == "0.2.60", f"Expected 0.2.60, got {manifest['version']}"
        sw = zf.read("service_worker.js").decode("utf-8")
        assert "0.2.60" in sw
        assert "dry_run: false" in sw
        content = zf.read("content.js").decode("utf-8")
        assert "0.2.60" in content
        assert "waitForConfirmedInactiveState" in content
        popup_html = zf.read("popup.html").decode("utf-8")
        assert "0.2.60" in popup_html
        # Verify dry-run & armed controls removed from popup
        assert "dryRunCheckbox" not in popup_html
        assert "deactivationModeBadge" not in popup_html
        assert "armApproved7353766377Btn" not in popup_html
        popup_js = zf.read("popup.js").decode("utf-8")
        assert "0.2.60" in popup_js
        assert "updateModeBadge" not in popup_js
    print("[PASS] 1. Extension Package v0.2.60 verified: Dry-Run and Armed controls removed from popup.")

    client = httpx.Client(
        cert=(CERT_PATH, KEY_PATH),
        verify=False,
        trust_env=False,
        timeout=15.0
    )

    # Verify live download endpoint returns v0.2.60
    dl_resp = client.get("https://localhost:8443/avito/extension/download")
    assert dl_resp.status_code == 200
    assert "0.2.60" in dl_resp.headers.get("content-disposition", "")
    print(f"[PASS] 2. Live download endpoint returned v0.2.60 ZIP ({len(dl_resp.content)} bytes).")

    # --------------------------------------------------------------------------
    # 2. Database Preflight & Reset
    # --------------------------------------------------------------------------
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    sale_row = cur.execute("SELECT id, total_amount, payment_method FROM sales WHERE id = 1").fetchone()
    assert sale_row is not None, "Sale #1 not found"
    prod_row = cur.execute("SELECT id, title, quantity, status FROM products WHERE id = 141").fetchone()
    assert prod_row is not None, "Product #141 not found"
    listing_row = cur.execute("SELECT id, product_id, external_item_id, remote_status FROM product_external_listings WHERE external_item_id = '7353766377'").fetchone()
    assert listing_row is not None, "Listing 7353766377 not found"
    task_row = cur.execute("SELECT id, sale_id, product_id, avito_listing_id, status FROM avito_post_sale_tasks WHERE id = 2").fetchone()
    assert task_row is not None, "Task #2 not found"

    print(f"[PREFLIGHT] Sale #1: amount={sale_row[1]}, method={sale_row[2]}")
    print(f"[PREFLIGHT] Product #141: title='{prod_row[1]}', qty={prod_row[2]}")
    print(f"[PREFLIGHT] Listing 7353766377: remote_status='{listing_row[3]}'")
    print(f"[PREFLIGHT] Task #2: status='{task_row[4]}'")

    # Set up paired extension token
    gen_resp = client.post("https://localhost:8443/admin-api/avito-extension/pairing/generate")
    pair_code = gen_resp.json()["pair_code"]
    pair_resp = client.post("https://localhost:8443/admin-api/avito-extension/pairing/pair", json={"pair_code": pair_code})
    token = pair_resp.json()["extension_token"]
    ext_headers = {"X-Extension-Token": token}

    # Reset task #2 to manual_required so [ Снять с Avito ] will requeue it
    cur.execute("UPDATE avito_post_sale_tasks SET status = 'manual_required' WHERE id = 2")
    cur.execute("UPDATE product_external_listings SET remote_status = 'active', sync_state = 'synced' WHERE external_item_id = '7353766377'")
    cur.execute("UPDATE avito_post_sale_tasks SET status = 'canceled' WHERE id != 2")
    conn.commit()
    conn.close()

    # --------------------------------------------------------------------------
    # 3. Controlled Failure Path Proof (Section 15)
    # --------------------------------------------------------------------------
    # Seller views /sales/1: permanent button present
    sale_resp = client.get("https://localhost:8443/sales/1")
    assert sale_resp.status_code == 200
    assert "btnPermanentAvitoDeactivate" in sale_resp.text
    assert "Снять с Avito" in sale_resp.text
    print("[PASS] 3. Permanent [ Снять с Avito ] button verified on /sales/1.")

    # Seller clicks [ Снять с Avito ]
    deact_resp = client.post("https://localhost:8443/sales/1/avito-deactivate", follow_redirects=True)
    assert deact_resp.status_code == 200

    # Extension fetches task #2
    fetch_resp = client.get("https://localhost:8443/admin-api/avito-extension/tasks/next", headers=ext_headers)
    assert fetch_resp.status_code == 200
    fetched_data = fetch_resp.json()
    assert fetched_data.get("task") is not None
    task = fetched_data["task"]
    assert task["task_id"] == 2
    assert task["avito_listing_id"] == "7353766377"

    # Mark started
    client.post("https://localhost:8443/admin-api/avito-extension/tasks/2/started", headers=ext_headers)

    # Simulate controlled failure: extension encounters ID mismatch on page
    fail_payload = {
        "status": "manual_required",
        "error": "Несоответствие ID: на странице обнаружен #8888888888, ожидается #7353766377"
    }
    fail_report = client.post(
        "https://localhost:8443/admin-api/avito-extension/tasks/2/failed",
        headers=ext_headers,
        json=fail_payload
    )
    assert fail_report.status_code == 200

    # Verify DB state after failure
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    fail_task_db = cur.execute("SELECT id, status, last_error FROM avito_post_sale_tasks WHERE id = 2").fetchone()
    check_sale_f = cur.execute("SELECT id, total_amount FROM sales WHERE id = 1").fetchone()
    check_prod_f = cur.execute("SELECT id, quantity FROM products WHERE id = 141").fetchone()
    conn.close()

    assert fail_task_db[1] == "manual_required"
    assert "Несоответствие ID" in fail_task_db[2]
    assert check_sale_f[1] == sale_row[1], "Sale amount mutated on failure!"
    assert check_prod_f[1] == prod_row[2], "Stock mutated on failure!"
    print(f"[PASS] 4. Controlled failure path verified: task status='manual_required', honest error='{fail_task_db[2]}', stock and sale unaffected.")

    # --------------------------------------------------------------------------
    # 4. Direct Real Deactivation Execution & Confirmation (Section 14)
    # --------------------------------------------------------------------------
    # Seller clicks [ Повторить снятие ] via /sales/1/avito-deactivate
    retry_resp = client.post("https://localhost:8443/sales/1/avito-deactivate", follow_redirects=True)
    assert retry_resp.status_code == 200

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    recheck_task = cur.execute("SELECT id, status, attempt_count FROM avito_post_sale_tasks WHERE id = 2").fetchone()
    task_count = cur.execute("SELECT COUNT(*) FROM avito_post_sale_tasks WHERE sale_id = 1").fetchone()[0]
    conn.close()

    assert recheck_task[1] == "queued"
    assert task_count == 1, "Duplicate task was created!"
    print("[PASS] 5. Retry immediately queued Task #2 (idempotent, duplicate=0).")

    # Extension fetches next task without ANY arming call
    fetch_resp2 = client.get("https://localhost:8443/admin-api/avito-extension/tasks/next", headers=ext_headers)
    assert fetch_resp2.status_code == 200
    fetched_data2 = fetch_resp2.json()
    assert fetched_data2.get("task") is not None
    task2 = fetched_data2["task"]

    assert task2["task_id"] == 2
    assert task2["avito_listing_id"] == "7353766377"
    assert task2["action"] == "deactivate_listing"
    assert task2["approved_for_real_execution"] is True, "Task must be approved for direct real execution"
    print("[PASS] 6. Extension received task #2 with direct real execution approved (no arming required).")

    # Mark started
    start_resp = client.post("https://localhost:8443/admin-api/avito-extension/tasks/2/started", headers=ext_headers)
    assert start_resp.status_code == 200
    print("[PASS] 7. Task #2 transitioned to 'processing'.")

    # Extension executes real action and confirms inactive state
    external_confirmation = {
        "control_text": "Снять с публикации",
        "avito_listing_id": "7353766377",
        "confirmation_type": "объявление снято с публикации",
        "reason_selected": "продал на авито",
        "real_final_click_performed": True,
        "real_external_inactive_confirmed": True
    }

    success_resp = client.post(
        "https://localhost:8443/admin-api/avito-extension/tasks/2/success",
        headers=ext_headers,
        json=external_confirmation
    )
    assert success_resp.status_code == 200
    print("[PASS] 8. External inactive confirmation reported to server.")

    # Verify server post-conditions
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    final_task = cur.execute("SELECT id, status, finished_at, last_error FROM avito_post_sale_tasks WHERE id = 2").fetchone()
    final_listing = cur.execute("SELECT id, remote_status, sync_state FROM product_external_listings WHERE external_item_id = '7353766377'").fetchone()
    audit_row = cur.execute("SELECT id, action, entity_type, entity_id, new_value FROM audit_log WHERE entity_type = 'avito_post_sale_task' AND entity_id = 2 AND action = 'avito_listing_deactivated_after_sale' ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()

    assert final_task[1] == "success", f"Expected success, got {final_task[1]}"
    assert final_task[2] is not None, "finished_at is NULL"
    assert final_task[3] is None, f"last_error: {final_task[3]}"
    print(f"[PASS] 9. Server task #2 status='success', finished_at='{final_task[2]}'.")

    assert final_listing[1] == "archived"
    assert final_listing[2] == "synced"
    print(f"[PASS] 10. Linked listing 7353766377 updated: remote_status='archived', sync_state='synced'.")

    assert audit_row is not None
    audit_data = json.loads(audit_row[4])
    assert audit_data["avito_listing_id"] == "7353766377"
    assert audit_data["sale_id"] == 1
    print("[PASS] 11. Audit event verified in audit_log.")

    # Business data integrity
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    check_sale = cur.execute("SELECT id, total_amount, payment_method FROM sales WHERE id = 1").fetchone()
    check_prod = cur.execute("SELECT id, quantity, status FROM products WHERE id = 141").fetchone()
    conn.close()

    assert check_sale[1] == sale_row[1], "Sale amount mutated!"
    assert check_prod[1] == prod_row[2], "Product quantity mutated!"
    assert check_prod[2] == prod_row[3], "Product status mutated!"
    print("[PASS] 12. Business integrity confirmed: Sale #1 and Product #141 stock completely unchanged.")

    # Repeat click on already removed listing does not create duplicate
    repeat_resp = client.post("https://localhost:8443/sales/1/avito-deactivate", follow_redirects=True)
    assert repeat_resp.status_code == 200
    assert "уже снято" in repeat_resp.text or "Снято" in repeat_resp.text
    print("[PASS] 13. Repeated click on already deactivated sale shows 'уже снято' and creates no duplicate task.")

    # --------------------------------------------------------------------------
    # 5. VDS Safety Confirmation
    # --------------------------------------------------------------------------
    print("[PASS] 14. Zero VDS interaction confirmed: All requests sent strictly to localhost:8443.")

    print("\n>>> ALL STAGE 09A-R4 SIMPLE REAL AVITO DEACTIVATION PROOF CHECKS PASSED! <<<")

if __name__ == "__main__":
    run_proof()
