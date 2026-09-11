#!/usr/bin/env python3
"""
Live verification script for:
1. Default Avito import creates product with status='in_stock' and storage_location='store'.
2. Selling a product moves product status='sold' and storage_location='archive'.
3. Cancelling a sale restores product status='in_stock' and storage_location='store'.
4. Existing products verification (50 items are in_stock/store).
5. Gateway 8443 mTLS endpoint accessibility and catalog rendering.
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
    print("=== STARTING LIVE VERIFICATION ===")
    
    # 1. Connect to DB and check existing products
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT count(*), status, storage_location FROM products GROUP BY status, storage_location")
    groups = cur.fetchall()
    print(f"Current DB product distributions (count, status, storage_location): {groups}")
    
    # Check that all existing 50 products are in_stock and store
    cur.execute("SELECT count(*) FROM products WHERE status = 'in_stock' AND storage_location = 'store'")
    in_stock_store_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM products")
    total_count = cur.fetchone()[0]
    print(f"Total products: {total_count}, In stock & in store: {in_stock_store_count}")
    assert total_count == in_stock_store_count, f"Expected all {total_count} products to be in_stock and store, found {in_stock_store_count}"
    print("[OK] Existing products check PASSED")

    # 2. Test Avito import endpoint default values
    test_external_id = "test-live-auto-archive-999"
    payload = {
        "account_key": "account_laptops",
        "external_item_id": test_external_id,
        "external_url": f"https://www.avito.ru/item/{test_external_id}",
        "remote_status": "active",
        "title": "Автотест Товар для Проверки Архивации",
        "price": 9999.0,
        "description": "Тестовое описание",
        "parameters": {"Тест": "Да"}
    }

    core_client = httpx.Client(base_url=CORE_URL, timeout=10.0, trust_env=False)
    
    import_res = core_client.post("/api/integrations/avito/import-item", json=payload)
    print(f"Import response: {import_res.status_code} {import_res.text}")
    assert import_res.status_code == 200
    import_data = import_res.json()
    product_id = import_data["product_id"]
    print(f"Imported product ID: {product_id}")

    # Fetch product details
    prod_res = core_client.get(f"/api/products/{product_id}")
    assert prod_res.status_code == 200
    prod_data = prod_res.json()
    print(f"Imported product state: status='{prod_data.get('status')}', storage_location='{prod_data.get('storage_location')}'")
    assert prod_data.get("status") == "in_stock", f"Expected in_stock, got {prod_data.get('status')}"
    assert prod_data.get("storage_location") == "store", f"Expected store, got {prod_data.get('storage_location')}"
    print("[OK] Avito import default status='in_stock' and storage_location='store' PASSED")

    # 3. Test Sale flow -> should move to archive
    sale_payload = {
        "total_amount": 9999.0,
        "payment_method": "card",
        "comment": "Live test sale",
        "items": [
            {
                "product_id": product_id,
                "title": prod_data.get("title"),
                "price": 9999.0,
                "quantity": 1
            }
        ]
    }
    sale_res = core_client.post("/api/sales/", json=sale_payload)
    print(f"Sale response: {sale_res.status_code} {sale_res.text}")
    assert sale_res.status_code == 200
    sale_data = sale_res.json()
    sale_id = sale_data["id"]
    print(f"Created sale ID: {sale_id}")

    # Check product state after sale
    prod_res = core_client.get(f"/api/products/{product_id}")
    assert prod_res.status_code == 200
    prod_data = prod_res.json()
    print(f"Product state after sale: status='{prod_data.get('status')}', storage_location='{prod_data.get('storage_location')}'")
    assert prod_data.get("status") == "sold", f"Expected sold, got {prod_data.get('status')}"
    assert prod_data.get("storage_location") == "archive", f"Expected archive, got {prod_data.get('storage_location')}"
    print("[OK] Product automatic move to archive upon sale PASSED")

    # 4. Test Cancel sale flow -> should restore to in_stock & store
    cancel_res = core_client.post(f"/api/sales/{sale_id}/cancel", json={"reason": "Live test cancellation"})
    print(f"Cancel response: {cancel_res.status_code} {cancel_res.text}")
    assert cancel_res.status_code == 200

    # Check product state after cancel
    prod_res = core_client.get(f"/api/products/{product_id}")
    assert prod_res.status_code == 200
    prod_data = prod_res.json()
    print(f"Product state after cancel: status='{prod_data.get('status')}', storage_location='{prod_data.get('storage_location')}'")
    assert prod_data.get("status") == "in_stock", f"Expected in_stock, got {prod_data.get('status')}"
    assert prod_data.get("storage_location") == "store", f"Expected store, got {prod_data.get('storage_location')}"
    print("[OK] Product restore to in_stock and store upon cancellation PASSED")

    # 5. Gateway 8443 mTLS verification
    print("Testing Gateway 8443 with Owner certificate...")
    gateway_client = httpx.Client(
        cert=(str(OWNER_CRT), str(OWNER_KEY)),
        verify=False,
        trust_env=False,
        timeout=15.0
    )
    gw_res = gateway_client.get(f"{GATEWAY_URL}/inventory/products")
    print(f"Gateway /inventory/products response code: {gw_res.status_code}")
    assert gw_res.status_code == 200
    assert "Товары" in gw_res.text or "products" in gw_res.text
    print("[OK] Gateway 8443 mTLS access PASSED")

    # 6. Teardown test product and test sale
    print("Cleaning up test records from DB...")
    cur.execute("DELETE FROM sale_items WHERE sale_id = ?", (sale_id,))
    cur.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
    cur.execute("DELETE FROM product_events WHERE product_id = ?", (product_id,))
    cur.execute("DELETE FROM product_external_listings WHERE product_id = ?", (product_id,))
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    print("[OK] Cleanup completed successfully")
    print("=== ALL LIVE VERIFICATION CHECKS PASSED ===")

if __name__ == "__main__":
    main()
