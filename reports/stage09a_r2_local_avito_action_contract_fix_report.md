# Stage 09A-R2 LOCAL Report: Avito Action Contract Fix, Sale Detail UX & Real Browser Execution

**Stage:** Stage 09A-R2 LOCAL  
**Date:** 2026-09-14  
**Target Environment:** LOCAL Development Workstation (`https://localhost:8443`)  
**Production VDS Impact:** **NONE (STRICT LOCAL DEV ONLY — Zero operations on VDS 144.31.50.134)**  
**Extension Version:** `0.2.59`  
**Status:** **SUCCESS / READY FOR OWNER ACCEPTANCE**

---

## 1. Problem Statement & Root Cause

During real Owner browser testing on local workstation with Sale #1 (Avito ID `7353766377`), the post-sale deactivation task failed with:
```text
Status: manual_required
Attempts: 1 / 3
Error: Unsupported action: deactivate
```

### Root Cause Analysis
1. **Core Business Model & Database:**
   - In `core/app/models.py`, `avito_post_sale_tasks.action` defaults to `"deactivate"`.
   - Core router `/api/avito/post-sale-tasks/next` returned `"action": task.action` (`deactivate`).
2. **Chrome Extension Contract Expectation:**
   - In Chrome Extension v0.2.58 `service_worker.js`, the task dispatcher enforced:
     ```javascript
     if (task.action !== "deactivate_listing") {
         throw new Error(`Unsupported action: ${task.action}`);
     }
     ```
   - Because `deactivate` != `deactivate_listing`, the extension immediately rejected the task and reported it as failed.
3. **Sale Detail UX Gaps (Section 6A):**
   - The post-sale deactivation prompt on the sale receipt was only shown immediately after checkout; if the seller clicked "Не сейчас" or re-opened `/sales/{id}`, there was no permanent button to trigger deactivation.
4. **Proxy Location Rewriting (Admin-Shell):**
   - In `admin-shell/app/main.py`, `rewrite_location_header` lacked `/sales` in its known-prefixes whitelist, which caused redirects from `/sales/{id}/avito-deactivate` to produce duplicate prefixes (`/sales/sales/{id}` -> 404).

---

## 2. Architecture & Key Solutions

### A. Action Contract Alignment (Zero DB Migration)
Rather than performing a risky database migration or mutating historic tasks, an adapter pattern was implemented:
- **Bridge Adapter (`avito-module/app/routers/extension_bridge.py`):**
  - Defines `BUSINESS_ACTION_DEACTIVATE = "deactivate"` and `EXTENSION_ACTION_DEACTIVATE_LISTING = "deactivate_listing"`.
  - In `get_next_extension_task`: transforms business action `deactivate` to `deactivate_listing` when serializing the task payload for the Chrome extension.
  - Bumped status and payload versions to `0.2.59`.
- **Chrome Extension Dual-Action Tolerance (`service_worker.js`):**
  - Configured `SUPPORTED_DEACTIVATION_ACTIONS = ["deactivate_listing", "deactivate"]`.
  - Accepts both actions safely.
  - Defense-in-depth: strictly rejects unauthorized / dangerous actions (e.g. `delete_account`, `publish_listing`, `pay_promotion`) with `Unsupported action: ${task.action}`.

### B. Section 6A: Permanent Sale Detail UX (`sales_detail.html` & `sales.py`)
- **Permanent Action Button:** Added `#btnPermanentAvitoDeactivate` `[ Снять с Avito ]` in the top action bar next to `[ Товарный чек ]`.
- **Multi-Item Confirmation:** If multiple Avito items are present, prompts a confirmation dialog displaying the exact listing count before submitting.
- **Honest Feedback Banners:**
  - `✓ Объявление уже снято с Avito` (when remote status is already archived/inactive).
  - `ⓘ Задачи на снятие с Avito уже обрабатываются` (when tasks are currently in queue/processing).
  - `ⓘ Для этой продажи нет связанных объявлений Avito` (when sale contains no Avito-linked products).
  - `✓ Задачи на снятие с Avito поставлены в очередь` (when tasks are successfully enqueued).
- **Proxy Location Rewrite Fix:** Updated `admin-shell/app/main.py` `rewrite_location_header` to prevent double `/sales` prefixes on 303 redirects.

### C. Section 6B: Direct Navigation & Robust DOM Discovery (`content.js` & `service_worker.js`)
- **Canonical URL Navigation:** Extension navigates directly to `https://www.avito.ru/{avito_listing_id}` or canonical item URL.
- **Exact ID Verification:** Implemented `extractAvitoItemId(url)` to parse IDs from trailing slugs, `/items/{id}`, query parameters, canonical link tags, and meta tags. Aborts with `manual_required` if the page does not match `task.avito_listing_id`.
- **Deep Menu & Profile Card Discovery:** Searches for deactivation buttons in primary page headers, dropdown action menus (`...`, `Действия`), and profile item rows (`/profile/items`).
- **Tab Focus Preservation:** Captures `originalTabId` before opening the task tab. Upon completing execution in Armed mode, restores focus to the seller's tab and closes the temporary Avito tab.

