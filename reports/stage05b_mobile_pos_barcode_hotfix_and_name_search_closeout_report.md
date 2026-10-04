# Stage 05B Mobile POS Barcode Hotfix and Name Search Closeout Report

- **Date:** 2026-10-04
- **Prompt:** `TR_Stage05B_OWNER_PASS_Closeout_R1.md`
- **Milestone:** Mobile POS Hardware Scanner & Search Parity (Stage 05B)
- **Status:** **CLOSED / ACCEPTED (PASS)**

---

## 1. Executive Summary

Stage 05B addressed a critical production defect where the Android Mobile POS scanner returned 404 for physical store price tags due to unpopulated barcode columns on production VDS (`144.31.15.88`), as well as the absence of product text search in the Mobile POS interface.

Following the deployment of release commit `973f318` and production APK v1.5.1 (code 21), OWNER conducted physical device testing on Samsung Galaxy S22 Ultra:
- Application updated to production 1.5.1 (versionCode 21) via canonical update mechanism.
- Barcode scanning of real printed store price tags (`200000000230`–`200000000458`) reliably finds products.
- Scanned products correctly add to the active POS cart.
- Instant search by product name/SKU functions as expected.
- Products selected from search results add to cart with correct price and stock invariants.

**OWNER VERDICT:** **PASS**.  
**Stage 05B Status:** **CLOSED / ACCEPTED**.

---

## 2. Exact Production Facts & Release Provenance

| Parameter | Production Value | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **Deployed Git Commit** | `973f318b5c...` (`release/stage05b-mobile-pos`) | `git rev-parse HEAD` on VDS `/srv/technoreboot/app` | MATCH (Direct child of `616951a`) |
| **Release Branch** | `release/stage05b-mobile-pos` | Clean branch off baseline `616951a` | ZERO unrelated/WEB commits |
| **APK Version** | `versionCode=21`, `versionName=1.5.1` | APK manifest & Android `build.gradle.kts` | MATCH |
| **APK File Size** | `32,967,534` bytes | `stat -c %s app-release-v21.apk` on VDS | MATCH |
| **APK SHA-256** | `6ab2a56c7253620b0ca3be97d9de189185ca0c775e0d6b047e6228a2437cbc88` | `sha256sum app-release-v21.apk` on VDS | EXACT MATCH |
| **Signer Certificate SHA-256** | `741ffd5582e3ab46aee12a746a3aae7454fcaa79553b9702102bf3a4ec47bcd1` | `apksigner verify --verbose --print-certs` | EXACT MATCH (Production Key) |
| **Published Manifest** | `/srv/technoreboot/data/releases/mobile/manifest.json` | Live manifest query & backup `manifest.json.v20.bak` | ACTIVE |
| **Physical Barcode Scan** | Samsung Galaxy S22 Ultra | OWNER physical verification | **PASS** |
| **Physical Name/SKU Search** | Samsung Galaxy S22 Ultra | OWNER physical verification | **PASS** |
| **Production Data Invariant** | Sales: 70 (UNTOUCHED), Repairs: 2 (UNTOUCHED), Products: 423 | SQLite `COUNT(*)` pre == post | PRESERVED |

---

## 3. Architecture & Defect Resolution

### A. Root Cause Analysis
1. In the production database on VDS, 422 out of 423 products had `barcode = NULL` (only product #327 had a barcode, but its status was `sold`).
2. Physical price tags in the store had 12-digit barcodes (`200000000230` to `200000000458`) assigned during pre-sync historical backup.
3. Core `/api/products/by-barcode/{barcode}` only searched the `Product.barcode` column. With NULL barcodes, every scan failed with 404.
4. Desktop cashiers search by title/SKU via `/inventory/products?q=...` or `/` which queries Core `GET /api/products/?q=...` across all fields, succeeding while mobile barcode scanning failed.
5. Mobile POS previously lacked product search by text/name.

### B. Applied Changes
1. **Core Backend (`core/app/routers/products.py`):**
   - Hardened `get_product_by_barcode` with whitespace trimming and case-insensitive matching (`func.lower(func.trim(models.Product.barcode)) == barcode_clean.lower()`), strictly preserving 404 contract on missing items without 500 errors.
2. **Admin-Shell Facade (`admin-shell/app/main.py`):**
   - Added `GET /api/mobile/products/search?q={query}&limit={limit}` protected by TRMOBILE1 PoP HMAC authentication.
   - Proxies to Core `GET /api/products/?q={q}&status=in_stock&limit={limit}` and formats items to standard POS product schema.
3. **Android Application (`android-app`):**
   - `MobileApiClient.kt`: Added `searchPosProducts` with canonical query string sorting and TRMOBILE1 PoP signing.
   - `PosTerminalScreen.kt`: Upgraded manual input into unified name/SKU/barcode search with instant result card display (title, barcode/SKU, location, price, stock) and tap-to-add via `cartRepository.addProduct`.
4. **Production Database Barcode Migration (`scripts/vds_apply_stage05b_barcodes.py`):**
   - Created pre-deploy safety backup: `/srv/technoreboot/data/backups/pre_stage05b_20261003_181548/technoreboot.db`.
   - Updated products 1..229 with barcodes `200000000230`..`200000000458` matching printed physical price tags.
   - Assigned unique sequential barcodes `200000000459`..`200000000652` for products 230..423.
   - Verified `PRAGMA quick_check` (ok), `PRAGMA foreign_key_check` ([]), distinct barcodes = 423, zero NULLs.
   - Preserved all business transactions: sales=70, repairs=2.

---

## 4. Migration Script Disposition

- **Script:** `scripts/vds_apply_stage05b_barcodes.py`
- **Disposition:** **COMMITTED**
- **Rationale:** This script is the exact, reproducible migration artifact executed on the live VDS to create the safety backup, perform the atomic transaction populating 423 canonical barcodes matching physical store tags, and verify relational integrity and business count preservation. Committing it ensures historical auditability and reproducibility for future disaster recovery or staging environments.

---

## 5. Closeout Decision & Readiness

- **Stage 05B Status:** **CLOSED / ACCEPTED**
- **Production Touched During Closeout:** **NO** (Production was deployed during the rollout phase; no changes made during closeout).
- **Ready to Resume Stage 05A OWNER Physical Test:** **YES**. With the POS scanning hotfix verified on the physical device, the environment and device are ready to resume physical testing of Stage 05A (Quick Product Intake with AI foundation).
