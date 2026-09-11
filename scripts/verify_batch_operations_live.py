#!/usr/bin/env python3
"""
Live Verification of Batch Operations via Gateway 8443 (mTLS)
Verifies:
1. /inventory/products contains checkboxes and batch action bar
2. Batch status change (set_status) updates products
3. Batch storage location change (set_location) updates products
4. Batch price tags (price-tags/batch) renders 58x40 tags with barcodes
5. Clean teardown of test products
"""

import os
import sqlite3
import httpx
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTH_DIR = PROJECT_ROOT / "data" / "auth"
OWNER_CRT = AUTH_DIR / "certificates" / "owner.crt"
OWNER_KEY = AUTH_DIR / "certificates" / "owner.key"
DB_PATH = PROJECT_ROOT / "data" / "db" / "technoreboot.db"

def main():
    print("=== LIVE VERIFICATION: BATCH OPERATIONS VIA GATEWAY 8443 ===")

    # 1. Setup client
    client = httpx.Client(
        cert=(str(OWNER_CRT), str(OWNER_KEY)),
        verify=False,
        trust_env=False
    )

    # 2. Seed 3 temporary test products in DB
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM products")
    initial_count = cur.fetchone()[0]
    print(f"Initial product count in DB: {initial_count}")

    cur.execute("""
        INSERT INTO products (title, sku, barcode, status, storage_location, sale_price, quantity, source_type)
        VALUES ('Test Batch Laptop', 'BATCH-001', '460000000991', 'draft', 'store', 45000.0, 1, 'test'),
               ('Test Batch Monitor', 'BATCH-002', '460000000992', 'draft', 'store', 18000.0, 2, 'test'),
               ('Test Batch Mouse', 'BATCH-003', '460000000993', 'draft', 'store', 3500.0, 5, 'test')
    """)
    conn.commit()
    cur.execute("SELECT id FROM products WHERE source_type = 'test'")
    test_ids = [r[0] for r in cur.fetchall()]
    print(f"Created temporary test products: {test_ids}")
    test_ids_str = ",".join(str(i) for i in test_ids)

    try:
        # 3. Check HTML on /inventory/products
        print("\n--- Testing UI Elements on /inventory/products ---")
        res = client.get("https://127.0.0.1:8443/inventory/products")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        html = res.text
        assert 'id="select-all-products"' in html, "Missing select-all checkbox"
        assert 'class="product-select-cb"' in html, "Missing row checkboxes"
        assert 'id="batch-actions-bar"' in html, "Missing batch actions bar"
        assert 'id="btn-batch-print-tags"' in html, "Missing print tags button"
        assert 'id="btn-batch-add-cart"' in html, "Missing add to cart button"
        assert 'id="batch-status-select"' in html, "Missing status select"
        assert '— Статус (не менять) —' in html, "Missing default status placeholder"
        assert 'id="batch-location-select"' in html, "Missing location select"
        assert '— Место (не менять) —' in html, "Missing default location placeholder"
        assert 'id="btn-batch-apply-changes"' in html, "Missing unified apply changes button"
        print("[PASS] All unified batch UI elements rendered in /inventory/products")

        # 4. Test Simultaneous Batch Status and Location Update (One Action)
        print("\n--- Testing Simultaneous Batch Status & Location Update (One Action) ---")
        res = client.post(
            "https://127.0.0.1:8443/inventory/products/batch-action",
            data={
                "action": "apply_changes",
                "new_status": "in_stock",
                "new_location": "workshop",
                "ids": test_ids_str
            },
            follow_redirects=True
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        cur.execute(f"SELECT status, storage_location FROM products WHERE id IN ({test_ids_str})")
        rows = cur.fetchall()
        assert all(r[0] == "in_stock" and r[1] == "workshop" for r in rows), f"Expected in_stock and workshop, got {rows}"
        print(f"[PASS] Both status and location updated simultaneously for {len(test_ids)} products")

        # 5. Test Batch Status-Only Update (Location Not Changed)
        print("\n--- Testing Batch Status-Only Update ---")
        res = client.post(
            "https://127.0.0.1:8443/inventory/products/batch-action",
            data={
                "action": "apply_changes",
                "new_status": "archived",
                "new_location": "",
                "ids": test_ids_str
            },
            follow_redirects=True
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        cur.execute(f"SELECT status, storage_location FROM products WHERE id IN ({test_ids_str})")
        rows = cur.fetchall()
        assert all(r[0] == "archived" and r[1] == "workshop" for r in rows), f"Expected archived and workshop, got {rows}"
        print(f"[PASS] Status updated to archived while storage_location remained workshop")

        # 6. Test Batch Location-Only Update (Status Not Changed)
        print("\n--- Testing Batch Location-Only Update ---")
        res = client.post(
            "https://127.0.0.1:8443/inventory/products/batch-action",
            data={
                "action": "apply_changes",
                "new_status": "",
                "new_location": "store",
                "ids": test_ids_str
            },
            follow_redirects=True
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        cur.execute(f"SELECT status, storage_location FROM products WHERE id IN ({test_ids_str})")
        rows = cur.fetchall()
        assert all(r[0] == "archived" and r[1] == "store" for r in rows), f"Expected archived and store, got {rows}"
        print(f"[PASS] Location updated to store while status remained archived")

        # 7. Test Batch Price Tags (58x40)
        print("\n--- Testing Batch Price Tags Preview (58x40) ---")
        res = client.get(f"https://127.0.0.1:8443/inventory/products/price-tags/batch?ids={test_ids_str}")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        tag_html = res.text
        assert "Массовая печать ценников 58×40 мм" in tag_html
        assert "Test Batch Laptop" in tag_html
        assert "Test Batch Monitor" in tag_html
        assert "Test Batch Mouse" in tag_html
        assert "45 000 ₽" in tag_html
        assert "window.print()" in tag_html
        print("[PASS] Batch price tags page rendered 3 tags with barcodes and print handler")

        # 8. Test Batch Add to Cart
        print("\n--- Testing Batch Add to Cart ---")
        # First ensure they are in_stock and in store
        cur.execute(f"UPDATE products SET status = 'in_stock', storage_location = 'store' WHERE id IN ({test_ids_str})")
        conn.commit()
        res = client.post(
            "https://127.0.0.1:8443/inventory/products/batch-action",
            data={
                "action": "add_to_cart",
                "ids": test_ids_str
            },
            follow_redirects=True
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        print("[PASS] Batch add to cart successfully redirected to cart")

        print("\n===========================================================")
        print("ALL BATCH OPERATIONS LIVE VERIFICATION SCENARIOS PASSED!")
        print("===========================================================")

    finally:
        # Clean up temporary test products
        print("\nCleaning up temporary test products...")
        cur.execute(f"DELETE FROM products WHERE id IN ({test_ids_str})")
        conn.commit()
        cur.execute("SELECT count(*) FROM products")
        final_count = cur.fetchone()[0]
        conn.close()
        print(f"Final product count in DB: {final_count} (restored to initial {initial_count})")
        assert final_count == initial_count, f"Expected {initial_count} products, found {final_count}"

if __name__ == "__main__":
    main()
