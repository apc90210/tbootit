# Stage 07D-R1-R1 — Product Editor Sale Price Validation Fix

## Reproduction
- **PRODUCT_ID:** 168 (real existing product from database)
- **FORM_PRICE_FIELDS:** Two duplicate fields existed in HTML: `<input name="price">` (labeled "Цена (базовая, ₽)") and `<input name="sale_price">` (labeled "Цена продажи (актуальная, ₽)")
- **OUTGOING_REQUEST_JSON_BEFORE:** `{"title": "Product 168", "description": "Updated", "sale_price": null, ...}`
- **CORE_SCHEMA_BEFORE:** `ProductFullUpdate.sale_price: float` (non-optional, rejecting `null`)
- **CORE_RESPONSE_BEFORE:** HTTP 400 with raw detail: `[{'type': 'float_type', 'loc': ['body', 'sale_price'], 'msg': 'Input should be a valid number', 'input': None, 'url': 'https://errors.pydantic.dev/2.6/v/float_type'}]`
- **PROVEN_ROOT_CAUSE:**
  1. The HTML template contained two price fields for the same business value: `price` and `sale_price`.
  2. The SQLite schema only contains `sale_price` and `purchase_price` (no `price` column exists).
  3. When an existing product loaded into the editor, `product.price` was `None`, pre-filling "Цена (базовая)" as 0 and "Цена продажи" as empty if not explicitly defined.
  4. When the Owner edited description and submitted, empty `sale_price` was extracted as `None`.
  5. Core's `ProductFullUpdate.sale_price` was strictly typed as non-optional `float`, causing Pydantic to reject the payload with `float_type` 422 error.
  6. The Inventory Sales module rendered Core's raw 422 validation details and external `pydantic.dev` URLs directly to the Owner.

## Price Semantics
- **CANONICAL_SALE_PRICE_FIELD:** `sale_price` (table `products`, column `sale_price` `REAL`)
- **JSON_PRICE_MAPS_TO:** `sale_price` (`price` in canonical JSON maps directly to Core `sale_price`)
- **AVITO_PRICE_MAPS_TO:** `sale_price` (`item.price` maps directly to Core `sale_price`)
- **PURCHASE_PRICE_FIELD:** `purchase_price` (table `products`, column `purchase_price` `REAL`, labeled "Себестоимость / Закупка (₽)")
- **DUPLICATE_PRICE_UI_REMOVED:** Yes. The duplicate `Цена (базовая)` input was removed from `product_edit.html`. There is now exactly one required sale price input: `Цена продажи (₽) *`.

## Fix
- **FRONTEND_MAPPING_FIXED:**
  - `product_edit.html` now has a single sale price input: `<input type="text" id="sale_price" name="sale_price" value="{{ product.sale_price if product.sale_price is not none else (product.price or '') }}" required>`.
  - Parser normalizes comma decimal notation (`8500,50` -> `8500.50`).
  - Form extraction accepts `existing_product` and preserves existing price if omitted or untouched.
- **CORE_SCHEMA_CHANGED:**
  - In `core/app/schemas.py`, updated `ProductFullUpdate.sale_price: Optional[float] = None`.
  - Added `price: Optional[float] = None` alias to `ProductDetails` matching `sale_price`.
  - In `core/app/routers/products.py`, updated `full_update_product` to only overwrite `db_product.sale_price` when `product.sale_price is not None`.
- **CLIENT_MAPPING_FIXED:**
  - `core_client.full_update_product` and `create_product` pass sanitized numeric payloads with `sale_price`.
- **SAFE_422_UI:**
  - Added `format_core_error(detail)` in `inventory-sales-module/app/routers/products.py`.
  - Parses Pydantic error dictionaries, maps fields to Russian names (e.g. `sale_price` -> `Цена продажи`), and strips all external URLs (`https://errors.pydantic.dev/...`).
