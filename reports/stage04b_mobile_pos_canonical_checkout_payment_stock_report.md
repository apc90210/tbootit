# Stage 04B: Mobile POS Canonical Checkout, Payment & Stock Report

## 1. Executive Summary

- **Stage:** Stage04B (Mobile POS Canonical Checkout, Payment & Stock)
- **Prompt Reference:** `TR_Android_Stage04B_Mobile_POS_Canonical_Checkout_Payment_Stock_R1.md`
- **Scope:** LOCAL / DEV environment only (Production VDS `144.31.15.88` untouched)
- **Prerequisite:** Stage04A ACCEPTED (`304292853f8f91ded46c6927da31310a7b1a93ec`)
- **Status:** **PASS / READY FOR SUPERVISOR ACCEPTANCE**
- **Physical Test Device:** Samsung Galaxy S22 Ultra (`RFCT70R6XVP`)
- **Physical Checkout Result:** **PASS (Owner Verified)**

---

## 2. Architecture & Design Implementation

Stage04B connects the accepted Stage04A mobile cart to the canonical Core desktop sales engine without duplicating business logic or allowing unprivileged bypasses.

### 2.1 Backend Core Architecture
- **Unified Sale Service:** Extracted canonical sale execution logic into [`core/app/services/sale_service.py`](file:///c:/tbootit/core/app/services/sale_service.py) with functions:
  - `compute_checkout_hash(...)`: Deterministic SHA-256 payload hashing for idempotency collision detection.
  - `execute_canonical_sale(...)`: Atomic transaction boundary executing product validation, sellable status checks, stock sufficiency validation, atomic stock decrement, stock movement generation, and audit logging.
  - `build_sale_checkout_response(...)`: Standardized canonical receipt/sale response matching desktop receipts.
- **Core Endpoint:** `POST /api/sales/checkout` in [`core/app/routers/sales.py`](file:///c:/tbootit/core/app/routers/sales.py).
- **Durable Core Idempotency:** Implemented via table `checkout_idempotency` (`client_checkout_id`, `sale_id`, `request_hash`, `cashier_name`, `created_at`). Survives process and container restarts. Duplicate submissions with identical hash return the existing sale without re-decrementing stock; conflicting payloads with the same key return HTTP 409 Conflict.

### 2.2 Admin-Shell Mobile Facade
- **Endpoint:** `POST /api/mobile/sales/checkout` in [`admin-shell/app/main.py`](file:///c:/tbootit/admin-shell/app/main.py).
- **Authentication:** Enforces `TRMOBILE1` Proof-of-Possession (PoP) with request body SHA-256 bound directly into the canonical signature payload.
- **Role/Revocation:** Validates device active status and parent certificate active status; binds authenticated cashier identity to the sale.
- **Pure Facade:** Admin-shell does NOT mutate SQLite directly; it delegates via HTTP to Core API.

### 2.3 Android Mobile POS UX
- **Cart & Checkout State:** [`android-app/app/src/main/java/com/technoreboot/mobile/ui/pos/PosTerminalScreen.kt`](file:///c:/tbootit/android-app/app/src/main/java/com/technoreboot/mobile/ui/pos/PosTerminalScreen.kt)
  - Review cart items, quantities, and prices.
  - Confirmation dialog with canonical payment method selection (Cash, Card, Transfer, SBP, etc.).
  - Prominent top error banner to ensure errors are immediately visible.
  - Anti-duplicate submission protection during checkout in-flight.
  - Success dialog displaying canonical receipt number and total, with direct `Открыть чек` button opening [`ReceiptDetailScreen`](file:///c:/tbootit/android-app/app/src/main/java/com/technoreboot/mobile/ui/receipt/ReceiptDetailScreen.kt).
  - Cart clearing only upon confirmed server success.

---

## 3. Automated Test Verification

| Suite | Component | Tests Run | Result | Notes |
| :--- | :--- | :---: | :---: | :--- |
| `test_stage04b_canonical_checkout.py` | Core API | 24 | **PASS** | Atomic stock decrement, rollback, idempotency retry, conflict 409, concurrency |
| `test_stage04b_mobile_pos_checkout.py` | Admin-Shell Facade | 7 | **PASS** | TRMOBILE1 PoP, body tampering denial, revoked device/parent denial, cashier binding |
| Gradle `testDebugUnitTest` | Android POS | 25 tasks / 100 tests | **PASS** | PosCartRepository, PosCheckout, price override, network error retry |
| Gradle `lintDebug` | Android App | - | **PASS** | 0 lint errors |

---

## 4. Issues Encountered & Resolved

1. **Service Downtime & ADB Forwarding:**
   - *Issue:* Docker containers and ADB daemon stopped after previous session terminated.
   - *Fix:* Re-launched all Docker containers (`technoreboot-core`, `technoreboot-admin-shell`, `technoreboot-gateway`, etc.), set up ADB reverse port forward (`tcp:8011`, `tcp:8000`), and launched persistent keepalive daemon [`scripts/adb_keepalive.py`](file:///c:/tbootit/scripts/adb_keepalive.py).
2. **Missing `id` Column in `checkout_idempotency` Table:**
   - *Issue:* Tapping "Подтвердить продажу" on physical phone caused HTTP 500 error (`sqlite3.OperationalError: no such column: checkout_idempotency.id`).
   - *Root Cause:* SQLite dev database schema had `checkout_idempotency` created without the primary key `id` defined in SQLAlchemy model.
   - *Fix:* Recreated table `checkout_idempotency` with exact SQLAlchemy schema (`id INTEGER PRIMARY KEY AUTOINCREMENT`), verified foreign keys and quick check, and restarted containers.
3. **Checkout Error UI Visibility:**
   - *Issue:* Error message was located below 7 payment method choices in scrollable column.
   - *Fix:* Added error banner at the top of the checkout dialog in `PosTerminalScreen.kt`, rebuilt and reinstalled debug APK on the phone.

---

## 5. Physical Device Verification (Owner Verification)

- **Device:** Samsung Galaxy S22 Ultra (`RFCT70R6XVP`)
- **App:** «Техноребут Тест» (`com.technoreboot.mobile.debug`)
- **Actions performed:**
  1. Opened POS Terminal via `[Продажа]`.
  2. Scanned product barcode.
  3. Tapped `Оформить продажу`, selected payment method `Наличные`.
  4. Tapped `Подтвердить продажу`.
  5. Received `Продажа оформлена` confirmation.
  6. Tapped `Открыть чек` and verified receipt details.
- **Owner Result:** **`PASS`**

### Post-Checkout Local Database Metrics
- **Sale ID:** `12`
- **Total Amount:** `4 900.00 ₽`
- **Payment Method:** `cash`
- **Status:** `completed`
- **Client Checkout ID:** `301dfc80-67a0-43f1-ba7a-e8a9d8372687`
- **Created At:** `2026-09-30 09:20:32`
- **Sold Item:** Product ID `229` (*МФУ HP LaserJet 3055*), Qty `1`, Unit Price `4 900.00 ₽`
- **Stock Movement:** Movement ID `10` created atomically, decremented stock by exactly 1 unit.
- **Idempotency Record:** Row 1 stored in `checkout_idempotency` with payload SHA-256 hash.
- **Total Sales Count:** Increased from 11 to 12.
- **Total Movements Count:** Increased from 9 to 10.

---

## 6. Next Stage Transition

- **Completed Stage:** Stage04B (Mobile POS Canonical Checkout, Payment & Stock)
- **Next Stage:** **Stage04C (Standard Receipt Printing)**