---

## 3. Package & Version Bump (v0.2.59)

All extension components were synchronized to version `0.2.59`:
1. `chrome-extension/technoreboot-avito/manifest.json` (`"version": "0.2.59"`)
2. `chrome-extension/technoreboot-avito/service_worker.js` (`VERSION = "0.2.59"`)
3. `chrome-extension/technoreboot-avito/content.js` (`VERSION = "0.2.59"`)
4. `chrome-extension/technoreboot-avito/popup.html` (`v0.2.59`)
5. `chrome-extension/technoreboot-avito/popup.js` (`VERSION = "0.2.59"`)
6. `admin-shell/app/main.py` (`FALLBACK_VERSION = "0.2.59"`)
7. `admin-shell/app/templates/avito_extension.html` (`Скачать расширение v0.2.59`)
8. ZIP Archives rebuilt via `scripts/build_extension_zip.py`:
   - `dist/technoreboot-avito-extension-0.2.59.zip` (71,671 bytes)
   - `admin-shell/app/technoreboot-avito-extension.zip` (71,671 bytes)

---

## 4. Verification Results

### A. Automated Test Suites (`scripts/run_targeted_tests.py`)
- **Core Tests:** 27 passed, 0 failed.
- **Admin-Shell Tests:** 28 passed, 0 failed (including location rewrite tests).
- **Root Tests:** 94 passed, 0 failed (including RBAC, pairing lifecycle, post-sale deactivation, schema guards).
- **Result:** **ALL TARGETED SUITES PASSED! FAILED = 0**.

### B. Real Local Owner Contract Verification (`scripts/verify_stage09a_r2_action_contract.py`)
Tested real Task #2 (`avito_listing_id: 7353766377`, from Sale #1):
1. Extension package v0.2.59 verified across all files and ZIP contents.
2. Live mTLS download endpoint `/avito/extension/download` returned v0.2.59 ZIP.
3. Extension paired and verified online with version `0.2.59`.
4. Bridge adapter polled Task #2: DB business `deactivate` correctly serialized to `deactivate_listing`.
5. Task #2 marked `started` and transitioned to `processing` without `Unsupported action` error.
6. Dry-run safety verified: destructive clicks blocked, safe report recorded.
7. Sale #1 detail page verified: renders permanent `#btnPermanentAvitoDeactivate` button.
8. Permanent `[ Снять с Avito ]` action triggered, followed redirect to `/sales/1?avito_msg=queued_1` without double-prefixing.
9. DB state preserved cleanly; Task #2 reset to `queued` ready for Owner browser testing.

---

## 5. Invariant Checks

| Invariant | Requirement | Verification Result |
| :--- | :--- | :--- |
| **Local Dev Only** | Zero operations on VDS `144.31.50.134` | **VERIFIED:** Zero VDS interactions; all work executed on local workstation |
| **Sale Integrity** | Sale completion never blocked by Avito | **VERIFIED:** Core sales creation unaffected |
| **Stock Non-Mutation** | Physical stock never altered by Avito tasks | **VERIFIED:** Quantities unaffected |
| **Action Contract** | No `Unsupported action: deactivate` error | **VERIFIED:** Bridge adapter maps action, SW accepts both |
| **Dry-Run Safety** | No real Avito click when dry-run is active | **VERIFIED:** Highlighting only; destructive click blocked |
| **Schema Guard** | `requires_manual_migration: true` | **VERIFIED:** Guard remains active, VDS migration blocked |

---

## 6. Real Owner Testing Instructions

To test in local Chrome browser:
1. Open Chrome -> `chrome://extensions`.
2. Ensure Developer Mode is ON.
3. If already installed, click the reload icon on "Technoreboot Avito Integration", or "Load unpacked" from `c:\tbootit\chrome-extension\technoreboot-avito`.
4. Verify extension badge / popup displays version `0.2.59`.
5. Open `https://localhost:8443/sales/1` (accept cert if prompted).
6. Note the permanent `[ Снять с Avito ]` button next to `[ Товарный чек ]`.
7. Task #2 (`7353766377`) is currently in `queued` state:
   - With the extension running, it will automatically poll Task #2 within 10 seconds.
   - It will open the Avito page for `7353766377`.
   - In Dry-Run mode, it highlights the deactivation control in yellow dashed outline and displays the on-page banner "⚠️ ТЕСТОВЫЙ РЕЖИМ (Dry-Run)".
   - No `Unsupported action` error occurs.
   - It restores tab focus to your working tab.
