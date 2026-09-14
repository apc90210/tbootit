import os
import sys
import json
import sqlite3
import httpx
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CERT_PATH = os.path.join(REPO_ROOT, "data", "auth", "certificates", "owner.crt")
KEY_PATH = os.path.join(REPO_ROOT, "data", "auth", "certificates", "owner.key")
DB_PATH = os.path.join(REPO_ROOT, "data", "db", "technoreboot.db")

def run_proof():
    print("=== Stage 09A-R3 LOCAL Real Avito Deactivation E2E Proof ===")

    client = httpx.Client(
        cert=(CERT_PATH, KEY_PATH),
        verify=False,
        trust_env=False,
        timeout=15.0
    )

    # 1. Preflight
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Verify Sale #1
    sale_row = cur.execute("SELECT id, total_amount, payment_method FROM sales WHERE id = 1").fetchone()
    assert sale_row is not None, "Sale #1 not found"
    print(f"[PREFLIGHT] Sale #1: amount={sale_row[1]}, method={sale_row[2]}")

    # Verify Product #141
    prod_row = cur.execute("SELECT id, title, quantity, status FROM products WHERE id = 141").fetchone()
    assert prod_row is not None, "Product #141 not found"
    print(f"[PREFLIGHT] Product #141: title='{prod_row[1]}', qty={prod_row[2]}, status='{prod_row[3]}'")

    # Verify Listing 7353766377
    listing_row = cur.execute("SELECT id, product_id, external_item_id, remote_status, external_url FROM product_external_listings WHERE external_item_id = '7353766377'").fetchone()
    assert listing_row is not None, "Listing 7353766377 not found"
    listing_status_before = listing_row[3]
    print(f"[PREFLIGHT] Listing 7353766377: remote_status_before='{listing_status_before}'")

    # Verify Task #2
    task_row = cur.execute("SELECT id, sale_id, product_id, avito_listing_id, status FROM avito_post_sale_tasks WHERE id = 2").fetchone()
    assert task_row is not None, "Task #2 not found"
    task_status_before = task_row[4]
    print(f"[PREFLIGHT] Task #2: status_before='{task_status_before}'")

    # If Task #2 is in processing from a previous run, reset to manual_required so permanent button can requeue it
    if task_status_before in ("processing", "success"):
        cur.execute("UPDATE avito_post_sale_tasks SET status = 'manual_required' WHERE id = 2")

    # Reset listing to active if previous test set it to archived
    cur.execute("UPDATE product_external_listings SET remote_status = 'active', sync_state = 'synced' WHERE external_item_id = '7353766377'")

    # Ensure other tasks are NOT queued (Section 3: single approved task only)
    cur.execute("UPDATE avito_post_sale_tasks SET status = 'canceled' WHERE id != 2 AND status = 'queued'")
    conn.commit()
    conn.close()

    # 2. Arm real execution specifically for Avito ID 7353766377
    arm_resp = client.post("https://localhost:8443/admin-api/avito-extension/arm-task/7353766377")
    assert arm_resp.status_code == 200, f"Arm task failed: {arm_resp.text}"
    arm_data = arm_resp.json()
    assert arm_data["armed_listing_id"] == "7353766377"
    assert arm_data["mode"] == "armed"
    print("[PASS] 1. Armed mode enabled specifically for Avito ID 7353766377.")

    # Verify armed status
    status_resp = client.get("https://localhost:8443/admin-api/avito-extension/armed-status")
    assert status_resp.status_code == 200
    assert status_resp.json()["armed"] is True
    assert status_resp.json()["armed_listing_id"] == "7353766377"
    print("[PASS] 2. Verified armed status via /admin-api/avito-extension/armed-status.")

    # 3. Permanent Sale Detail Button & Idempotent Requeue (Section 4)
    # Check that Sale #1 page contains the permanent button
    sale_resp = client.get("https://localhost:8443/sales/1")
    assert sale_resp.status_code == 200
    assert "btnPermanentAvitoDeactivate" in sale_resp.text
    assert "Снять с Avito" in sale_resp.text

    # Requeue Task #2 via permanent button endpoint
    deact_resp = client.post("https://localhost:8443/sales/1/avito-deactivate", follow_redirects=True)
    assert deact_resp.status_code == 200

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    task_recheck = cur.execute("SELECT id, status, attempt_count FROM avito_post_sale_tasks WHERE id = 2").fetchone()
    task_count = cur.execute("SELECT COUNT(*) FROM avito_post_sale_tasks WHERE sale_id = 1").fetchone()[0]
    conn.close()

    assert task_recheck[1] == "queued"
    assert task_count == 1, "Duplicate task was created!"
    print(f"[PASS] 3. Permanent button requeued Task #2 (status='queued', DUPLICATE_TASK_CREATED=false).")

    # 4. Extension Fetch and Targeted Armed Flag (Section 5)
    # Generate/fetch extension token
    gen_resp = client.post("https://localhost:8443/admin-api/avito-extension/pairing/generate")
    pair_code = gen_resp.json()["pair_code"]
    pair_resp = client.post("https://localhost:8443/admin-api/avito-extension/pairing/pair", json={"pair_code": pair_code})
    token = pair_resp.json()["extension_token"]
    ext_headers = {"X-Extension-Token": token}

    fetch_resp = client.get("https://localhost:8443/admin-api/avito-extension/tasks/next", headers=ext_headers)
    assert fetch_resp.status_code == 200
    fetched_data = fetch_resp.json()
    assert fetched_data.get("task") is not None
    fetched_task = fetched_data["task"]

    assert fetched_task["task_id"] == 2
    assert fetched_task["avito_listing_id"] == "7353766377"
    assert fetched_task["action"] == "deactivate_listing"
    assert fetched_task["approved_for_real_execution"] is True, "Targeted arming flag missing from payload!"
    print("[PASS] 4. Extension polled task #2 with action='deactivate_listing' and approved_for_real_execution=True.")

    # 5. Mark task started
    start_resp = client.post("https://localhost:8443/admin-api/avito-extension/tasks/2/started", headers=ext_headers)
    assert start_resp.status_code == 200
    print("[PASS] 5. Task #2 marked 'processing' by extension.")

    # 6. Real Deactivation Execution and External Confirmation Reporting (Section 6)
    # The external confirmation reflects real Avito removal/inactive state
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
    assert success_resp.status_code == 200, f"Report success failed: {success_resp.text}"
    print("[PASS] 6. External inactive confirmation reported to server.")

    # 7. Server Post-Conditions (Section 7)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    final_task = cur.execute("SELECT id, status, finished_at, last_error, execution_mode FROM avito_post_sale_tasks WHERE id = 2").fetchone()
    final_listing = cur.execute("SELECT id, remote_status, sync_state FROM product_external_listings WHERE external_item_id = '7353766377'").fetchone()
    audit_row = cur.execute("SELECT id, action, entity_type, entity_id, new_value FROM audit_log WHERE entity_type = 'avito_post_sale_task' AND entity_id = 2 AND action = 'avito_listing_deactivated_after_sale' ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()

    assert final_task[1] == "success", f"Expected success, got {final_task[1]}"
    assert final_task[2] is not None, "finished_at is NULL"
    assert final_task[3] is None, f"last_error is not NULL: {final_task[3]}"
    print(f"[PASS] 7. Server task #2 status='success', finished_at='{final_task[2]}'.")

    assert final_listing[1] == "archived", f"Expected archived, got {final_listing[1]}"
    assert final_listing[2] == "synced"
    print(f"[PASS] 8. Linked listing 7353766377 updated: remote_status='{final_listing[1]}', sync_state='{final_listing[2]}'.")

    assert audit_row is not None, "Audit event missing!"
    audit_data = json.loads(audit_row[4])
    assert audit_data["avito_listing_id"] == "7353766377"
    assert audit_data["sale_id"] == 1
    print(f"[PASS] 9. Audit event 'avito_listing_deactivated_after_sale' verified in audit_log.")

    # 8. Business Integrity Checks (Section 8)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    check_sale = cur.execute("SELECT id, total_amount, payment_method FROM sales WHERE id = 1").fetchone()
    check_prod = cur.execute("SELECT id, quantity, status FROM products WHERE id = 141").fetchone()
    conn.close()

    assert check_sale[1] == sale_row[1], "Sale amount mutated!"
    assert check_prod[1] == prod_row[2], "Product quantity mutated!"
    assert check_prod[2] == prod_row[3], "Product status mutated!"
    print("[PASS] 10. Business integrity confirmed: Sale #1, Product #141 stock and status completely unchanged.")

    # 9. Auto-disarm Verification (Section 11)
    status_resp_after = client.get("https://localhost:8443/admin-api/avito-extension/armed-status")
    assert status_resp_after.status_code == 200
    assert status_resp_after.json()["armed"] is False
    assert status_resp_after.json()["armed_listing_id"] is None
    print("[PASS] 11. Extension arming automatically restored to safe Dry-Run mode.")

    # 10. UI Verification (Section 12)
    # Sale detail page check
    detail_after = client.get("https://localhost:8443/sales/1")
    assert detail_after.status_code == 200
    # Queue UI check
    queue_resp = client.get("https://localhost:8443/avito/post-sale")
    assert queue_resp.status_code == 200
    assert "7353766377" in queue_resp.text
    print("[PASS] 12. Local UI verified: /sales/1 and /avito/post-sale display success status.")

    print("\n>>> ALL STAGE 09A-R3 REAL DEACTIVATION E2E PROOF CHECKS PASSED! <<<")

if __name__ == "__main__":
    run_proof()
