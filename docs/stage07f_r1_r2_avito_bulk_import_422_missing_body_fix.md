# Stage 07F-R1-R2 — Avito Bulk Import HTTP 422 Missing Body Fix & Accounting Invariant

## 1. Problem Statement & Root Cause

During browser testing of the Chrome extension bulk import on personal Avito cabinet profiles (`/profile/items`, `sellerId=...`), the operation failed with the following user-visible error in the extension popup:
```text
HTTP 422: [{"type":"missing","loc":["body"],"msg":"Field required","input":null,"url":"https://errors.pydantic.dev/2.5/v/missing"}]
```
Simultaneously:
1. **Broken Accounting & False Green Success**: Despite 0 listings being created or updated in Technoreboot, the progress log in the popup proceeded through item counts and eventually displayed:
   ```text
   ✓ Импорт успешно завершен!
   Страниц обработано: 1, объявлений: 50
   ```
2. **Missing Body in Service Worker**:
   - `popup.js` dispatched the background message:
     ```javascript
     chrome.runtime.sendMessage({ action: "bulk_import_batch", items: batchItems }, ...);
     ```
   - `service_worker.js` received this message and extracted:
     ```javascript
     const payload = request.payload; // undefined!
     ```
   - In `sendBulkImportPayload`, `body: JSON.stringify(payload)` evaluated to `JSON.stringify(undefined)` which is `undefined`.
   - `fetch(endpoint, { method: "POST", body: undefined })` transmitted an HTTP POST request with an empty body to FastAPI `/admin-api/avito-extension/bulk-import`.
   - Pydantic v2 rejected the empty body with:
     `[{"type":"missing","loc":["body"],"msg":"Field required",...}]`.
3. **Pydantic URL Leakage**:
   - The raw Pydantic JSON error was stringified and presented directly to the user, leaking internal `https://errors.pydantic.dev/2.5/v/missing` URLs.
4. **Single-Page vs Multi-Page Drift**:
   - `bulkImportCurrentBtn` and `bulkImportAllBtn` implemented separate, diverging logic for sending batches and handling server responses.
5. **Session Loss on In-Tab Navigation**:
   - In multi-page traversal, SPA navigation or full-page navigation could terminate popup context, causing loss of pagination offsets, seen Avito IDs, and completed items.

---

## 2. Architecture & Invariants

### 2.1 Accounting Invariant
Any bulk import execution (single page or multi-page) must satisfy:
$$\text{totalCreated} + \text{totalUpdated} + \text{totalSkipped} + \text{errors.length} \equiv \text{submitted\_items}$$
- If $\text{errors.length} > 0$, the final UI banner MUST NOT be green success (`msg-success`). It must show warning (`msg-warning`) or error (`msg-error`).
- If $\text{totalCreated} + \text{totalUpdated} + \text{totalSkipped} === 0$, green success is strictly forbidden.

### 2.2 Canonical Batch Sender (`sendBulkBatch`)
Both `bulkImportCurrentBtn` and `bulkImportAllBtn` invoke a single canonical helper:
- Normalizes items array.
- Ensures valid non-empty payload structure.
- Calls `chrome.runtime.sendMessage({ action: "bulk_import_batch", payload: {...}, items: [...] })`.
- Handles success and error responses uniformly, incrementing `totalCreated`, `totalUpdated`, `totalSkipped`, or appending to `allErrors`.

### 2.3 Double Defensive Payload Normalization
- **Client Service Worker (`service_worker.js`)**:
  - Accepts both `request.payload` and fallback `request.items`.
  - Normalizes bare array or wrapped dictionary into canonical structure:
    ```json
    {
      "schema_version": 1,
      "extension_version": "0.2.50",
      "captured_at": "...",
      "page_type": "bulk_import",
      "items": [...]
    }
    ```
  - Validates `bodyJson` before `fetch()`. Throws explicit error if payload is empty.
- **Backend Bridge Router (`extension_bridge.py`)**:
  - `receive_bulk_import` accepts `Union[BulkImportPayload, List[Dict[str, Any]]]`.
  - If a bare list is received, it is automatically converted into `BulkImportPayload` with default metadata.

### 2.4 Error Sanitization & Russian UI Translation
- `parseJsonResponseSafely` in `service_worker.js`:
  - Strips any URLs matching `https?://errors\.pydantic\.dev[^\s"']*`.
  - Detects `missing -> loc: ["body"]` and translates to:
    `"Ошибка отправки данных в Техноребут: сервер не получил пакет объявлений."`
- `sanitizeErrorMessage` in `popup.js`:
  - Translates network errors and server errors into clean, user-friendly Russian messages without raw exception traces.

### 2.5 Navigation Resilience & Session Storage
- Multi-page pagination state is stored in `chrome.storage.session` under key `bulk_import_session`.
- Includes: `currentPage`, `maxPages`, `seenAvitoIds`, `visitedUrls`, `totalCreated`, `totalUpdated`, `totalSkipped`, `allErrors`.
- On page load / popup reopen, session state is recovered if a job is in progress.
- Content script SPA extraction incorporates 3 retry attempts with exponential backoff (up to 10s wait) to accommodate lazy React hydration after pagination clicks.

---

## 3. Versioning & Artifacts
All components bumped to version **`0.2.50`**:
- `chrome-extension/technoreboot-avito/manifest.json`: `"version": "0.2.50"`
- `chrome-extension/technoreboot-avito/popup.html`: `v0.2.50`
- `chrome-extension/technoreboot-avito/popup.js`: `manifestVer = "0.2.50"`
- `chrome-extension/technoreboot-avito/service_worker.js`: `v0.2.50`
- `chrome-extension/technoreboot-avito/content.js`: `v0.2.50`
- `avito-module/app/routers/extension_bridge.py`: `DEFAULT_EXTENSION_VERSION = "0.2.50"`
- `admin-shell/app/main.py`: `LATEST_AVITO_EXTENSION_VERSION = "0.2.50"`
- `admin-shell/app/templates/avito_extension.html`: `0.2.50`
- Built ZIP: `dist/technoreboot-avito-extension-0.2.50.zip` and `admin-shell/app/technoreboot-avito-extension-0.2.50.zip`.

---

## 4. Verification Results
1. **Automated Unit & Integration Tests**:
   - `avito-module`: 118 passed (including 10 new tests in `test_stage07f_r1_r2_bulk_422_fix.py`).
   - `admin-shell`: 83 passed, 1 skipped.
   - `core`: 238 passed.
   - `inventory-sales-module`: 142 passed.
   - Total test suite: 581 passed, 1 skipped, 0 failed.
2. **Live Gateway mTLS End-to-End Scenarios**:
   - Scenario 1: Unauthenticated request rejected by Gateway mTLS.
   - Scenario 2: Gateway serves `/avito/extension` and `/avito/extension/download` with v0.2.50.
   - Scenario 3: Extension pairing flow through Gateway returns valid token.
   - Scenario 4: Missing body correctly handled with 422 on raw server, sanitized in extension.
   - Scenario 5: Bulk import 50 items (Page 1) created=50, updated=0, errors=0.
   - Scenario 6: Idempotent re-import Page 1 created=0, updated=50, errors=0.
   - Scenario 7: Multi-page simulation (Page 2: 50 items, Page 3: 15 items), total 115 unique items created.
   - Scenario 8: On-demand enrichment of imported item through Gateway mTLS verified in inventory.