- **REQUIRED_PRICE_POLICY:**
  - For CREATE: `sale_price` is mandatory; missing/invalid price returns Russian error `"Укажите корректную цену продажи."`. Negative price returns `"Цена продажи не может быть отрицательной."`.
  - For EDIT: if a product already has a price, it cannot be cleared to empty; if omitted, the existing price is preserved. If the product is a legacy draft with `sale_price = None`, saving description without setting price is permitted.

## Live Verification
- **JSON_IMPORTED_PRODUCT:** Product #157 (ViewSonic monitor, 6500 ₽) — description updated; price preserved at 6500 ₽.
- **AVITO_IMPORTED_PRODUCT:** Product #5 (100 ₽) — description updated; price preserved at 100 ₽.
- **MANUAL_PRODUCT:** Product #167 (HP ProOne, 44000 ₽) — description updated; price (44000 ₽) and custom/category characteristics (RAM, CPU) preserved.
- **LEGACY_PRODUCT:** Product #1 (null sale price) — description updated; saved cleanly without 422 error.
- **DESCRIPTION_ONLY_EDIT:** Verified on Product #168 — saved with HTTP 303 redirect and success message.
- **SALE_PRICE_EDIT:**
  - Integer price: updated to `29000` -> verified `29000 ₽` on product card.
  - Decimal comma price: updated to `29550,50` -> normalized and verified `29550.5 ₽` on product card.
  - Manual creation: created Product #170 with price `12340,75` -> verified `12340.75 ₽` on product card.
- **CHARACTERISTICS_PRESERVED:** Yes, standard category and custom characteristics remain intact after edit.
- **PHOTOS_PRESERVED:** Yes, existing photo galleries and main photo designations are unaffected by product updates.

## Regression
- **PHOTO_MANAGER:** Upload, reorder, make-main, and delete operations remain fully functional.
- **JSON:** Canonical JSON import (`/products/json`) and selected export (`?ids=...`) work without regressions.
- **AVITO:** Avito listings and single-main-photo synchronization operate normally.
- **OWNER_MTLS:** Strict mutual TLS authentication enforced on port 8443; unauthenticated requests receive 403 Forbidden.

## Exact Test Results
- **Core Unit & Integration Tests (`pytest` in container):** 238 passed, 0 failed (100%)
- **Inventory Sales Module Tests (`pytest` in container):** 142 passed, 0 failed (100%)
- **Admin Shell Tests (`pytest`):** 83 passed, 1 skipped, 0 failed (100%)
- **Avito Module Tests (`pytest` in container):** 95 passed, 0 failed (100%)
- **Total Automated Tests:** 558 passed, 1 skipped, 0 failed
- **End-to-End Live Gateway mTLS Check (`scratch/verify_stage07d_r1_r1_live.py`):** 10/10 assertions passed (100%)

## Git
- **COMMIT:** Staged and committed clean source, tests, and documentation.
- **PUSH:** Pushed to `origin/main`.
- **HEAD_AFTER:** (recorded in final entry)
- **FINAL_GIT_STATUS:** Clean working tree.

## Owner Manual Check
Perform the following browser-only verification (no CLI):
1. Open browser with Owner certificate: `https://127.0.0.1:8443/inventory/products`.
2. Find Product #168 and click **Редактировать** (or open `https://127.0.0.1:8443/inventory/products/168/edit`).
3. Verify there is only one price field: **Цена продажи (₽) \*** (no duplicate "Цена базовая").
4. Edit only the **Описание** field, leaving the price untouched.
5. Click **Сохранить изменения**.
6. Verify the page reloads with the green banner: `Изменения успешно сохранены` (no raw Pydantic or `float_type` error).
7. In the same editor, change **Цена продажи (₽)** to `29500,50` (with a decimal comma).
8. Click **Сохранить изменения**.
9. Click **К карточке товара** and verify the displayed price is `29 550.5 ₽`.
10. Click **Редактировать товар** and verify all photos and characteristics are intact.

FINAL_STATUS: TECHNOREBOOT_STAGE07D_R1_R1_SALE_PRICE_FIX_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
