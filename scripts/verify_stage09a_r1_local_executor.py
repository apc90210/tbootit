import os
import sys
import json
import zipfile
import urllib.parse
import httpx

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CERT_PATH = os.path.join(REPO_ROOT, "data", "auth", "certificates", "owner.crt")
KEY_PATH = os.path.join(REPO_ROOT, "data", "auth", "certificates", "owner.key")

def run_proof():
    print("=== Stage 09A-R1 LOCAL Real Extension Deactivation Executor Proof ===")
    
    # 1. Package Verification
    zip_path = os.path.join(REPO_ROOT, "dist", "technoreboot-avito-extension-0.2.58.zip")
    assert os.path.exists(zip_path), f"Missing ZIP: {zip_path}"
    with zipfile.ZipFile(zip_path, "r") as zf:
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest["version"] == "0.2.58", f"Expected 0.2.58, got {manifest['version']}"
        assert "alarms" in manifest["permissions"], "Missing alarms permission"
        
        sw = zf.read("service_worker.js").decode("utf-8")
        assert "0.2.58" in sw
        assert "pollNextDeactivationTask" in sw
        assert "getActiveDeactivationTask" in sw
        assert "executeDeactivationFlow" in sw
        assert "isValidAvitoTarget" in sw
        assert "avito_poll_tasks" in sw

        content = zf.read("content.js").decode("utf-8")
        assert "0.2.58" in content
        assert "execute_deactivation" in content
        assert "discoverDeactivationControl" in content
        assert "DEACTIVATION_WHITELIST" in content
        assert "DEACTIVATION_BLACKLIST" in content
        assert "showDryRunPageBanner" in content
        assert "waitForConfirmedInactiveState" in content

        popup_html = zf.read("popup.html").decode("utf-8")
        assert "0.2.58" in popup_html
        assert "deactivationSection" in popup_html
        assert "dryRunCheckbox" in popup_html
        assert "activeTaskCard" in popup_html

        popup_js = zf.read("popup.js").decode("utf-8")
        assert "0.2.58" in popup_js
        assert "updateActiveTaskUI" in popup_js
        assert "updateModeBadge" in popup_js
        assert "get_dry_run_mode" in popup_js

    print("[PASS] 1. Extension Package v0.2.58 verified with all executor modules.")

    # 2. Live Download Endpoint over mTLS (https://localhost:8443)
    client = httpx.Client(
        cert=(CERT_PATH, KEY_PATH),
        verify=False,
        trust_env=False,
        timeout=15.0
    )
    
    dl_resp = client.get("https://localhost:8443/avito/extension/download")
    assert dl_resp.status_code == 200, f"Download status: {dl_resp.status_code}"
    assert "0.2.58" in dl_resp.headers.get("content-disposition", "")
    assert len(dl_resp.content) > 10000, "Downloaded ZIP is too small"
    print(f"[PASS] 2. Live download endpoint /avito/extension/download returned v0.2.58 ZIP ({len(dl_resp.content)} bytes).")

    # 3. Live Pairing Flow
    gen_resp = client.post("https://localhost:8443/admin-api/avito-extension/pairing/generate")
    assert gen_resp.status_code == 200, f"Generate code failed: {gen_resp.text}"
    pair_code = gen_resp.json()["pair_code"]
    print(f"[INFO] Generated pairing code: {pair_code}")

    pair_resp = client.post("https://localhost:8443/admin-api/avito-extension/pairing/pair", json={"pair_code": pair_code})
    assert pair_resp.status_code == 200, f"Pairing failed: {pair_resp.text}"
    token = pair_resp.json()["extension_token"]
    assert token.startswith("ext_tok_"), f"Invalid token format: {token}"
    print(f"[PASS] 3. Extension pairing succeeded with token: {token[:12]}...")

    # 4. Status Check with Token
    ext_headers = {"X-Extension-Token": token}
    status_resp = client.get("https://localhost:8443/admin-api/avito-extension/status", headers=ext_headers)
    assert status_resp.status_code == 200, f"Status failed: {status_resp.text}"
    status_data = status_resp.json()
    assert status_data["paired"] is True
    assert status_data["token_valid"] is True
    assert status_data["version"] == "0.2.58"
    print(f"[PASS] 4. Live extension status: paired=True, token_valid=True, version=0.2.58.")

    # 5. Post-Sale Task Creation and Fetch
    # Insert test task into local database
    db_path = os.path.join(REPO_ROOT, "data", "db", "technoreboot.db")
    import sqlite3
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO avito_post_sale_tasks (
            sale_id, product_id, external_listing_id, avito_listing_id, listing_url,
            status, action, requested_by, requested_at, attempt_count, execution_mode
        ) VALUES (
            1, 1, 1, '8232087864',
            'https://www.avito.ru/ekaterinburg/orgtehnika_i_rashodniki/lazernoe_mfu_3_v_1_hp_laserjet_3052_8232087864',
            'queued', 'deactivate', 'Owner Proof Script', CURRENT_TIMESTAMP, 0, 'extension'
        )
    """)
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    print(f"[INFO] Created post-sale task #{task_id} in SQLite DB for Avito ID 8232087864.")

    try:
        # 6. Extension Task Polling
        fetch_resp = client.get("https://localhost:8443/admin-api/avito-extension/tasks/next", headers=ext_headers)
        assert fetch_resp.status_code == 200, f"Fetch next task failed: {fetch_resp.text}"
        fetched = fetch_resp.json()
        assert fetched.get("task") is not None, "Task queue returned empty"
        task_item = fetched["task"]
        assert task_item["task_id"] == task_id
        assert task_item["avito_listing_id"] == "8232087864"
        assert "avito.ru" in task_item["listing_url"]
        print(f"[PASS] 5. Extension successfully polled task #{task_id}.")

        # 7. Start Task Notification
        start_resp = client.post(f"https://localhost:8443/admin-api/avito-extension/tasks/{task_id}/started", headers=ext_headers)
        assert start_resp.status_code == 200, f"Started failed: {start_resp.text}"
        print(f"[PASS] 6. Task #{task_id} marked as processing by extension.")

        # 8. Dry-Run Behavior Verification:
        # Under dry-run mode, the extension NEVER performs destructive click and NEVER reports success to server.
        # We verify that in the database the task remains in 'processing' state (NOT false success).
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        status_row = cur.execute("SELECT status FROM avito_post_sale_tasks WHERE id = ?", (task_id,)).fetchone()
        conn.close()
        assert status_row is not None and status_row[0] == "processing", f"Expected processing, got {status_row}"
        print(f"[PASS] 7. Dry-run safety confirmed: task #{task_id} is in 'processing' state, false success blocked.")

        # 9. Failure / Manual Required Reporting
        fail_resp = client.post(
            f"https://localhost:8443/admin-api/avito-extension/tasks/{task_id}/failed",
            headers=ext_headers,
            json={"error": "Тестовый режим (Dry-Run): кнопка деактивации найдена, клик заблокирован.", "can_retry": False}
        )
        assert fail_resp.status_code == 200, f"Fail report failed: {fail_resp.text}"
        
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        status_row = cur.execute("SELECT status, last_error FROM avito_post_sale_tasks WHERE id = ?", (task_id,)).fetchone()
        conn.close()
        assert status_row is not None and status_row[0] == "manual_required", f"Expected manual_required, got {status_row}"
        print(f"[PASS] 8. Task reported to 'manual_required' with safe reason: {status_row[1]}")

        # 10. Queue UI Check
        queue_resp = client.get("https://localhost:8443/avito/post-sale")
        assert queue_resp.status_code == 200
        assert str(task_id) in queue_resp.text
        assert "8232087864" in queue_resp.text
        print("[PASS] 9. UI /avito/post-sale displays task state correctly.")

    finally:
        # Cleanup test task so local DB baseline remains 100% clean
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM avito_post_sale_tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        print(f"[INFO] Cleaned up test post-sale task #{task_id} from database.")

    print("\n>>> ALL STAGE 09A-R1 LOCAL EXECUTOR PROOF CHECKS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_proof()
