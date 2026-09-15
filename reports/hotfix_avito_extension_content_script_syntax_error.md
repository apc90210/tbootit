# Emergency Hotfix Report: Chrome Extension Content Script Syntax Error

- **Date:** 2026-09-15
- **Component:** Chrome Extension (`chrome-extension/technoreboot-avito`) & Admin Shell (`admin-shell/app/technoreboot-avito-extension.zip`)
- **Status:** FIXED, VALIDATED, TESTED, PACKAGED

---

## 1. Problem Description & User Symptoms
- **User Symptom:**
  When opening the TechnoReboot Chrome extension on individual Avito item pages (e.g. `https://www.avito.ru/moskva/...`), parsing fails completely. The popup UI continuously displays:
  > *"Обновите страницу Avito (F5) для активации расширения."*
  Refreshing the page (F5) never resolves the issue.

---

## 2. Root Cause Analysis
1. In `chrome-extension/technoreboot-avito/content.js`:
   During the Stage 09A-R4 Avito post-sale deactivation refactoring, the function `waitForConfirmedInactiveState` around line 4581 was modified to poll for item status. A `while (Date.now() - startTime < timeoutMs)` loop was introduced without its closing curly brace `}`.
2. Because of this missing closing brace, Google Chrome's V8 JavaScript engine failed to parse `content.js`, throwing `SyntaxError: Unexpected token ')'` at file evaluation.
3. Because compilation failed, Chrome never injected or executed `content.js` into the Avito tab DOM.
4. When `popup.js` called `sendMessageToTabWithAutoInject(activeTab.id, { action: "extract_current_page" })`, no content script listener answered.
5. In `popup.js:1329`, if `response` is null/undefined, it executes the fallback error handler:
   `pageDetectInfo.textContent = "Обновите страницу Avito (F5) для активации расширения."`.
6. Additional observation: `content.js` contained stale hardcoded version strings (`"0.2.57"` and `"0.2.60"`) in fallback structures instead of reading the dynamic extension manifest version (`0.2.62`).

---

## 3. Implementation of the Fix
1. **Syntax Fix in `content.js`:**
   - Added the missing `}` to properly close the `while` loop inside `waitForConfirmedInactiveState`.
2. **Dynamic Versioning in `content.js`:**
   - Added helper `getExtensionVersion()` which queries `chrome.runtime.getManifest().version` (fallback `"0.2.62"`).
   - Replaced all hardcoded version strings with `getExtensionVersion()`.
3. **Automated JS Syntax Packaging Guard in `scripts/validate_extension_package.py`:**
   - Updated `validate_extension_directory()` to evaluate every `.js` file via Playwright Chromium V8 runtime (`page.evaluate("code => new Function(code)", code)`).
   - Any JavaScript syntax error now immediately terminates the build/validation process with a clear diagnostic message.
4. **Regression Test Scripts:**
   - `scripts/test_extension_syntax.py`: Tests that all extension scripts (`content.js`, `popup.js`, `service_worker.js`) compile without syntax errors.
   - `scripts/test_content_script_extraction.py`: Mocks an Avito listing DOM, injects `content.js`, sends `extract_current_page`, and verifies extracted data structure.

---

## 4. Verification & Testing
1. **Syntax Verification:**
   - `content.js`: PASS
   - `popup.js`: PASS
   - `service_worker.js`: PASS
2. **Listing Extraction Verification:**
   - Simulated Avito listing extraction verified end-to-end: item ID, title, price, description, parameters, HD photos, diagnostics.
3. **Packaging & Download Verification:**
   - Built ZIP packages via `scripts/build_extension_zip.py`.
   - Validated ZIP via `scripts/validate_extension_package.py`: PASS.
   - Local Admin Shell container restarted and served `https://localhost:8443/avito/extension/download` (HTTP 200, valid 70,871 byte ZIP).
4. **Full Test Suite:**
   - All 164 tests across `core`, `admin-shell`, and root test suites passed (0 failures).
