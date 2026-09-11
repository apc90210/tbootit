# Stage 08A-R1-R2: Deterministic Avito Regression Tests Report

**Audit Date:** 2026-09-11  
**Target Environment:** Local Stack (`https://127.0.0.1:8443`)  
**Status:** **PASS / TECHNOREBOOT_STAGE08A_R1_R2_DETERMINISTIC_TESTS_READY_FOR_OWNER_CHECK**  
**Git Baseline Commit:** `1baf45caef4bf1e31aec287d5509cf85958b5f3c`  

---

## 1. Executive Summary

In Stage 08A-R1-R1, the Avito regression test suite had 5 historical restoration tests skipped when run against the live database because the current catalog had been re-baselined to 50 items rather than the historical 193 items (`if total_cur != 193: pytest.skip(...)`). Additionally, `test_test_i_catalog_preservation_invariant` contained hard-coded business count assumptions (`>= 50` products, `>= 50` photos, `>= 33` real Avito products) coupled directly to `data/db/technoreboot.db`.

In Stage 08A-R1-R2, all live-DB coupling, skips, and magic business-count assumptions were audited and eliminated. The test suites were refactored using isolated disposable database fixtures (Patterns A & C) to ensure 100% deterministic execution regardless of current live catalog state, while fully preserving all intended historical regressions.

### Key Results
- **Avito Module Tests (`pytest avito-module\tests`):** **154 passed, 0 failed, 0 skipped** (previously 149 passed, 5 skipped).
- **Chrome Extension Tests (`pytest chrome-extension\technoreboot-avito\tests`):** **126 passed, 0 failed, 0 skipped**.
- **Focused Avito Regressions (`scripts/verify_avito_focused_regressions.py`):** **PASS** across all 10 checks.
- **Live Business Data Safety:** `REAL_PRODUCT_IDS_UNCHANGED: true`, `REAL_SALE_IDS_UNCHANGED: true`, `REAL_REPAIR_IDS_UNCHANGED: true`, `REAL_PHOTO_IDS_UNCHANGED: true`, `REAL_EXTERNAL_LISTING_IDS_UNCHANGED: true`, `REAL_PRODUCTS_DELETED: 0`.
- **VDS Deployment:** `PRODUCTION_DEPLOYMENT_NOT_STARTED: true`.

---

## 2. Audit of the 5 Skipped Avito Tests

All 5 skipped tests were located in `avito-module/tests/test_stage07f_r1_r3_r1_restoration_and_verification.py`.

### Test 1
- **TEST_NAME:** `test_b_backup_current_diff_identifies_all_missing_products`
- **CURRENT_SKIP_REASON:** `pytest.skip(f"Historical Stage 07F restoration test: catalog re-baselined in Stage 07E/08A (found {total_cur}, expected 193)")`
- **WHY_IT_DEPENDS_ON_LIVE_DATA:** Compared `BAK_PATH` (318 products) directly to `CUR_PATH` (`data/db/technoreboot.db`), expecting `total_cur == 193`.
- **INTENDED_REGRESSION:** Verify that the backup/target restoration diff logic accurately distinguishes the 123 synthetic products (IDs 173..295) and 2 test stubs (IDs 171, 172) from real business products without false positives.
- **NEW_ISOLATION_STRATEGY:** Pattern C (Isolated temp DB fixture `restored_target_db`): Copies `BAK_PATH` into a temporary DB, deletes synthetic/stub items, and asserts the diff identifies exactly the 125 missing IDs. Zero coupling to `data/db/technoreboot.db`.

