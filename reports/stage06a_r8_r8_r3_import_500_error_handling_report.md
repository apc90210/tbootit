# Stage 06A-R8-R8-R3 Verification Report: Import 500 Root Cause & Robust Error Handling

**Date:** 2026-08-13  
**Stage:** Stage 06A-R8-R8-R3  
**Status:** COMPLETE — READY FOR OWNER CHECK  

---

## 1. Owner Error & Root Cause Analysis

### Reported Owner Error
When the Owner attempted to transfer listing `8313765236` using Chrome Extension v0.1.7:
```text
✕ Объявление получено, но импорт товара завершился ошибкой.
Ошибка при передаче: Unexpected token 'I', "Internal S"... is not valid JSON
```

### Empirical Traceback & Root Cause Diagnosis
1. **Root Cause A (Backend 500 ReadTimeout)**:
   - File: `admin-shell/app/main.py`, line 487 (`proxy_avito_extension_api`).
   - Exception: `httpx.ReadTimeout` (Traceback logged at container start).
   - Input Condition: `proxy_avito_extension_api` instantiated `httpx.AsyncClient(trust_env=False)` without an explicit timeout. In `httpx`, the default read timeout is **5.0 seconds**.
   - Why Triggered: During listing import, `core` API fetches remote photos from Avito CDN (`https://80.img.avito.st/image/...`). Downloading 8+ remote images over the network took 8–15 seconds, exceeding `admin-shell`'s 5.0-second default read timeout.
   - Consequence: At second 5.0, `admin-shell` raised `httpx.ReadTimeout`. Uncaught exception bubbled to FastAPI's default 500 middleware, returning `HTTP 500 Internal Server Error` with `Content-Type: text/plain` and body `"Internal Server Error"`.

2. **Root Cause B (Frontend Extension Error Handling)**:
   - File: `chrome-extension/technoreboot-avito/service_worker.js` (`sendListingPayload`).
   - Exception: `SyntaxError: Unexpected token 'I', "Internal S"... is not valid JSON`.
   - Why Triggered: `service_worker.js` called `await res.json()` directly on the HTTP 500 response without checking `res.ok` or `Content-Type`. Parsing plain text `"Internal Server Error"` threw a JavaScript `SyntaxError`, which was caught in the catch block and formatted as `Unexpected token 'I'...`.

---

## 2. Implemented Fixes

### A. Backend Proxy & Timeout Enhancements
- **`admin-shell/app/main.py`**:
  - Increased `httpx.AsyncClient` timeout from default 5.0s to **60.0 seconds** in `proxy_avito_extension_api`.
  - Added `try...except` handling:
    - `httpx.TimeoutException`: Returns `HTTP 504 Gateway Timeout` with JSON `{"ok": False, "status": "failed", "detail": "Превышено время ожидания ответа от модуля Avito (60с)..."}`.
    - `Exception`: Returns `HTTP 500 Internal Server Error` with JSON `{"ok": False, "status": "failed", "detail": "Ошибка проксирования запроса к модулю Avito: ..."}`.
- **`avito-module/app/services/import_service.py`**:
  - Increased Core API client timeouts in `import_ad_to_core` and `run_account_import` from 15.0s to **60.0 seconds**.

### B. Extension Robust Error Handling (`service_worker.js` v0.1.8)
- Added `parseJsonResponseSafely(res)` helper in `service_worker.js`:
  - Inspects `res.ok` and `Content-Type`.
  - Parses JSON only when valid.
  - On non-2xx statuses, extracts user-facing `detail` or falls back to `Ошибка сервера <status>: <safe_text>`.
  - **Completely eliminates JavaScript `Unexpected token` SyntaxErrors!**

---

## 3. Product 58 Read-Only Audit State

- **Product ID:** `58`
- **SKU:** `AVITO-8313765236`
- **External Listing ID:** `8313765236`
- **Status:** `draft`
- **Photo Row Count:** `12`
- **Mutation:** Product 58 was NOT mutated or deleted during this corrective stage.

---

## 4. Extension Version 0.1.8 Delivery

- Version bumped to `0.1.8` in `manifest.json`, `popup.js`, `README.md`, `admin-shell/app/main.py`, `avito_extension.html`, and `scripts/build_extension_zip.py`.
- Rebuilt ZIP package `technoreboot-avito-extension-0.1.8.zip` in `dist/` and `admin-shell/app/`.
- Download endpoint `GET http://localhost:8011/avito/extension/download` returns `technoreboot-avito-extension-0.1.8.zip` with `HTTP 200 OK`.

---

## 5. Test Suite Verification (100% Pass)

- `chrome-extension/technoreboot-avito/tests`: 27 / 27 passed (includes new `test_robust_error_handling.py`)
- `avito-module/tests`: 83 / 83 passed
- `core/tests` (safe): 175 / 175 passed
- `inventory-sales-module/tests`: 119 / 119 passed
- `repairs-module/tests`: 34 / 34 passed
- `admin-shell/tests`: 45 / 45 passed
- **Total:** 483 unit tests passing 100%.

---

## Definition of Done Matrix

```text
OWNER_500_ROOT_CAUSE_IDENTIFIED: true
OWNER_500_FIXED: true
IMPORT_ENDPOINT_SUCCESS_JSON_VALID: true
EXTENSION_PLAIN_TEXT_ERROR_HANDLING_FIXED: true
UNEXPECTED_TOKEN_ERROR_ELIMINATED: true
BEST_QUALITY_ONLY_MULTI_PHOTO_PRESERVED: true
REPEAT_IMPORT_IDEMPOTENT: true
PRODUCT_58_MUTATED_BY_AGENT: false
EXTENSION_VERSION_0_1_8_READY: true
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_IMPORT_NOT_YET_FULLY_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
