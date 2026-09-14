# Stage 09A-R5 LOCAL Report: Operator-Assisted Manual Avito Deactivation Flow

**Stage:** Stage 09A-R5 LOCAL  
**Date:** 2026-09-14  
**Status:** SUCCESS / READY FOR OWNER ACCEPTANCE  
**Target Environment:** LOCAL Development Sandbox (`https://localhost:8443`)  
**Production VDS (`144.31.50.134`):** STRICT ZERO OPERATIONS (Code, DB, and state untouched)  

---

## 1. Executive Summary

Based on Owner feedback and real-world evaluation, automatic browser DOM deactivation across dynamic marketplace UIs introduces unacceptable operational brittleness. In **Stage 09A-R5**, TechnoReboot completely eliminated automatic DOM clicking from the normal seller workflow, replacing it with an **operator-assisted manual flow**:

1. **Clear Post-Sale Prompt:** When a sale is completed for a product with an active linked Avito listing, the seller is presented with a prominent post-sale card: "Снять объявление с Avito?"
2. **`[ ↗ Снять с Avito вручную ]`:** Opens the exact canonical Avito URL (`https://www.avito.ru/{id}`) in a new browser tab (`target="_blank"`, `rel="noopener noreferrer"`).
   - **Crucial Invariant:** Opening the page transitions the post-sale task to `manual_required`. It **NEVER** marks the task as `success` merely because the page was opened.
   - The original TechnoReboot sales tab remains completely intact and active.
3. **`[ Не снимать ]`:** Dismisses the prompt and transitions the task to `canceled`.
   - **Crucial Invariant:** Does NOT mutate the listing status in `product_external_listings` (it remains `active`).
   - Does NOT roll back, cancel, or modify the completed sale or physical inventory.
4. **Permanent Action on Sale Detail (`/sales/{id}`):** Located in the action bar adjacent to `[ Товарный чек ]`, with 3 honest states:
   - No linked listing: Disabled button `Для этой продажи нет связанного объявления Avito`.
   - Already inactive: Disabled button `✓ Объявление уже снято с Avito`.
   - Active linked listing: `[ ↗ Снять с Avito вручную ]` (or modal trigger for multi-item cart sales).
5. **Optional Manual Confirmation (`[ ✓ Я снял объявление ]`):** When the operator completes manual removal on Avito, they can click this button on the sale page or in the post-sale queue. This marks the task `success`, `execution_mode = manual`, updates `product_external_listings.remote_status = 'archived'`, and writes an audit event.
6. **Operator Queue UI (`/avito/post-sale`):** Clean, operator-oriented table with columns: *Дата, Продажа, Товар, Avito ID, Статус, Действие* with contextual actions.
7. **Chrome Extension v0.2.61:** Automatic polling alarms (`chrome.alarms.create`) and DOM auto-clicker routines are completely disabled and inerted. Packages rebuilt for distribution.
8. **Automated & Live Verification:** All 158 targeted tests passed cleanly. Live 12-point end-to-end verification script passed 100%.

---

## 2. Core Architectural Changes

### 2.1 Backend Router (`core/app/routers/avito_post_sale.py`)
- Added `_canonical_avito_url(listing_url, avito_listing_id)` enforcing security validation: hostname must be `avito.ru` / `*.avito.ru` and must match the linked `avito_listing_id`.
- Added `POST /api/avito/post-sale-tasks/{task_id}/mark-opened`: transitions `suggested` or `queued` tasks to `manual_required` (never `success`).
- Added `POST /api/sales/{sale_id}/avito-manual-open`: batch-transitions a sale's tasks to `manual_required`.
- Added `POST /api/avito/post-sale-tasks/{task_id}/manual-confirm`: records operator manual deactivation, transitions task to `success`, sets listing `remote_status = 'archived'`, and logs audit event `avito_listing_deactivated_after_sale`.
- Added `POST /api/sales/{sale_id}/avito-manual-confirm`: batch confirmation for all tasks of a sale.
- Added `POST /api/sales/{sale_id}/avito-dismiss`: transitions tasks to `canceled` without touching listing or sale.
- Enriched `get_sale_avito_tasks` with `has_linked_listings` and `all_archived` metadata.

### 2.2 Inventory & Sales Module (`inventory-sales-module`)
- **`app/core_client.py`:** Added async client methods `mark_sale_manual_open`, `manual_confirm_sale_avito`, `dismiss_sale_avito`, `mark_task_opened`.
- **`app/routers/sales.py`:** 
  - Passed `has_linked_listings` and `all_archived` to template context.
  - Added endpoints `/sales/{sale_id}/avito-manual-open`, `/sales/{sale_id}/avito-manual-confirm`, `/sales/{sale_id}/avito-dismiss`.
- **`app/templates/sales_detail.html`:**
  - Added large post-sale prompt `#avito-post-sale-prompt`.
  - Added permanent action bar button `#btnPermanentAvitoDeactivate` with 3 honest states.
  - Added manual confirmation banner when listing has been opened (`manual_required`).
  - Added multi-listing modal `#modalMultiAvito` for cart sales with >1 linked listing.
  - Added safe `handleManualOpen` JavaScript helper to notify backend when the operator clicks to open Avito.

### 2.3 Admin-Shell & Queue UI (`admin-shell`)
- **`app/main.py`:** Added proxy routes for `/manual-confirm` and `/mark-opened`. Bumped extension fallback version to `0.2.61`.
- **`app/templates/avito_post_sale.html`:** Redesigned table with operator columns: *Дата, Продажа, Товар, Avito ID, Статус, Действие*. Integrated `[ ↗ Открыть объявление ]`, `[ Не снимать ]`, and `[ ✓ Я снял объявление ]`.
- **`app/templates/avito_extension.html`:** Bumped download link to `v0.2.61`.

