# Stage 07C-R1-R3 Report — JSON Create/Open UX & Product List Shortcut

## Executive Summary

Stage 07C-R1-R3 has been successfully implemented, verified, and regression-tested across all system components. The Owner can now:
1. Immediately open newly created products directly from the JSON import results table in a separate browser tab (`target="_blank" rel="noopener noreferrer"`), while keeping the `/products/json` page and its entire results state open.
2. Directly navigate to `/products/json` from the main `/inventory/products` list via a prominent `+ Добавить новый товар через JSON` button placed at the top next to existing quick controls (*Магазин*, *Мастерская*, *Архив*, *Черновики*).

---

## Requirement Checklist

### Requirement A — Open Newly Created Product Immediately
- `CREATED_ROW_OPEN_BUTTON`: `true` (`<a href="/inventory/products/${prodId}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm btn-open-product">↗ Открыть товар</a>`)
- `USES_REAL_PRODUCT_ID`: `true` (uses `product_id` returned directly from Core service response)
- `OPENS_NEW_TAB`: `true` (uses `target="_blank"` with `rel="noopener noreferrer"`)
- `BATCH_ROWS_LINK_CORRECTLY`: `true` (verified multi-product batch creation where each row renders its specific product link)
- `ERROR_ROWS_SAFE`: `true` (skipped/error rows without valid product entities render a safe dash `—` without misleading links)

### Requirement B — JSON Create Shortcut in Main Product List
- `PRODUCT_LIST_SHORTCUT_VISIBLE`: `true` (placed in top quick controls bar)
- `SHORTCUT_LABEL`: `+ Добавить новый товар через JSON`
- `SHORTCUT_TARGET`: `/products/json`
- `EXISTING_TOP_CONTROLS_PRESERVED`: `true` (*Все*, *Магазин*, *Мастерская*, *Архив*, *Черновики* fully present and intact)

---

## Exact Test Suite Results

1. **`admin-shell` (Full Suite):** 82 passed, 1 skipped, 0 failed
   - `admin-shell/tests/test_products_json_ui.py`: 13 passed, 0 failed
2. **`core` (Full Suite):** 228 passed, 0 failed
3. **`inventory-sales-module` (Full Suite):** 125 passed, 0 failed
   - `inventory-sales-module/tests/test_products_routes.py`: 4 passed, 0 failed
4. **`avito-module` (Full Suite):** 95 passed, 0 failed
5. **Live Gateway mTLS Testing (`https://127.0.0.1:8443`):**
   - Unauthenticated access to `/inventory/products` & `/products/json`: `403 Forbidden` (PASS)
   - Owner mTLS access to `/inventory/products`: `200 OK` (PASS)
   - Owner mTLS access to `/products/json`: `200 OK` (PASS)
   - 2-product batch import: `200 OK` (`created: 2`, IDs: 157, 158) (PASS)
   - Product detail retrieval for created products: `200 OK` (PASS)
   - Selected export (`?ids=157,158`): `200 OK` (PASS)
   - Full catalog export: `200 OK` (148 products) (PASS)

**Total Automated Unit/Integration Tests Passing:** 530 passed, 1 skipped.

---

## Owner Manual Check Instructions (Browser-Only)

1. Open the main product catalog in the browser: `https://127.0.0.1:8443/inventory/products`.
2. Confirm the green button `+ Добавить новый товар через JSON` is visible at the top next to the quick filters (*Магазин*, *Мастерская*, *Архив*, *Черновики*).
3. Click `+ Добавить новый товар через JSON` and confirm you are navigated to `https://127.0.0.1:8443/products/json`.
4. Import a test product payload via JSON or file upload.
5. In the import results table, locate the created product row and click `↗ Открыть товар`.
6. Confirm the product detail card opens in a **NEW browser tab** (`/inventory/products/{product_id}`).
7. Return to the previous tab and confirm `/products/json` remains open with the import summary and result rows completely preserved.
8. Import two products simultaneously; confirm both rows in the results table link to their respective distinct product cards.
