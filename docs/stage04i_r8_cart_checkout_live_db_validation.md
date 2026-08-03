# Stage 04I-R8 Final Cart Checkout and Live DB Consistency Validation

## Overview
This document records the release audit, runtime live database consistency validation, end-to-end acceptance flow verification, and test isolation proof for Stage 04I-R8 of project "Technoreboot".

---

## 1. DB Count Distinction & Test Isolation Architecture

### Safe Unit Tests vs. Live Business Operations
- **Isolated Unit Tests (`scripts/test_core_safe.ps1`):**
  - Execute against an isolated, temporary SQLite database located in `/tmp/pytest_core_isolated_.../isolated_test.db`.
  - Do **NOT** read, modify, or delete the live database at `C:\tbootit\data\db\technoreboot.db` (container path `/data/db/technoreboot.db`).
  - **Empirical Proof:** SHA256 of live database (`54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`) and product/sale counts remained **100% identical** before and after running unit test suites.

- **Live Business Operations (Runtime Smoke / User UI Actions):**
  - Execute HTTP calls against `http://localhost:8030/cart/checkout` which calls Core API (`http://localhost:8000/api/sales/`) bound to `/data/db/technoreboot.db`.
  - When real sales are created, canceled, or reissued, records are persisted in the live database.
  - **Empirical Proof:** The live database correctly updated its SHA256 and incremented sale count as expected during live runtime validation (+1 for SBP sale, +1 for no-warranty sale, +1 for reissued sale).

---

## 2. End-to-End Live Runtime Acceptance Results

### A. Live DB State BEFORE Runtime
- `LIVE_DB_SHA256_BEFORE`: `d25dc807113c169b1b76612727cd45154dc9a189fb28caf4724b87da56f8aa81`
- `PRODUCT_COUNT_BEFORE`: 53
- `BARCODE_COUNT_BEFORE`: 53
- `SALE_COUNT_BEFORE`: 36
- `MAX_SALE_ID_BEFORE`: 36
- `REPORT_TOTAL_BEFORE`: 34750.0

### B. Add Product from `/products` (`POST /cart/add`)
- Added Product #46 (`Report Test Product 43bdfedf`, price 1000.0) without body `price`.
- Status: HTTP 303 Redirect to `/cart`. Product details (title & price) fetched automatically from Core API (`GET /api/products/46`). No 422 error.

### C. Checkout SBP + 30 Days Warranty (`POST /cart/checkout`)
- Parameters: `payment_method = sbp`, `warranty_enabled = true`, `warranty_days = 30`.
- Sale Created: **Sale #37**.
- Saved Total: 1000.0 (Server calculated).
- Live DB State After SBP:
  - `LIVE_DB_SHA256`: `f9eb35305c06689188ce8404ef57ba8d9932b29161ce60e39dee7fbcc753d77c`
  - `SALE_COUNT`: 37 (BEFORE + 1)
  - `MAX_SALE_ID`: 37
  - `REPORT_TOTAL`: 35750.0 (+1000.0)

### D. Checkout No Warranty (`POST /cart/checkout`)
- Added Product #47, parameters: `payment_method = cash`, `warranty_enabled = false`, `warranty_days = null`.
- Sale Created: **Sale #38**.
- Receipt Verification: `GET /sales/38/receipt` HTML confirmed containing "Без гарантии".

### E. Sale Cancellation (`POST /sales/37/cancel`)
- Canceled SBP Sale #37 (`reason = "Клиент передумал"`).
- Status updated to `canceled`, product stock returned.
- Double Cancel Attempt: Core API returned **HTTP 409 Conflict** as expected.

### F. Sale Reissue (`POST /sales/37/reissue`)
- Reissued Sale #37.
- Original Sale #37 status updated to `superseded` (`superseded_by_sale_id = 39`).
- New Sale **#39** created (`source_sale_id = 37`, status `completed`).
- Report Integrity: Sales report includes Sale #39 once (1000.0) and excludes superseded Sale #37.

---

## 3. Live DB State AFTER Runtime Operations
- `LIVE_DB_SHA256_AFTER_RUNTIME`: `54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`
- `PRODUCT_COUNT_AFTER_RUNTIME`: 53
- `BARCODE_COUNT_AFTER_RUNTIME`: 53
- `SALE_COUNT_AFTER_RUNTIME`: 39
- `MAX_SALE_ID_AFTER_RUNTIME`: 39
- `REPORT_TOTAL_AFTER_RUNTIME`: 35750.0

---

## 4. Test Isolation & Safe Test Preservation Proof

- `LIVE_DB_SHA256_BEFORE_TESTS`: `54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`
- Executed `scripts/test_core_safe.ps1` (**118 passed**).
- Executed `inventory-sales-module pytest` (**91 passed**).
- Executed `avito-module pytest` (**12 passed**).
- `LIVE_DB_SHA256_AFTER_TESTS`: `54c5e0572f584866e2299ebff18531e6ea67411d07124594e2cd3d0cc948310c`
- **Result:** **100% Identical SHA256 and record counts before & after unit tests.**

---

## 5. UI Navigation Links Verification
All 7 key owner UI pages returned **HTTP 200 OK**:
- `GET /products` -> 200 OK
- `GET /cart` -> 200 OK
- `GET /sales/39` -> 200 OK
- `GET /sales/39/receipt` -> 200 OK
- `GET /sales/39/cancel` -> 200 OK
- `GET /sales/39/reissue` -> 200 OK
- `GET /reports/sales` -> 200 OK