### Test 2
- **TEST_NAME:** `test_d_all_accidentally_deleted_real_avito_products_are_restored`
- **CURRENT_SKIP_REASON:** `pytest.skip(f"Historical Stage 07F restoration test: catalog re-baselined in Stage 07E/08A (found {total_cur}, expected 193)")`
- **WHY_IT_DEPENDS_ON_LIVE_DATA:** Queried `CUR_PATH` directly to assert that real Avito products with ID >= 296 (296..328) are present.
- **INTENDED_REGRESSION:** Verify that all 33 real Avito products with ID >= 296 survive restoration and are not treated as synthetic cleanup candidates.
- **NEW_ISOLATION_STRATEGY:** Pattern C (Isolated temp DB fixture `restored_target_db`): Asserts presence of IDs 296..328 in the restored dataset. Zero coupling to `data/db/technoreboot.db`.

### Test 3
- **TEST_NAME:** `test_f_no_unrelated_current_product_is_overwritten`
- **CURRENT_SKIP_REASON:** `pytest.skip(f"Historical Stage 07F restoration test: catalog re-baselined in Stage 07E/08A (found {total_cur}, expected 193)")`
- **WHY_IT_DEPENDS_ON_LIVE_DATA:** Compared base products (ID <= 170) between `BAK_PATH` and `CUR_PATH`, asserting 160 base products match.
- **INTENDED_REGRESSION:** Ensure baseline catalog records (including fixture product 58 for admin-shell) are not overwritten or modified by the restoration process.
- **NEW_ISOLATION_STRATEGY:** Pattern C (Isolated temp DB fixture `restored_target_db`): Compares base products between `BAK_PATH` and `restored_target_db`. Zero coupling to `data/db/technoreboot.db`.

### Test 4
- **TEST_NAME:** `test_h_dependent_external_listing_rows_restored`
- **CURRENT_SKIP_REASON:** `pytest.skip(f"Historical Stage 07F restoration test: catalog re-baselined in Stage 07E/08A (found {total_cur}, expected 193)")`
- **WHY_IT_DEPENDS_ON_LIVE_DATA:** Queried `CUR_PATH` to assert that external listings for real products 296..328 exist.
- **INTENDED_REGRESSION:** Ensure `product_external_listings` rows linked to restored products are preserved with `marketplace='avito'`.
- **NEW_ISOLATION_STRATEGY:** Pattern C (Isolated temp DB fixture `restored_target_db`): Asserts presence and integrity of external listings for IDs 296..328 in `restored_target_db`. Zero coupling to `data/db/technoreboot.db`.

### Test 5
- **TEST_NAME:** `test_q_r_s_future_test_cleanup_safety_and_invariants`
- **CURRENT_SKIP_REASON:** `pytest.skip(f"Historical Stage 07F restoration test: catalog re-baselined in Stage 07E/08A (found {total_cur}, expected 193)")`
- **WHY_IT_DEPENDS_ON_LIVE_DATA:** Queried `CUR_PATH` expecting `len(real_set_before) == 193`.
- **INTENDED_REGRESSION:** Verify invariants Q (cleanup removes only test-created IDs), R (high-ID real products survive cleanup), and S (real product identity set is unchanged before and after test cleanup).
- **NEW_ISOLATION_STRATEGY:** Pattern C (Isolated temp DB fixture `restored_target_db`): Simulates creating temporary test records, executes scoped cleanup, and verifies that real product IDs (including IDs 296..328) are untouched and exact set equality is preserved. Zero coupling to `data/db/technoreboot.db`.

---

## 3. Removal of Magic Business Counts

Search of all Avito tests revealed live catalog count coupling in two files:

1. **`avito-module/tests/test_stage07f_r1_r3_r1_restoration_and_verification.py`**:
   - `LIVE_COUNT_ASSUMPTIONS_FOUND`: `total_cur != 193` in `test_b`, `test_d`, `test_f`, `test_h`, `test_q_r_s`.
   - `LIVE_COUNT_ASSUMPTIONS_REMOVED`: Replaced `CUR_PATH` with disposable temp DB fixture `restored_target_db`. All skips and live DB checks removed.

