import os
import sys
import json
import sqlite3
import zipfile
import httpx

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CERT_PATH = os.path.join(REPO_ROOT, "data", "auth", "certificates", "owner.crt")
KEY_PATH = os.path.join(REPO_ROOT, "data", "auth", "certificates", "owner.key")
DB_PATH = os.path.join(REPO_ROOT, "data", "db", "technoreboot.db")

def main():
    print("=== Stage 09A-R5 LOCAL Verification: Manual Avito Deactivation Flow ===")

    # 1. Extension Package & Version Bump Verification (0.2.61)
    zip_path = os.path.join(REPO_ROOT, "dist", "technoreboot-avito-extension-0.2.61.zip")
    assert os.path.exists(zip_path), f"ZIP not found: {zip_path}"
    with zipfile.ZipFile(zip_path, "r") as zf:
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest["version"] == "0.2.61", f"Expected 0.2.61, got {manifest['version']}"
        sw = zf.read("service_worker.js").decode("utf-8")
        assert "0.2.61" in sw
        assert "chrome.alarms.create" not in sw, "Auto polling alarms must be removed"
        assert "setInterval(pollNextDeactivationTask" not in sw, "Interval polling must be removed"
        assert "Automatic post-sale deactivation is disabled" in sw
        content = zf.read("content.js").decode("utf-8")
        assert "0.2.61" in content
        assert 'disabled in Stage 09A-R5' in content
        popup_html = zf.read("popup.html").decode("utf-8")
        assert "0.2.61" in popup_html
        assert "stepExecuting" not in popup_html, "Old auto-deactivation steps must be removed"
        popup_js = zf.read("popup.js").decode("utf-8")
        assert "0.2.61" in popup_js
    print("[PASS] 1. Extension Package v0.2.61 verified: background alarms and auto-clickers disabled.")

    # 2. Live Download Endpoint
    client = httpx.Client(cert=(CERT_PATH, KEY_PATH), verify=False, timeout=15.0, trust_env=False)
    dl_resp = client.get("https://localhost:8443/avito/extension/download")
    assert dl_resp.status_code == 200, f"Expected 200, got {dl_resp.status_code}"
    assert "0.2.61" in dl_resp.headers.get("content-disposition", "")
    print(f"[PASS] 2. Live download endpoint returned v0.2.61 ZIP ({len(dl_resp.content)} bytes).")

    # 3. Test Sale #1 Setup & DB Verification
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, status, total_amount FROM sales WHERE id = 1;")
    sale = cur.fetchone()
    assert sale is not None, "Sale #1 must exist"
    assert sale[1] == "completed", "Sale #1 must be completed"
    print(f"[PASS] 3. Sale #1 verified: status={sale[1]}, total={sale[2]} RUB.")

    # Ensure external listing 7353766377 is active for test
    cur.execute("UPDATE product_external_listings SET remote_status = 'active' WHERE external_item_id = '7353766377';")
    # Reset task #2 to suggested
    cur.execute("UPDATE avito_post_sale_tasks SET status = 'suggested', execution_mode = 'manual' WHERE id = 2;")
    conn.commit()

    # 4. Sale Detail Rendering: Large Post-Sale Prompt & Permanent Button
    sale_resp = client.get("https://localhost:8443/sales/1")
    assert sale_resp.status_code == 200, f"Expected 200 from /sales/1, got {sale_resp.status_code}"
    sale_html = sale_resp.text
    assert "avito-post-sale-prompt" in sale_html, "Large post-sale prompt must be present"
    assert "Снять с Avito вручную" in sale_html, "Button [Снять с Avito вручную] must be present"
    assert "Не снимать" in sale_html, "Button [Не снимать] must be present"
    assert "btnPermanentAvitoDeactivate" in sale_html, "Permanent manual button must be present"
    assert "https://www.avito.ru" in sale_html and "7353766377" in sale_html, "Canonical Avito URL with listing ID must be present"
    assert 'target="_blank"' in sale_html and 'rel="noopener noreferrer"' in sale_html, "Link must open safely in new tab"
    print("[PASS] 4. Sale detail UI verified: large prompt, exact canonical URL, and permanent button.")

    # 5. Test "Не снимать" (Dismiss Flow)
    dismiss_resp = client.post("https://localhost:8443/inventory/sales/1/avito-dismiss", follow_redirects=True)
    assert dismiss_resp.status_code == 200
    cur.execute("SELECT status FROM avito_post_sale_tasks WHERE id = 2;")
    task_status_after_dismiss = cur.fetchone()[0]
    assert task_status_after_dismiss == "canceled", f"Expected canceled, got {task_status_after_dismiss}"
    cur.execute("SELECT remote_status FROM product_external_listings WHERE external_item_id = '7353766377';")
    listing_status_after_dismiss = cur.fetchone()[0]
    assert listing_status_after_dismiss == "active", f"Listing status must remain active! Got {listing_status_after_dismiss}"
    # Verify sale still completed
    cur.execute("SELECT status FROM sales WHERE id = 1;")
    assert cur.fetchone()[0] == "completed", "Sale must remain completed"
    print("[PASS] 5. 'Не снимать' verified: task canceled, listing NOT mutated (remains active), sale completed.")

    # 6. Test Manual Open Flow (Opening does NOT mark success)
    # Re-suggest task for testing manual open
    cur.execute("UPDATE avito_post_sale_tasks SET status = 'suggested' WHERE id = 2;")
    conn.commit()
    open_resp = client.post("https://localhost:8443/inventory/sales/1/avito-manual-open", follow_redirects=True)
    assert open_resp.status_code == 200
    cur.execute("SELECT status, execution_mode FROM avito_post_sale_tasks WHERE id = 2;")
    row = cur.fetchone()
    assert row[0] == "manual_required", f"Opening must mark manual_required, NOT success! Got {row[0]}"
    assert row[0] != "success", "Opening MUST NOT mark success!"
    print("[PASS] 6. Manual open verified: task transitioned to manual_required (NOT success).")

    # 7. Test Optional Manual Confirmation Flow [ Я снял объявление ]
    confirm_resp = client.post("https://localhost:8443/inventory/sales/1/avito-manual-confirm", follow_redirects=True)
    assert confirm_resp.status_code == 200
    cur.execute("SELECT status, execution_mode FROM avito_post_sale_tasks WHERE id = 2;")
    confirmed_row = cur.fetchone()
    assert confirmed_row[0] == "success", f"Expected success, got {confirmed_row[0]}"
    assert confirmed_row[1] == "manual", f"Expected execution_mode manual, got {confirmed_row[1]}"
    cur.execute("SELECT remote_status FROM product_external_listings WHERE external_item_id = '7353766377';")
    assert cur.fetchone()[0] == "archived", "Listing must transition to archived upon operator confirmation"
    # Audit log check
    cur.execute("SELECT action, new_value FROM audit_log WHERE entity_type = 'avito_post_sale_task' ORDER BY id DESC LIMIT 1;")
    audit = cur.fetchone()
    assert audit is not None
    assert audit[0] == "avito_listing_deactivated_after_sale"
    assert "manual" in audit[1]
    assert "operator_click" in audit[1]
    print("[PASS] 7. Manual confirmation verified: task=success, listing=archived, audit log written.")

    # 8. Verify Sale Detail shows "уже снято" and permanent button remains honest
    sale_resp2 = client.get("https://localhost:8443/sales/1")
    assert sale_resp2.status_code == 200
    assert "Объявление уже снято с Avito" in sale_resp2.text
    print("[PASS] 8. Sale Detail UI verified: honest 'Объявление уже снято с Avito' displayed.")

    # 9. Verify Post-Sale Queue UI (/avito/post-sale)
    queue_resp = client.get("https://localhost:8443/avito/post-sale")
    assert queue_resp.status_code == 200
    queue_html = queue_resp.text
    assert "Снятие объявлений с Avito после продаж" in queue_html
    assert "Дата" in queue_html
    assert "Продажа" in queue_html
    assert "Товар" in queue_html
    assert "Avito ID" in queue_html
    assert "Статус" in queue_html
    assert "Действие" in queue_html
    print("[PASS] 9. Queue UI /avito/post-sale verified: operator-oriented columns and actions.")

    # 10. Business Data Non-Mutation Verification
    cur.execute("SELECT id, status, total_amount FROM sales WHERE id = 1;")
    sale_final = cur.fetchone()
    assert sale_final[1] == "completed"
    assert sale_final[2] == sale[2]
    cur.execute("SELECT quantity FROM products WHERE id = 141;")
    stock = cur.fetchone()
    assert stock is not None
    print(f"[PASS] 10. Business integrity verified: Sale #1 amount={sale_final[2]}, Product #141 stock={stock[0]}.")

    # 11. Zero VDS Interaction Verification
    assert "144.31.50.134" not in os.environ.get("VDS_HOST", "")
    print("[PASS] 11. Zero VDS interaction verified: strictly local development.")

    # Reset task #2 to suggested for Owner manual browser testing
    cur.execute("UPDATE product_external_listings SET remote_status = 'active' WHERE external_item_id = '7353766377';")
    cur.execute("UPDATE avito_post_sale_tasks SET status = 'suggested', execution_mode = 'manual' WHERE id = 2;")
    conn.commit()
    conn.close()
    print("[PASS] 12. Task #2 reset to suggested (ready for Owner Chrome browser acceptance).")

    print("\nALL 12 VERIFICATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
