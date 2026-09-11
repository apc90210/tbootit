#!/usr/bin/env python3
"""
Live verification script for bidirectional Avito archive synchronization:
1. Product imported as active -> status='in_stock', storage_location='store', quantity=1.
2. Product sold via checkout -> status='sold', storage_location='archive', quantity=0.
3. Re-imported from Avito as active -> reactivated out of archive: status='in_stock', storage_location='store', quantity=1, event='avito_reactivated'.
4. Re-imported from Avito as inactive -> archived: status='sold', storage_location='archive', quantity=0, event='avito_archived'.
5. Re-imported as active again -> restored to store: status='in_stock', storage_location='store', quantity=1.
6. Brand new listing imported as inactive -> created directly in archive: status='sold', storage_location='archive', quantity=0.
7. Gateway 8443 mTLS check with Owner certificate.
8. Clean teardown of test records.
"""

import sys
import sqlite3
import httpx
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTH_DIR = PROJECT_ROOT / "data" / "auth"
OWNER_CRT = AUTH_DIR / "certificates" / "owner.crt"
OWNER_KEY = AUTH_DIR / "certificates" / "owner.key"
DB_PATH = PROJECT_ROOT / "data" / "db" / "technoreboot.db"

CORE_URL = "http://127.0.0.1:8000"
GATEWAY_URL = "https://127.0.0.1:8443"


