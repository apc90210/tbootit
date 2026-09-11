# Stage 08A-R1-R4 — Self-Contained Chrome Extension Regression Fixtures Report

**Date:** 2026-09-11  
**Workspace:** `C:\tbootit`  
**Stage:** `Stage 08A-R1-R4 — Self-Contained Chrome Extension Regression Fixtures`  
**Target:** Eliminate all dependencies on untracked historical runtime ad files (`data/avito-module/ads/8355529554.json`) and eliminate `pytest.skip` in fresh clones.

---

## 1. Executive Summary

In Stage 08A-R1-R3, the `avito-module` test suite was made 100% self-contained by eliminating dependencies on historical database backup files. However, two tests in the `chrome-extension` suite still depended on untracked runtime ad captures (`data/avito-module/ads/8355529554.json`) and were skipping when run in a fresh Git clone.

Stage 08A-R1-R4 successfully eliminated this dependency:
1. Replaced the untracked runtime ad file with a clean, Git-tracked synthetic fixture at `chrome-extension/technoreboot-avito/tests/fixtures/synthetic_ad_8355529554.json`.
2. Fully preserved both core regressions:
   - **Strict HQ photo candidate filtering:** distinguishes genuine Avito CDN photos (`*.img.avito.st/image/1/`) from foreign items (trackers, maps, avatars, logos, delivery badges).
   - **Full gallery extraction:** validates complete 6-photo gallery ordering, deduplication, and base64 payloads without regression to single-photo behavior.
3. Removed `pytest.skip` logic across all Chrome extension tests.
4. Preserved dynamic on-demand ZIP building so that pre-existing `dist/*.zip` is never required.
5. Executed a clean-clone proof from `origin/main` in a separate temporary directory without `data/` and without pre-existing `dist/`:
   - `avito-module`: **154 passed, 0 failed, 0 skipped** (27.17s).
   - `chrome-extension`: **126 passed, 0 failed, 0 skipped** (1.44s).
6. Guaranteed zero mutation of live business data (50 products, 52 sales, 66 repairs, 50 photos, 50 external listings. 0 deleted).

---

## 2. Dependency Audit & Skip Analysis

### Skip 1: `test_sample_listing_photo_integrity`
- **File:** `chrome-extension/technoreboot-avito/tests/test_stage07b_r5_r2_strict_hq_photos.py`
- **Runtime Dependency:** `data/avito-module/ads/8355529554.json`
- **Intended Regression:** Strict validation of photo candidates; verification that foreign patterns (`dashboard`, `adriver`, `cursor`, `delivery`, `logo`, `avatar`) are rejected while genuine `img.avito.st/image/1/` photos are accepted.
- **Why Skip Was Not Acceptable:** In a fresh checkout without `data/`, skipping silenced this safety check, risking silent contamination of product catalogs with ad trackers or seller avatars.
- **New Fixture Strategy:** Converted to read `chrome-extension/technoreboot-avito/tests/fixtures/synthetic_ad_8355529554.json`, strictly asserting 6 genuine gallery photos and >= 5 foreign rejected items without skipping.

### Skip 2: `test_test_a_and_l_owner_listing_photo_count_and_integrity`
- **File:** `chrome-extension/technoreboot-avito/tests/test_stage07b_r5_r3_full_gallery.py`
- **Runtime Dependency:** `data/avito-module/ads/8355529554.json`
- **Intended Regression:** Multi-photo gallery integrity verification (ensuring all 6 photos are captured and base64 payloads preserved).
- **Why Skip Was Not Acceptable:** In clean clones, skipping silently removed verification that full multi-photo extraction works end-to-end on parsed listing data.
- **New Fixture Strategy:** Converted to read `chrome-extension/technoreboot-avito/tests/fixtures/synthetic_ad_8355529554.json`, strictly asserting 6 genuine photos with valid base64 payload (>1000 bytes) without skipping.

### Package Skip Hardening: `test_extension_manifest_and_zip_version`
- **File:** `chrome-extension/technoreboot-avito/tests/test_photo_detection_bug_fix.py`
- **Previous Issue:** Had a hardcoded path to an old version zip (`technoreboot-avito-extension-0.2.47.zip`) and skipped if missing.
- **Fix:** Dynamically determines target zip based on `manifest.json` version (`0.2.53`), builds via `build_zip()` if missing, and asserts existence without skipping.

---

## 3. Synthetic Fixture Architecture

