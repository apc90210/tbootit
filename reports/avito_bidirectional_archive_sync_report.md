# Avito Bidirectional Archive Synchronization Report

## 1. Context & Request
Owner voice request received:
> "И еще проверь такая схема: если у нас какое-то, допустим, объявление есть в базе, оно в архиве, но мы его повторно импортируем с Авито, оно просто обновляет данные данного объявления и делает его активным в магазине? То есть, например, мы товар продали на Авито, потом сделали его активным, но потом через Авито мы можем его обратно автоматически выдернуть из архива на продажу как будто бы. Вот. И также обратный механизм..."

## 2. Core Implementation
In `core/app/routers/integrations.py`:
1. **Status Categorization:**
   - Detects if remote Avito status is active: `remote_status == "active"` or raw text contains "активно".
   - Detects if remote Avito status is inactive/closed/archived: `remote_status in ["inactive", "closed", "archived", "blocked", "removed", "sold", "old"]` or raw text contains "завершено", "архив", "снято", "неактивно", "заблокировано", "отклонено".
2. **Reactivation (Archive -> Store):**
   - When an existing product is in archive (`storage_location == "archive"`, `status in ["sold", "draft", "archived"]`, or `quantity <= 0`) and is re-imported from Avito as active:
     - Sets `status = "in_stock"`
     - Sets `storage_location = "store"`
     - Sets `quantity = max(quantity, 1)`
     - Updates listing data (price, title, description, parameters, photos)
     - Logs `ProductEvent` with `event_type = "avito_reactivated"`
   - **Ledger Integrity:** Historical `Sale` and `SaleItem` records remain immutable.
3. **Archiving (Store -> Archive):**
   - When an existing product is currently active in store (`status == "in_stock"` or `storage_location != "archive"`) and is re-imported from Avito with an inactive/closed status:
     - Sets `status = "sold"`
     - Sets `storage_location = "archive"`
     - Sets `quantity = 0`
     - Logs `ProductEvent` with `event_type = "avito_archived"`
4. **Initial Import of Inactive Listing:**
   - If an inactive listing is imported from Avito for the first time, it is created directly in the archive (`status = "sold"`, `storage_location = "archive"`, `quantity = 0`).
5. **Photo Import Deduplication Hardening:**
   - Ensured that when a new product is created (`created_product = True`), any stale orphan photo records matching the auto-increment ID are cleared, guaranteeing photo downloads succeed reliably for fresh imports.

## 3. Automated Test Suite Results
- `core/tests/test_avito_archive_reactivation_and_reverse_sync.py`: Added comprehensive lifecycle tests for both reactivation and reverse archive synchronization.
- `core/tests/test_avito_import_upsert.py`: Updated upsert test cases for active and inactive re-imports.
- **Test Results:**
  - `core` container: 241 passed, 0 failed (100%)
  - `inventory-sales-module` container: 151 passed, 0 failed (100%)
  - `admin-shell` host suite: 83 passed, 1 skipped (100%)
  - Total automated unit/integration tests: 475 passed, 0 failed.

## 4. Live Verification Against Running Containers
Script `scripts/verify_avito_bidirectional_archive_sync_live.py` executed against live Gateway 8443 and Core:
- Step 1: Product imported as active -> `in_stock`, `store`, `quantity=1` [PASSED]
- Step 2: Sold via checkout -> `sold`, `archive`, `quantity=0` [PASSED]
- Step 3: Re-imported from Avito as active -> reactivated: `in_stock`, `store`, `quantity=1`, `avito_reactivated` event logged [PASSED]
- Step 4: Re-imported from Avito as inactive -> archived: `sold`, `archive`, `quantity=0`, `avito_archived` event logged [PASSED]
- Step 5: Re-imported from Avito as active again -> reactivated: `in_stock`, `store`, `quantity=1` [PASSED]
- Step 6: Brand new inactive listing imported -> directly created in archive: `sold`, `archive`, `quantity=0` [PASSED]
- Step 7: Gateway 8443 mTLS access with Owner certificate: HTTP 200 OK [PASSED]
- Step 8: Clean teardown of test records [PASSED]

## 5. Acceptance Status
Ready for Owner verification in browser. Zero CLI required.
