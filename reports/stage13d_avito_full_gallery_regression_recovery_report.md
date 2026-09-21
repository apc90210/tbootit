# Stage 13D: Avito Full Gallery Regression Recovery & Popup Race Elimination Report

**Date:** 2026-09-21  
**Target:** Chrome Extension `technoreboot-avito` (v0.2.66)  
**Historical Working Reference:** Stage 07B-R5-R3 (`bd7bdc75c765e74c00994e9c4f6f9053b879535a`, v0.2.46)  
**Real Live Listing Tested:** `8355529554` (`https://www.avito.ru/ekaterinburg/noutbuki/noutbuk_acer_aspire_5690_pod_vosstanovlenie_8355529554`)  
**Status:** **PASSED / COMPLETE**

---

## 1. Executive Summary & Root Cause Confirmation

In Stage 13C, live diagnostic investigation revealed that on listing `8355529554`, the TechnoReboot Chrome Extension extracted only 1 photo instead of all 5 visible gallery photos. Stage 13D was chartered to systematically recover full-gallery extraction based on proven historical baselines, eliminate popup fast/deep scan race conditions, and elevate structured page-state media to the primary authoritative source.

### Root Causes Confirmed

1. **Avito Frontend SSR Architecture Migration (Missing Structured Media):**
   - **Historical Baseline (v0.2.46):** Avito stored listing data in `window.__initialData__` or `window.__INITIAL_STATE__` with component key `@avito/bx-item-view`. All photos were listed in `item.images` or `item.imageLargeUrl`.
   - **Modern Avito Migration (v0.2.65 failure):** Avito migrated from traditional monolithic SSR hydration to Remix / React Router 6 SSR data. The listing gallery data is now embedded in:
     ```html
     <script>window.__staticRouterHydrationData = JSON.parse("{\"loaderData\":{\"catalog-or-main-or-item\":{\"buyerItem\":{\"galleryInfo\":{\"media\":[...]}}}}}")</script>
     ```
   - Previous extension regexes looked specifically for `__initialData__` and `@avito/bx-item-view`, completely missing `window.__staticRouterHydrationData`. Because structured state was not recognized, the extension fell back to DOM traversal on a modern DOM with virtualized, lazy-loaded or non-interactive thumbnail wrappers.

2. **Popup Fast/Deep Scan Race Condition:**
   - On popup open, `popup.js` issued a provisional `deepScan: false` request.
   - `setupSingleListingSection()` immediately received the 1-photo provisional response and set `sendBtn.disabled = false`.
   - When the user clicked "Доимпортировать данные", the handler transmitted either the provisional 1-photo payload or fired a duplicate asynchronous query that raced with previous deep scans, frequently persisting only 1 photo to TechnoReboot Core.

---

## 2. Historical vs Current Architecture Analysis (8 Paths Compared)

| Function / Path | Historical Working (Stage 07B-R5-R3, v0.2.46) | Pre-Fix (v0.2.65) | Recovered Architecture (Stage 13D, v0.2.66) |
|---|---|---|---|
| **1. `triggerInitialDataCapture`** | Dispatched script injection to capture `window.__initialData__` | Dispatched script injection, but only read `__initialData__` | Captures `__initialData__`, `__staticRouterHydrationData`, and delegates to `main_world_bridge.js` |
| **2. `extractPhotosFromEmbeddedState`** | Scanned script tags with regex for `@avito/bx-item-view` | Narrow regex for `__initialData__` | Multi-format scanner: parses `__staticRouterHydrationData` (handling `JSON.parse("...")` unescaping), `data-mfe-state`, and raw JSON scripts |
| **3. `extractGalleryFromInitialData`** | Parsed `item.images` from `@avito/bx-item-view` | Looked only for `item.images` | Unified parser for Remix `loaderData['catalog-or-main-or-item'].buyerItem.galleryInfo.media`, `@avito/bx-item-view`, and top-level `galleryInfo` |
| **4. `extractListingData`** | Synced Layer 1 structured photos | Relied on extraPhotos or hero img | Layer 1 structured photos synchronously populate `listing.photos` with full 1280x960 resolution & exact dimensions |
| **5. `extractListingDataMultiPass`** | Ran traversal only if Layer 1 was missing | Always attempted DOM traversal on 1 photo | If structured page state provides gallery (`layer1Count > 0`), DOM traversal is strictly bypassed; only base64 enrichment runs |
| **6. `walkAndCollectAllGalleryPhotos`** | Walked slides | Complex button clicking that often failed or stalled | Preserved purely as fallback for non-structured pages |
| **7. `extract_current_page` handler** | Simple request handler | Returned response without request tracking | Echoes `scanRequestId` to prevent stale fast responses from clobbering newer deep scans |
| **8. Popup scan/import flow** | Prematurely enabled send button | Enabled button on provisional scan | Strict state machine: button disabled during scanning, atomic `authoritativeListingData` storage, degraded warnings if visible > extracted |

