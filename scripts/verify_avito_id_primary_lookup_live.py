#!/usr/bin/env python3
"""
Live verification script confirming Avito ID is the universal matching identifier across all statuses:
1. Initial active import -> creates product.
2. Identical active re-import -> in-place no-op for stock, NO duplicate product created.
3. Active re-import with price change -> updates price in place, NO duplicate product created.
4. Product sold (moved to archive) -> re-import active pulls back to store, NO duplicate product created.
5. Missing external listing fallback -> matches product by SKU across DB and heals link without duplication.
"""

import sys
import sqlite3
import httpx
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "db" / "technoreboot.db"
CORE_URL = "http://127.0.0.1:8000"


def main():
    print("=== STARTING LIVE VERIFICATION: AVITO ID PRIMARY IDENTIFIER ===")

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    core_client = httpx.Client(base_url=CORE_URL, timeout=10.0, trust_env=False)

    test_avito_id = "test-live-key-lookup-88899"
    created_product_ids = []

    try:
        # Step 1: Initial import
        print("\n--- Step 1: Initial Import ---")
        payload = {
            "account_key": "account_laptops",
            "external_item_id": test_avito_id,
            "external_url": f"https://www.avito.ru/item/{test_avito_id}",
            "remote_status": "active",
            "title": "Ноутбук для проверки первичного ключа Авито",
            "price": 32000.0,
            "description": "Описание 1",
            "parameters": {"Оперативная память": "16 ГБ"}
        }
        res1 = core_client.post("/api/integrations/avito/import-item", json=payload)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] == "created"
        prod_id = data1["product_id"]
        created_product_ids.append(prod_id)
        print(f"Created product ID: {prod_id}")

        # Verify exactly 1 product exists with this SKU
        cur.execute("SELECT count(*) FROM products WHERE sku = ?", (f"AVITO-{test_avito_id}",))
        assert cur.fetchone()[0] == 1
        print("[OK] Step 1 passed: Product created.")

        # Step 2: Identical re-import
        print("\n--- Step 2: Identical Re-import (No-op check) ---")
        res2 = core_client.post("/api/integrations/avito/import-item", json=payload)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["status"] == "updated"
        assert data2["product_id"] == prod_id
        print(f"Re-imported product ID: {data2['product_id']} (matched original ID)")

        # Verify still exactly 1 product in DB (NO duplicate)
        cur.execute("SELECT count(*) FROM products WHERE sku = ?", (f"AVITO-{test_avito_id}",))
        assert cur.fetchone()[0] == 1
        print("[OK] Step 2 passed: Identical re-import updated in-place, ZERO duplicates created.")

        # Step 3: Re-import with price change
        print("\n--- Step 3: Re-import with Price Change ---")
        payload_new_price = dict(payload)
        payload_new_price["price"] = 33500.0
        res3 = core_client.post("/api/integrations/avito/import-item", json=payload_new_price)
        assert res3.status_code == 200
        assert res3.json()["product_id"] == prod_id

        # Verify price updated on the same product
        cur.execute("SELECT sale_price FROM products WHERE id = ?", (prod_id,))
        assert cur.fetchone()[0] == 33500.0
        cur.execute("SELECT count(*) FROM products WHERE sku = ?", (f"AVITO-{test_avito_id}",))
        assert cur.fetchone()[0] == 1
        print("[OK] Step 3 passed: Price updated on existing product, ZERO duplicates created.")

        # Step 4: Product in Archive -> re-import active
        print("\n--- Step 4: Archive Reactivation by Avito ID ---")
        cur.execute("UPDATE products SET status = 'sold', storage_location = 'archive', quantity = 0 WHERE id = ?", (prod_id,))
        conn.commit()

        res4 = core_client.post("/api/integrations/avito/import-item", json=payload)
        assert res4.status_code == 200
        assert res4.json()["product_id"] == prod_id

        cur.execute("SELECT status, storage_location, quantity FROM products WHERE id = ?", (prod_id,))
        st, loc, qty = cur.fetchone()
        assert st == "in_stock"
        assert loc == "store"
        assert qty == 1
        cur.execute("SELECT count(*) FROM products WHERE sku = ?", (f"AVITO-{test_avito_id}",))
        assert cur.fetchone()[0] == 1
        print("[OK] Step 4 passed: Archived product found by Avito ID and reactivated, ZERO duplicates created.")

        # Step 5: Fallback lookup by SKU if external listing link is missing
        print("\n--- Step 5: Missing External Listing Link Fallback ---")
        cur.execute("DELETE FROM product_external_listings WHERE external_item_id = ?", (test_avito_id,))
        conn.commit()

        # Re-import should find product by SKU and heal external listing
        res5 = core_client.post("/api/integrations/avito/import-item", json=payload)
        assert res5.status_code == 200
        assert res5.json()["product_id"] == prod_id

        cur.execute("SELECT count(*) FROM product_external_listings WHERE external_item_id = ?", (test_avito_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT count(*) FROM products WHERE sku = ?", (f"AVITO-{test_avito_id}",))
        assert cur.fetchone()[0] == 1
        print("[OK] Step 5 passed: Fallback by SKU succeeded and healed link, ZERO duplicates created.")

    finally:
        print("\n--- Step 6: Teardown test records ---")
        for p_id in created_product_ids:
            cur.execute("DELETE FROM product_events WHERE product_id = ?", (p_id,))
            cur.execute("DELETE FROM product_photos WHERE product_id = ?", (p_id,))
            cur.execute("DELETE FROM product_external_listings WHERE product_id = ?", (p_id,))
            cur.execute("DELETE FROM products WHERE id = ?", (p_id,))
        conn.commit()
        conn.close()
        print("[OK] Teardown completed successfully.")

    print("\n=== ALL AVITO ID PRIMARY IDENTIFIER CHECKS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    main()