- **Path:** `chrome-extension/technoreboot-avito/tests/fixtures/synthetic_ad_8355529554.json`
- **Tracked in Git:** Yes
- **Sensitive Data Included:** **None** (No real seller names, no real buyer names, no phone numbers, no physical addresses, no cookies, no auth tokens, no session IDs).
- **Structure:**
  - `id`: `"8355529554"`
  - `photos[0..5]`: 6 genuine Avito gallery photo objects with `https://30.img.avito.st/image/1/1.synthetic_gallery_photo_...` and valid dummy base64 JPEG payload (>1000 bytes).
  - `photos[6..11]`: 6 foreign asset objects representing dashboard, adriver tracker, maps cursor, delivery badge, static logo, and seller avatar.

---

## 4. Clean-Clone Proof Verification

A fresh clone was initialized from `origin/main` in a clean temporary directory:
- **Path:** `C:\Users\Apc\AppData\Local\Temp\fresh_clone_stage08a_r4`
- **HEAD:** `68cd820f7216900a52a3f740a48707e3366430ef`
- `data/` directory exists: **False**
- `data/avito-module/ads/8355529554.json` exists: **False**
- `dist/` pre-existing requirement: **False** (directory was explicitly deleted before testing)

### Test Results in Clean Clone:
```text
pytest avito-module\tests
=> 154 passed, 0 failed, 0 skipped (27.17s)

pytest chrome-extension\technoreboot-avito\tests
=> 126 passed, 0 failed, 0 skipped (1.44s)
```

---

## 5. Focused Extension Regressions

Executed via `scripts/verify_extension_focused_regressions.py`:

| Check | Focus Area | Status | Detail |
|---|---|:---:|---|
| **STRICT_HQ** | Strict HQ photo candidate selection | **PASS** | Validates genuine Avito CDN URLs, rejects 6 foreign tracker/avatar patterns, rejects blind string replacement |
| **FULL_GALLERY** | Full gallery parsing | **PASS** | Validates 6 gallery photos, slot indexing, order preservation, and traversal logic |
| **ZERO_OF_50** | Real cabinet thumbnail extraction | **PASS** | Validates asynchronous extraction, lazy-scroll trigger, diagnostics, and CDN permissions |
| **CARD_BOUNDARY** | Card container isolation | **PASS** | Validates `findCardContainer` strict boundary (`distinctIds.size > 1` break) |
| **PHOTO_EXTRACTION** | Multi-source photo extraction | **PASS** | Validates extraction across `img[src]`, `srcset`, `picture > source`, and CSS `background-image` |
| **PACKAGE_CONTENTS** | Extension packaging | **PASS** | Validates zip structure, root manifest, icons, service worker, content script, and popup |
| **MANIFEST_VERSION** | Version synchronization | **PASS** | Confirms manifest version `0.2.53` matches across UI, scripts, and built ZIP |
| **NO_PUBLISH_OR_PAYMENT_ACTION** | Safety guard against paid actions | **PASS** | Confirms zero selectors or API triggers for publishing, VAS, promote, wallet, or payment |

---

## 6. Live Business Data Safety Invariant

Verified before and after all test executions:
- `PRODUCT_IDS_UNCHANGED`: **True** (hash: `d33590f5c8c43e6f873c01869865493c280d92b3518f34f11b6b708d13c47b06`)
- `SALE_IDS_UNCHANGED`: **True** (hash: `9180064a278dc115017621b5b46e2d8424468a675c6278c8d2261106aa6b9179`)
- `REPAIR_IDS_UNCHANGED`: **True** (hash: `2ba02c6bd9d14b20a6629c8fc850badeeab3e5bdbf7b84711c850027e45965ab`)
- `PHOTO_IDS_UNCHANGED`: **True** (hash: `7458408486ea85d8c77bae1cafcf8a06c3f8b448153da8dcabe6d993b7351ed7`)
- `EXTERNAL_LISTING_IDS_UNCHANGED`: **True** (hash: `d33590f5c8c43e6f873c01869865493c280d92b3518f34f11b6b708d13c47b06`)
- `REAL_PRODUCTS_DELETED`: **0**

---

## 7. Release Gap Counts (Normalized)

Unchanged at baseline:
- **P0 Blockers:** **0**
- **P1 Broken Core Daily Workflows:** **0**
- **P2 Important Improvements:** **6**
- **P3 Future Enhancements:** **3**
- **VDS Blockers:** **0**

---

## 8. Final Status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE08A_R1_R4_EXTENSION_TESTS_FULLY_SELF_CONTAINED

PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```