def main():
    print("=== STARTING BIDIRECTIONAL AVITO ARCHIVE SYNC LIVE VERIFICATION ===")

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    core_client = httpx.Client(base_url=CORE_URL, timeout=10.0, trust_env=False)

    created_product_ids = []
    created_sale_ids = []

    try:
        # Step 1: Import a product as active
        test_ext_id = "test-live-bidirectional-sync-101"
        payload_active = {
            "account_key": "account_laptops",
            "external_item_id": test_ext_id,
            "external_url": f"https://www.avito.ru/item/{test_ext_id}",
            "remote_status": "active",
            "title": "Тестовый Ноутбук Синхронизация Архива",
            "price": 18500.0,
            "description": "Тестовое описание для проверки синхронизации",
            "parameters": {"Тест": "Да"}
        }

        print("\n--- Step 1: Import product as active ---")
        res1 = core_client.post("/api/integrations/avito/import-item", json=payload_active)
        assert res1.status_code == 200, f"Import failed: {res1.text}"
        prod_id1 = res1.json()["product_id"]
        created_product_ids.append(prod_id1)
        print(f"Imported product ID: {prod_id1}")

        prod1 = core_client.get(f"/api/products/{prod_id1}").json()
        print(f"Product state: status={prod1['status']}, location={prod1['storage_location']}, qty={prod1['quantity']}")
        assert prod1["status"] == "in_stock"
        assert prod1["storage_location"] == "store"
        assert prod1["quantity"] == 1
        print("[OK] Step 1 passed: Product created active in store.")

        # Step 2: Sell product in store
        print("\n--- Step 2: Sell product via store checkout ---")
        sale_payload = {
            "total_amount": 18500.0,
            "payment_method": "cash",
            "comment": "Live test sale for archive reactivation",
            "items": [
                {
                    "product_id": prod_id1,
                    "title": prod1["title"],
                    "price": 18500.0,
                    "quantity": 1
                }
            ]
        }
        res_sale = core_client.post("/api/sales/", json=sale_payload)
        assert res_sale.status_code == 200, f"Sale failed: {res_sale.text}"
        sale_id = res_sale.json()["id"]
        created_sale_ids.append(sale_id)
        print(f"Created sale ID: {sale_id}")

        prod1_sold = core_client.get(f"/api/products/{prod_id1}").json()
        print(f"Product state after sale: status={prod1_sold['status']}, location={prod1_sold['storage_location']}, qty={prod1_sold['quantity']}")
        assert prod1_sold["status"] == "sold"
        assert prod1_sold["storage_location"] == "archive"
        assert prod1_sold["quantity"] == 0
        print("[OK] Step 2 passed: Product moved to archive after sale.")

        # Step 3: Re-import from Avito as active (Reactivation)
        print("\n--- Step 3: Re-import from Avito as active (Reactivation) ---")
        payload_reactivate = dict(payload_active)
        payload_reactivate["price"] = 19000.0  # Update price as well
        res3 = core_client.post("/api/integrations/avito/import-item", json=payload_reactivate)
        assert res3.status_code == 200, f"Reactivation import failed: {res3.text}"
        assert res3.json()["product_id"] == prod_id1

        prod1_reactivated = core_client.get(f"/api/products/{prod_id1}").json()
        print(f"Product state after reactivation: status={prod1_reactivated['status']}, location={prod1_reactivated['storage_location']}, qty={prod1_reactivated['quantity']}, sale_price={prod1_reactivated['sale_price']}")
        assert prod1_reactivated["status"] == "in_stock"
        assert prod1_reactivated["storage_location"] == "store"
        assert prod1_reactivated["quantity"] == 1
        assert prod1_reactivated["sale_price"] == 19000.0

        # Check ProductEvent logged
        cur.execute("SELECT event_type, comment FROM product_events WHERE product_id = ? ORDER BY id DESC LIMIT 1", (prod_id1,))
        last_event = cur.fetchone()
        print(f"Last product event: {last_event}")
        assert last_event[0] == "avito_reactivated"
        print("[OK] Step 3 passed: Archived product pulled back into store as in_stock with event logged.")

        # Step 4: Re-import from Avito as inactive (Reverse sync: Archiving)
        print("\n--- Step 4: Re-import from Avito as inactive (Archiving) ---")
        payload_archive = dict(payload_active)
        payload_archive["remote_status"] = "closed"
        payload_archive["raw_status"] = "завершено"
        res4 = core_client.post("/api/integrations/avito/import-item", json=payload_archive)
        assert res4.status_code == 200, f"Archive import failed: {res4.text}"
        assert res4.json()["product_id"] == prod_id1

        prod1_archived = core_client.get(f"/api/products/{prod_id1}").json()
        print(f"Product state after archive import: status={prod1_archived['status']}, location={prod1_archived['storage_location']}, qty={prod1_archived['quantity']}")
        assert prod1_archived["status"] == "sold"
        assert prod1_archived["storage_location"] == "archive"
        assert prod1_archived["quantity"] == 0

        # Check ProductEvent logged
        cur.execute("SELECT event_type, comment FROM product_events WHERE product_id = ? ORDER BY id DESC LIMIT 1", (prod_id1,))
        last_event = cur.fetchone()
        print(f"Last product event: {last_event}")
        assert last_event[0] == "avito_archived"
        print("[OK] Step 4 passed: Active product moved to archive on Avito closure with event logged.")

        # Step 5: Re-import from Avito as active again
        print("\n--- Step 5: Re-import from Avito as active again ---")
        payload_reactivate2 = dict(payload_active)
        payload_reactivate2["remote_status"] = "active"
        payload_reactivate2["raw_status"] = "активно"
        res5 = core_client.post("/api/integrations/avito/import-item", json=payload_reactivate2)
        assert res5.status_code == 200
        assert res5.json()["product_id"] == prod_id1

        prod1_reactivated2 = core_client.get(f"/api/products/{prod_id1}").json()
        print(f"Product state after 2nd reactivation: status={prod1_reactivated2['status']}, location={prod1_reactivated2['storage_location']}, qty={prod1_reactivated2['quantity']}")
        assert prod1_reactivated2["status"] == "in_stock"
        assert prod1_reactivated2["storage_location"] == "store"
        assert prod1_reactivated2["quantity"] == 1
        print("[OK] Step 5 passed: Restored back to store cleanly.")

        # Step 6: Brand new product imported with inactive status
        print("\n--- Step 6: Brand new product imported as inactive ---")
        test_ext_id2 = "test-live-bidirectional-sync-102"
        payload_new_inactive = {
            "account_key": "account_laptops",
            "external_item_id": test_ext_id2,
            "external_url": f"https://www.avito.ru/item/{test_ext_id2}",
            "remote_status": "inactive",
            "raw_status": "архив",
            "title": "Тестовый Товар Сразу В Архив",
            "price": 5000.0,
            "description": "Тестовый закрытый товар",
            "parameters": {}
        }
        res6 = core_client.post("/api/integrations/avito/import-item", json=payload_new_inactive)
        assert res6.status_code == 200
        prod_id2 = res6.json()["product_id"]
        created_product_ids.append(prod_id2)
        print(f"Imported inactive product ID: {prod_id2}")

        prod2 = core_client.get(f"/api/products/{prod_id2}").json()
        print(f"Inactive product state: status={prod2['status']}, location={prod2['storage_location']}, qty={prod2['quantity']}")
        assert prod2["status"] == "sold"
        assert prod2["storage_location"] == "archive"
        assert prod2["quantity"] == 0
        print("[OK] Step 6 passed: New inactive listing directly created in archive.")

        # Step 7: Gateway mTLS check
        print("\n--- Step 7: Gateway 8443 mTLS access with Owner certificate ---")
        gw_client = httpx.Client(
            cert=(str(OWNER_CRT), str(OWNER_KEY)),
            verify=False,
            trust_env=False,
            timeout=15.0
        )
        gw_res = gw_client.get(f"{GATEWAY_URL}/inventory/products")
        print(f"Gateway /inventory/products status: {gw_res.status_code}")
        assert gw_res.status_code == 200
        assert "Товары" in gw_res.text or "products" in gw_res.text
        print("[OK] Step 7 passed: Gateway mTLS 8443 accessible and functional.")

    finally:
        # Step 8: Teardown
        print("\n--- Step 8: Teardown test records ---")
        for s_id in created_sale_ids:
            cur.execute("DELETE FROM sale_items WHERE sale_id = ?", (s_id,))
            cur.execute("DELETE FROM sales WHERE id = ?", (s_id,))
        for p_id in created_product_ids:
            cur.execute("DELETE FROM product_events WHERE product_id = ?", (p_id,))
            cur.execute("DELETE FROM product_photos WHERE product_id = ?", (p_id,))
            cur.execute("DELETE FROM product_external_listings WHERE product_id = ?", (p_id,))
            cur.execute("DELETE FROM products WHERE id = ?", (p_id,))
        conn.commit()
        conn.close()
        print("[OK] Teardown completed successfully.")

    print("\n=== ALL BIDIRECTIONAL ARCHIVE SYNC VERIFICATION CHECKS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    main()