### 2.4 Chrome Extension v0.2.61 (`chrome-extension/technoreboot-avito`)
- **`manifest.json`:** Bumped version to `0.2.61`.
- **`service_worker.js`:** Completely removed `chrome.alarms.create` and polling intervals. `pollNextDeactivationTask` disabled and made inert. `trigger_poll_tasks` disabled.
- **`content.js`:** `execute_deactivation` inerted (returns `status: "disabled"`).
- **`popup.html` & `popup.js`:** Removed obsolete auto-deactivation DOM click steps (`#stepExecuting`, etc.). Displayed clean status and version `0.2.61`.
- **ZIP Archives Rebuilt:**
  - `dist/technoreboot-avito-extension-0.2.61.zip`
  - `admin-shell/app/technoreboot-avito-extension.zip`

---

## 3. Invariant Verification

| Invariant | Requirement | Result |
| :--- | :--- | :--- |
| **No Auto-Clicking** | System must never auto-click Avito DOM controls in normal workflow | **VERIFIED** (Extension background alarms and click routines disabled) |
| **Opening != Success** | Opening listing must transition task to `manual_required`, NEVER `success` | **VERIFIED** (Pass 6 in verification script) |
| **Tab Isolation** | Listing opens in new browser tab (`target="_blank"`, `rel="noopener noreferrer"`) | **VERIFIED** (Pass 4 in verification script) |
| **"Не снимать" Safety** | Dismiss transitions task to `canceled`, preserves active listing, sale completed | **VERIFIED** (Pass 5 in verification script) |
| **Permanent Action** | Sale detail maintains honest permanent button adjacent to receipt | **VERIFIED** (Pass 4 & 8 in verification script) |
| **Manual Confirmation** | `[ Я снял объявление ]` transitions to `success`, listing to `archived`, logs audit event | **VERIFIED** (Pass 7 in verification script) |
| **Business Integrity** | Completed sale amount and product inventory are NEVER touched | **VERIFIED** (Pass 10 in verification script) |
| **URL Security** | Only canonical `avito.ru` hostname and linked listing ID permitted | **VERIFIED** (Pass 4 in verification script) |
| **Zero VDS Impact** | Zero operations or deployments on VDS `144.31.50.134` | **VERIFIED** (Pass 11 in verification script) |

---

## 4. Test Suite Execution Results

### 4.1 Automated Tests (`python scripts/run_targeted_tests.py`)
- **Core Test Suite:** 27 passed in 4.11s
- **Admin-Shell Test Suite:** 28 passed in 4.86s
- **Root & Integration Test Suite:** 103 passed in 13.06s (including `tests/test_stage09a_r5_manual_flow.py`)
- **TOTAL:** **158 passed, 0 failed**

### 4.2 Live End-to-End Verification (`python scripts/verify_stage09a_r5_manual_flow.py`)
1. `[PASS]` 1. Extension Package v0.2.61 verified: background alarms and auto-clickers disabled.
2. `[PASS]` 2. Live download endpoint returned v0.2.61 ZIP (70,217 bytes).
3. `[PASS]` 3. Sale #1 verified: status=completed, total=900.0 RUB.
4. `[PASS]` 4. Sale detail UI verified: large prompt, exact canonical URL, and permanent button.
5. `[PASS]` 5. 'Не снимать' verified: task canceled, listing NOT mutated (remains active), sale completed.
6. `[PASS]` 6. Manual open verified: task transitioned to `manual_required` (NOT `success`).
7. `[PASS]` 7. Manual confirmation verified: task=`success`, listing=`archived`, audit log written.
8. `[PASS]` 8. Sale Detail UI verified: honest 'Объявление уже снято с Avito' displayed.
9. `[PASS]` 9. Queue UI `/avito/post-sale` verified: operator-oriented columns and actions.
10. `[PASS]` 10. Business integrity verified: Sale #1 amount=900.0, Product #141 stock=0.
11. `[PASS]` 11. Zero VDS interaction verified: strictly local development.
12. `[PASS]` 12. Task #2 reset to `suggested` (ready for Owner Chrome browser acceptance).

---

## 5. Owner Acceptance Guide

To test the Stage 09A-R5 operator-assisted manual flow in your local Chrome browser:

1. **Reload Extension (if using extension):**
   - In Chrome, navigate to `chrome://extensions`.
   - Click the reload icon on **TechnoReboot Avito Assistant** to load `v0.2.61`.
2. **Open Sale #1:**
   - In Chrome, open `https://localhost:8443/sales/1`.
3. **Verify Post-Sale Prompt:**
   - Notice the prominent prompt: **"Снять объявление с Avito?"**
   - Click **`[ ↗ Снять с Avito вручную ]`**:
     - Avito listing `https://www.avito.ru/ekaterinburg/tovary_dlya_kompyutera/amd_athlon_x4_950_am4._garantiya_7353766377` opens in a **new tab**.
     - The TechnoReboot sale tab remains on `/sales/1`.
     - The page displays: `✓ Ссылка на объявление открыта в новой вкладке. Снимите его с публикации на Avito вручную.` along with the green button **`[ ✓ Я снял объявление ]`**.
4. **Confirm Deactivation:**
   - Click **`[ ✓ Я снял объявление ]`**:
     - The prompt confirms the deactivation.
     - The permanent button displays: **`✓ Объявление уже снято с Avito`**.
5. **Verify Queue UI:**
   - Navigate to `https://localhost:8443/avito/post-sale`.
   - Verify the table columns (*Дата, Продажа, Товар, Avito ID, Статус, Действие*) and the archived listing status.