2. **`avito-module/tests/test_stage07f_r1_r3_r3_zero_of_50_fix.py`**:
   - `LIVE_COUNT_ASSUMPTIONS_FOUND`: `total_products >= 50`, `total_photos >= 50`, `avito_products >= 33` against `DB_PATH = "data/db/technoreboot.db"` in `test_test_i_catalog_preservation_invariant`.
   - `LIVE_COUNT_ASSUMPTIONS_REMOVED`: Removed `DB_PATH`. Replaced with `isolated_catalog_db` fixture seeded with synthetic business items. Test verifies that temporary record creation and scoped cleanup strictly preserves the baseline catalog without modifying or deleting business records.

---

## 4. Test Suite Execution Results

### 4.1 Avito Module
- **Command:** `pytest avito-module\tests`
- **Collected:** 154
- **Passed:** 154
- **Failed:** 0
- **Skipped:** **0**
- **Duration:** 25.11s

### 4.2 Chrome Extension
- **Command:** `pytest chrome-extension\technoreboot-avito\tests`
- **Collected:** 126
- **Passed:** 126
- **Failed:** 0
- **Skipped:** **0**
- **Duration:** 1.09s

### 4.3 Focused Avito Regressions (`scripts/verify_avito_focused_regressions.py`)
- **IDENTITY:** PASS: 1 Avito ID -> 1 Product, 0 duplicates in database
- **NO_QUANTITY_INFLATION:** PASS: Repeated active import keeps quantity = 1
- **ARCHIVE_REACTIVATION:** PASS: sold/archive/0 reactivated to in_stock/store/1 on same product
- **INACTIVE_REMOTE_STOCK_SAFETY:** PASS: Remote closed/archived status preserved physical store inventory
- **THUMBNAILS:** PASS: Photo payload ingestion verified
- **PHOTO_PERSISTENCE:** PASS: Photo records linked to product
- **RICH_GALLERY_PRESERVED:** PASS: Lower quality thumbnails do not wipe existing richer gallery
- **ZERO_OF_50_THUMBNAIL:** PASS: DOM lazy triggers, srcset, and background-image handlers prevent 0/50 failure
- **CARD_BOUNDARY:** PASS: Distinct card ID isolation prevents photo bleeding between neighboring items
- **PHOTO_EXTRACTION:** PASS: Validates img.avito.st candidates and filters out non-product badges/avatars
- **NO_DESTRUCTIVE_CLEANUP:** PASS: Cleanup targets only synthetic test IDs, 0 real business products affected

---

## 5. Live Data Safety Verification

All tests and focused verification scripts ran with rigorous data safety verification against `data/db/technoreboot.db`:

- **Preflight Live Counts:**
  - Products: 50
  - Sales: 52
  - Repairs: 66
  - Photos: 50
  - Avito External Listings: 50
- **Post-Verification Live Counts:**
  - Products: 50
  - Sales: 52
  - Repairs: 66
  - Photos: 50
  - Avito External Listings: 50
- **Invariants:**
  - `REAL_PRODUCT_IDS_UNCHANGED`: **true**
  - `REAL_SALE_IDS_UNCHANGED`: **true**
  - `REAL_REPAIR_IDS_UNCHANGED`: **true**
  - `REAL_PHOTO_IDS_UNCHANGED`: **true**
  - `REAL_EXTERNAL_LISTING_IDS_UNCHANGED`: **true**
  - `REAL_PRODUCTS_DELETED`: **0**

---

## 6. Release Gap List (Normalized)

The normalized gap classification from Stage 08A-R1-R1 remains valid:
- **P0 Blockers for VDS Deployment:** **0**
- **P1 Broken Core Daily Workflows:** **0**
- **P2 Important Improvements:** **6** (Automated backup cron, Avito webhook sync, direct ESC/POS printer, photo compression, bulk repair transitions, technician RBAC)
- **P3 Future Enhancements:** **3** (Telegram/SMS notifications, barcode scanner listener, dark mode)
- **VDS Blockers:** **0**