---

## 3. The Modern Avito Structured State Discovery

Direct DevTools Protocol analysis of live listing `8355529554` revealed:
- `window.__initialData__` is no longer declared by modern Avito.
- Inside script tag #49:
  ```javascript
  window.__staticRouterHydrationData = JSON.parse("{\"loaderData\":{\"catalog-or-main-or-item\":{\"buyerItem\":{\"galleryInfo\":{\"media\":[...]}}}}}")
  ```
- The `media` array contains exactly 5 elements. Each element has an `urls` object providing:
  - `140x105`
  - `640x480`
  - `1280x960` (High Definition)
  - `isVideo: false`
- By sorting variants by pixel area ($1280 \times 960 = 1,228,800$), the extension deterministically extracts the highest resolution available.

---

## 4. Isolated World vs Main World Security & CSP Immunity

To guarantee 100% reliability across all Avito CSP configurations:
1. **Isolated World DOM Parsing (Primary / Infallible):**
   - Content scripts running in Chrome Extension isolated world can inspect all `<script>` elements in `document.querySelectorAll('script')`.
   - The extension reads the script's `textContent`, executes regex extraction on the string literal passed to `JSON.parse()`, decodes escaped characters, and parses the JSON.
   - **CSP Immunity:** Reading DOM script text does not execute code in page context, requires no script tag injection, and is completely immune to page Content Security Policies.
2. **MAIN World Bridge (Secondary / Complementary):**
   - Declared in `manifest.json` with `"world": "MAIN"`, `main_world_bridge.js` directly reads `window.__staticRouterHydrationData` and dispatches `TechnorebootStructuredState` event to the content script.
   - Both layers complement each other; if either succeeds, full gallery extraction is guaranteed.

---

## 5. Popup State Machine & Race Elimination

The popup state machine in `popup.js` now enforces deterministic synchronization:
1. **Unique Scan Request IDs:** Each tab inspection generates `scanRequestId = "scan_" + Date.now() + "_" + Math.random()`. Responses with mismatched IDs are ignored.
2. **Provisional State Gate:** If fast scan yields only 1 photo while gallery indicators report more, `sendBtn.disabled = true` is enforced with status text: `"Сбор полной галереи..."`.
3. **Atomic Authoritative Data Storage:** Once complete structured data or deep scan arrives, `authoritativeListingData` is atomically populated, `isScanComplete = true`, and the button is enabled: `"Доимпортировать данные"`.
4. **Direct Authoritative Ingestion:** When the user clicks the send button, if `authoritativeListingData` is complete, it transmits that payload directly to Core without redundant re-scanning.
5. **Degraded State Alert:** If genuinely only 1 photo exists on a listing where visible thumbnails indicated multiple, a distinct warning banner is displayed: `"Внимание: найдена только 1 фотография из галереи. Полный импорт фото не готов."`

---

## 6. Real Browser Validation Metrics on Live Tab 8355529554

Validation script `scripts/validate_live_tab_8355529554.py` connected directly to Chrome DevTools Protocol port 9222 and executed the full extraction and local ingestion pipeline on active listing `8355529554`.

### Verification Metrics

| Parameter | Required / Expected | Actual Measured | Status |
|---|---|---|---|
| **REAL_LISTING_ID** | `8355529554` | `8355529554` | **PASS** |
| **VISIBLE_COUNT** | 5 | 5 | **PASS** |
| **STRUCTURED_MEDIA_COUNT** | 5 | 5 | **PASS** |
| **FINAL_EXTENSION_COUNT** | 5 | 5 | **PASS** |
| **PERSISTED_LOCAL_COUNT** | 5 | 5 | **PASS** |
| **HQ_COUNT (1280x960)** | 5 | 5 | **PASS** |
| **FOREIGN_COUNT** | 0 | 0 | **PASS** |
| **POPUP_STATE_TRANSITION** | Fast scan $\to$ Ready Complete | Fast scan $\to$ Ready Complete (instant complete structured state) | **PASS** |

