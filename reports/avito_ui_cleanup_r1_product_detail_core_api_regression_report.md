# Technoreboot — Avito UI Cleanup R1: Product Detail / Core API Regression Fix Report

**Date:** `2026-08-14`  
**Repository:** `C:\tbootit`  
**Stage:** `Avito UI Cleanup R1: Fix Product Button / Core API Regression`  

---

## 1. STATUS & SUMMARY

```text
FINAL_STATUS:
TECHNOREBOOT_AVITO_UI_CLEANUP_R1_PRODUCT_DETAIL_FIXED_READY_FOR_OWNER_CHECK

OWNER_PRODUCT_CLICK_WORKS: true
PRODUCT_DETAIL_ROUTE_200: true
CORE_API_ERROR_ELIMINATED: true
PRODUCT_58_OPENS_CORRECTLY: true
PHOTO_GALLERY_STILL_WORKS: true
PLUGIN_ONLY_AVITO_UI_PRESERVED: true
LEGACY_AVITO_UI_STILL_HIDDEN: true
R9_CORE_MODEL_PRESERVED: true
EXTENSION_UNCHANGED_OR_JUSTIFIED: true
OWNER_MANUAL_CHECK_REQUIRED: true

PROJECT_NEXT_STEP_AFTER_OWNER_ACCEPTANCE:
RESUME_STAGE06A_R9_R1
```

---

## 2. FAILED LAYER & DIAGNOSTIC DETAILS

- **OWNER_ERROR:** Clicking on a product link or navigating to `http://localhost:8011/inventory/products/58` displayed error page: `"Ошибка Core API"`.
- **FAILED_URL:** `http://localhost:8011/inventory/products/58` (proxied to `inventory-sales-module` `GET /products/58`, which requests `GET /api/products/58/details` on `core`).
- **FAILED_SERVICE:** `core`
- **FAILED_ENDPOINT:** `GET /api/products/{id}/details` (and `GET /api/products/`)
- **HTTP_STATUS:** `500 Internal Server Error`
- **TRACEBACK:**
  ```text
  File "/app/app/routers/products.py", line 321, in get_product_details
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
  sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: products.avito_category_id
  ```

---

## 3. ROOT CAUSE & REGRESSION MECHANISM

- **ROOT_CAUSE:** In Stage06A-R9 commit (`b698649`), column `avito_category_id` was added to `models.Product` in `core/app/models.py`. However, `avito_category_id` was missing from the `prod_updates` list in `migrate_db()` inside `core/app/main.py`.
- **REGRESSION_MECHANISM:** Because SQLite `Base.metadata.create_all` only creates *new* tables and does not perform `ALTER TABLE` on existing tables, running existing SQLite databases (`technoreboot.db`) lacked column `avito_category_id` on table `products`. Whenever `get_product_details(58)` was queried by `inventory-sales-module`, SQLAlchemy attempted to select `products.avito_category_id`, causing SQLite to raise `no such column: products.avito_category_id` (500). `inventory-sales-module` caught the 500 error and rendered `error.html` with `"Ошибка Core API"`.

---

## 4. FIX & IMPLEMENTATION

- **CORE_FIX:** Added `("avito_category_id", "INTEGER")` to `prod_updates` in `migrate_db()` in `core/app/main.py`.
- **BEHAVIOR:** When `core` container starts up, `migrate_db()` automatically runs `ALTER TABLE products ADD COLUMN avito_category_id INTEGER;` if the column does not already exist on existing SQLite databases.
- **REGRESSION_TEST:** Added `admin-shell/tests/test_owner_product_detail_route.py` testing product listing link presence, product detail page GET 200, Product 58 GET 200, and absence of `"Ошибка Core API"`.

---

## 5. CODE & EXTENSION STATE

- **EXTENSION_CODE_CHANGED:** `false` (No chrome-extension runtime code modified).
- **EXTENSION_VERSION:** `0.1.11` (Unchanged).
- **PLUGIN_ONLY_UI:** Preserved 100%. Only `Расширение Avito` (`/avito/extension`) appears in navigation.

---

## 6. TEST EXECUTION SUMMARY

| Test Suite | Total Tests | Passed | Failed | Result |
| :--- | :---: | :---: | :---: | :---: |
| **Core Safe Pytest** | 185 | 185 | 0 | **PASS** |
| **Inventory & Sales Module** | 119 | 119 | 0 | **PASS** |
| **Avito Module** | 83 | 83 | 0 | **PASS** |
| **Repairs Module** | 34 | 34 | 0 | **PASS** |
| **Admin Shell UI & Proxy** | 55 | 55 | 0 | **PASS** |
| **Chrome Extension** | 27 | 27 | 0 | **PASS** |
| **Total** | **503** | **503** | **0** | **PASS** |

---

## 7. OWNER CHECK GUIDE

1. Open Technoreboot Admin Shell at `http://localhost:8011/`.
2. Click on **"Товары"** (`/inventory/products`).
3. Click on any product link in the table (e.g. Product 58: `http://localhost:8011/inventory/products/58`).
4. Verify the product detail page opens cleanly with 200 OK, showing product title, SKU, barcode, price tag generation link, and photo gallery — without `"Ошибка Core API"`.
5. Verify top navigation still displays only **"Расширение Avito"** without legacy sync/parser links.
