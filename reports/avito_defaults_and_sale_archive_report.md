# Avito Defaults to In-Stock/Store and Automatic Sale Archiving Report

## 1. Context & Task
User voice request received:
> "И давай еще так: по умолчанию надо будет сделать, чтобы все... статус после импорта с Авито был 'в наличии' и 'в магазине' просто стоял.
> А потом, когда при продаже, он автоматически переносился в архив там, не знаю... в архив, да."

## 2. Changes Made
1. **Core Avito Import (`core/app/routers/integrations.py`):**
   - Changed default product creation status from `"draft"` to `"in_stock"`.
   - Preserved `storage_location = "store"` and `quantity = 1`.
   - New items imported via extension or Core endpoint are immediately available in the catalog and sellable.

2. **Core Sales Lifecycle (`core/app/routers/sales.py`):**
   - In `create_sale`: when product quantity reaches 0, sets `db_product.status = "sold"` and `db_product.storage_location = "archive"`.
   - In `reissue_sale`: when product quantity reaches 0, sets `db_product.status = "sold"` and `db_product.storage_location = "archive"`.
   - In `cancel_sale`: when product quantity is restored to `> 0`, restores `db_product.status = "in_stock"` and moves `storage_location` back to `"store"` if it was `"archive"`.
   - Product events (`ProductEvent`) now log `storage_location` before and after sales, cancellations, and reissues.

3. **Database Migration (`data/db/technoreboot.db`):**
   - Migrated all 46 existing draft Avito products to `status = 'in_stock'` and `storage_location = 'store'`.
   - Verified that all 50 active products currently in the database are in stock and located in the store.

4. **Automated Tests:**
   - `core/tests/test_sales_flow.py`: enhanced to assert `storage_location == "archive"` on sale, and `storage_location == "store"` on cancellation.
   - `core/tests/test_avito_import_upsert.py`: enhanced to assert imported products receive `status == "in_stock"` and `storage_location == "store"`.

5. **Live Verification Script (`scripts/verify_avito_defaults_and_archive_sale_live.py`):**
   - Validated existing database products distribution.
   - Tested Avito import endpoint produces `in_stock` / `store`.
   - Tested sale creation moves item to `sold` / `archive`.
   - Tested sale cancellation restores item to `in_stock` / `store`.
   - Verified Gateway 8443 mTLS endpoint accessibility and catalog rendering.

## 3. Test Suite Results
- `core`: 239 passed (100%)
- `inventory-sales-module`: 151 passed (100%)
- `admin-shell`: 83 passed, 1 skipped (100%)
- Live verification script: all 6 checks passed.
Total automated tests: 473 passed, 0 failed.

## 4. Status
Ready for Owner browser-only acceptance.