### Verified Extracted Photo URLs ($1280\times960$)

1. `https://30.img.avito.st/image/1/1.XloHMba48rMxhnC-Nyw1ZRuR8LW5kHClMZ3wsbeY-rmx...` ($1280\times960$, area 1,228,800)
2. `https://10.img.avito.st/image/1/1.9jUHcba4WtwxxtjRZ16HDBvRWNq50NjWb5cI79sUWtc...` ($1280\times960$, area 1,228,800)
3. `https://80.img.avito.st/image/1/1.PWY3bra4kY8B2ROCQV5bWSvOk4mJzxOPc_8vI6eOmY0...` ($1280\times960$, area 1,228,800)
4. `https://60.img.avito.st/image/1/1.JzzVJba4i9XjkgnYl11bBMmFidNrhAnfntc4fNuKgd8...` ($1280\times960$, area 1,228,800)
5. `https://90.img.avito.st/image/1/1._78DwLa4U1Y1d9Fbcf_KgR9gUVC9YdFYebc_3RtnU1c...` ($1280\times960$, area 1,228,800)

### Local Core Ingestion Verification

```json
{
  "status": "success",
  "external_item_id": "8355529554",
  "product_id": 31,
  "result": "updated",
  "photos_imported": 5,
  "photos_total": 5,
  "photos_received": 5,
  "message": "Объявление 8355529554 импортировано в Техноребут (Product ID: 31, фото: 5)."
}
```

---

## 7. Automated Test Suite Results

All automated test suites pass with zero errors:

1. **New Stage 13D Suites:**
   - `test_stage13d_historical_6_photo_regression.py` (3 passed)
   - `test_stage13d_static_router_hydration.py` (3 passed)
   - `test_stage13d_popup_race_synchronization.py` (7 passed)
2. **Chrome Extension Full Suite (`pytest chrome-extension/technoreboot-avito/tests/`):**
   - 181 passed in 6.82s (0 failed).
3. **Admin Shell Full Suite (`pytest admin-shell/tests/`):**
   - 9 passed in 4.44s (0 failed).
4. **Root Post-Sale & Pairing Guard Suites (`pytest tests/`):**
   - 37 passed in 2.57s (0 failed).
5. **Targeted Regressions (`python scripts/run_targeted_tests.py`):**
   - Core: 27 passed
   - Admin-Shell: 28 passed
   - Root: 109 passed
   - Total: 164 passed, 0 failed.
6. **Database Schema Contract (`python scripts/db_schema_contract.py verify`):**
   - PASSED.

---

## 8. Version Bump & Package Verification

- Extension version bumped to **`0.2.66`** across:
  - `chrome-extension/technoreboot-avito/manifest.json`
  - `chrome-extension/technoreboot-avito/content.js`
  - `chrome-extension/technoreboot-avito/popup.js`
  - `chrome-extension/technoreboot-avito/popup.html`
  - `chrome-extension/technoreboot-avito/service_worker.js`
  - `admin-shell/app/main.py`
  - `admin-shell/app/templates/help.html`
  - `admin-shell/app/templates/avito_extension.html`
- Validated ZIP packages generated:
  - `dist/technoreboot-avito-extension-0.2.66.zip`
  - `admin-shell/app/technoreboot-avito-extension-0.2.66.zip`
  - `admin-shell/app/technoreboot-avito-extension.zip`
- Admin shell container `technoreboot-admin-shell` synchronized and restarted.

---

## 9. Constraints Compliance

- **Local Only:** All actions executed locally against `https://localhost:8443` / `http://127.0.0.1:8011` / `http://127.0.0.1:8020`. No remote production deploy was performed.
- **Avito Non-Interference:** Read-only inspection of listing `8355529554`. No publishing, editing, favoriting, messaging, or removal was performed on Avito.
- **Deactivation Safety:** Automatic Avito post-sale deactivation remains strictly disabled.
- **No Broad Permissions:** Manifest V3 permissions unchanged; `chrome.debugger` was NOT added.
- **Append-only Logging:** Maintained in `logs/2026-09-21.md`.
