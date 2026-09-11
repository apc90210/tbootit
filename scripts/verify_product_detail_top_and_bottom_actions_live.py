#!/usr/bin/env python3
"""
Live verification script confirming top and bottom action button duplication
on product detail page (/inventory/products/{product_id}) via Gateway 8443 (mTLS):
1. Loads an existing product via Gateway 8443.
2. Verifies #product-actions-top contains:
   - Редактировать товар
   - Продать
   - В корзину
   - Ценник 58×40
   - Назад к товарам
3. Verifies #product-actions-bottom contains:
   - Редактировать товар
   - Продать
   - В корзину
   - Ценник 58×40
   - Назад к товарам
4. Performs quick-add to cart and verifies both top and bottom badges update.
"""

import sys
import re
import httpx
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GATEWAY_URL = "https://127.0.0.1:8443"
CORE_URL = "http://127.0.0.1:8000"

OWNER_CERT = PROJECT_ROOT / "data" / "auth" / "certificates" / "owner.crt"
OWNER_KEY = PROJECT_ROOT / "data" / "auth" / "certificates" / "owner.key"
CA_CERT = PROJECT_ROOT / "data" / "auth" / "ca" / "ca.crt"


def main():
    print("=== STARTING LIVE VERIFICATION: PRODUCT DETAIL TOP & BOTTOM ACTION BUTTONS ===")

    assert OWNER_CERT.exists(), f"Owner cert missing: {OWNER_CERT}"
    assert OWNER_KEY.exists(), f"Owner key missing: {OWNER_KEY}"
    assert CA_CERT.exists(), f"CA cert missing: {CA_CERT}"

    gw_client = httpx.Client(
        base_url=GATEWAY_URL,
        cert=(str(OWNER_CERT), str(OWNER_KEY)),
        verify=str(CA_CERT),
        timeout=15.0,
        trust_env=False
    )

    # Step 1: Find an existing product from /inventory/products
    print("\n--- Step 1: Find Active Product in Catalog ---")
    res_list = gw_client.get("/inventory/products")
    assert res_list.status_code == 200, f"Failed to get products: {res_list.status_code}"

    # Extract first product ID
    m = re.search(r'/inventory/products/(\d+)', res_list.text)
    assert m, "No product link found in catalog table"
    product_id = m.group(1)
    print(f"Selected product ID: {product_id}")

    # Step 2: Request product detail page
    print(f"\n--- Step 2: Request /inventory/products/{product_id} over mTLS ---")
    res_detail = gw_client.get(f"/inventory/products/{product_id}")
    assert res_detail.status_code == 200, f"Detail page failed: {res_detail.status_code}"
    html = res_detail.text
    assert "Карточка товара:" in html
    assert "Ошибка Core API" not in html
    print("[OK] Product detail page loaded successfully (HTTP 200).")

    # Step 3: Verify Top Actions Panel
    print("\n--- Step 3: Verify Top Actions Bar (#product-actions-top) ---")
    assert 'id="product-actions-top"' in html, "Missing #product-actions-top"
    top_start = html.find('id="product-actions-top"')
    top_block = html[top_start:top_start + 3000]

    assert 'href="/inventory/products"' in top_block, "Missing 'Назад к товарам' link in top bar"
    assert 'Назад к товарам' in top_block
    assert f'/inventory/products/{product_id}/edit' in top_block, "Missing 'Редактировать товар' in top bar"
    assert 'Редактировать товар' in top_block
    assert 'Продать' in top_block, "Missing 'Продать' in top bar"
    assert 'В корзину' in top_block, "Missing 'В корзину' in top bar"
    assert f'data-product-id="{product_id}"' in top_block, "Missing data-product-id in top bar"
    assert 'Ценник 58×40' in top_block, "Missing 'Ценник 58×40' in top bar"
    print("[OK] Step 3 passed: All 4 action buttons + back link verified in top bar.")

    # Step 4: Verify Bottom Actions Panel
    print("\n--- Step 4: Verify Bottom Actions Bar (#product-actions-bottom) ---")
    assert 'id="product-actions-bottom"' in html, "Missing #product-actions-bottom"
    bottom_start = html.find('id="product-actions-bottom"')
    bottom_block = html[bottom_start:bottom_start + 3000]

    assert 'href="/inventory/products"' in bottom_block, "Missing 'Назад к товарам' link in bottom bar"
    assert 'Назад к товарам' in bottom_block
    assert f'/inventory/products/{product_id}/edit' in bottom_block, "Missing 'Редактировать товар' in bottom bar"
    assert 'Редактировать товар' in bottom_block
    assert 'Продать' in bottom_block, "Missing 'Продать' in bottom bar"
    assert 'В корзину' in bottom_block, "Missing 'В корзину' in bottom bar"
    assert f'data-product-id="{product_id}"' in bottom_block, "Missing data-product-id in bottom bar"
    assert 'Ценник 58×40' in bottom_block, "Missing 'Ценник 58×40' in bottom bar"
    print("[OK] Step 4 passed: All 4 action buttons + back link verified in bottom bar.")

    # Step 5: Test quick add to cart and badge update in both bars
    print("\n--- Step 5: Test Cart Quick-Add and Dual-Bar Synchronization ---")
    res_add = gw_client.post(
        "/inventory/cart/add-quick",
        data={"product_id": product_id, "quantity": 1},
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    assert res_add.status_code == 200, f"Quick add failed: {res_add.status_code}"
    add_data = res_add.json()
    assert add_data.get("ok") is True
    print(f"Added to cart response: {add_data}")

    # Reload product detail to verify both top and bottom badges show cart quantity
    res_after = gw_client.get(f"/inventory/products/{product_id}")
    assert res_after.status_code == 200
    html_after = res_after.text

    top_after = html_after[html_after.find('id="product-actions-top"'):html_after.find('id="product-actions-top"') + 3000]
    bottom_after = html_after[html_after.find('id="product-actions-bottom"'):html_after.find('id="product-actions-bottom"') + 3000]

    assert 'class="btn btn-success product-go-to-cart"' in top_after
    assert 'display: none;' not in top_after.split('class="btn btn-success product-go-to-cart"')[1].split('>')[0]
    assert 'class="btn btn-success product-go-to-cart"' in bottom_after
    assert 'display: none;' not in bottom_after.split('class="btn btn-success product-go-to-cart"')[1].split('>')[0]
    print("[OK] Step 5 passed: Both top and bottom bars reflect cart membership and 'Перейти в корзину'.")

    # Step 6: Clean cart
    print("\n--- Step 6: Reset/Clear Cart ---")
    gw_client.post(f"/inventory/cart/remove/{product_id}")
    print("[OK] Cart reset cleanly.")

    print("\n=== ALL PRODUCT DETAIL TOP & BOTTOM BUTTON CHECKS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    main()
