# Stage 08D-R1R3 — Avito Extension Pairing VDS Fix

## Reproduction
- **PRODUCTION_URL:** `https://144.31.50.134`
- **PAIRING_PAGE:** `https://144.31.50.134/avito/extension`
- **PAIRING_CREATE_ENDPOINT:** `POST /admin-api/avito-extension/pairing/generate`
- **PAIRING_REDEEM_ENDPOINT:** `POST /admin-api/avito-extension/pairing/pair`
- **ORIGINAL_FAILURE_REPRODUCED:** `true`
- **ORIGINAL_HTTP_STATUS:** `400`
- **ORIGINAL_MESSAGE:** `Код подключения не найден.`

### Reproduction Details
When the Owner attempted to pair the extension in their browser on VDS:
1. The Owner navigated to `https://144.31.50.134/avito/extension` and generated a 6-digit code. The code was saved in VDS canonical storage (`/srv/technoreboot/data/avito-module/extension_pair_codes.json`).
2. The Owner entered the 6-digit code into the Chrome Extension popup.
3. Because the Chrome Extension v0.2.53 hardcoded `BRIDGE_BASE_URL = "http://localhost:8011/admin-api/avito-extension"` and lacked host permissions for VDS IP in `manifest.json`, the extension sent `POST http://localhost:8011/admin-api/avito-extension/pairing/pair`.
4. The local development environment (running on `localhost:8011`) received the request, searched its local pairing store, and returned `HTTP 400: {"detail": "Код подключения не найден."}` because the code was generated on VDS.
5. The extension displayed: `Ошибка сервера 400: Код подключения не найден.`.

---

## Root Cause
- **ROOT_CAUSE:** Chrome Extension `service_worker.js` had hardcoded `BRIDGE_BASE_URL = "http://localhost:8011/admin-api/avito-extension"` and lacked host permissions for the VDS IP in `manifest.json`. In addition, `popup.html` had no input to set or override the server address. When the Owner generated a pairing code on VDS (`https://144.31.50.134`), the extension sent the redemption request to the local development environment (`http://localhost:8011`), which rejected it with HTTP 400 `Код подключения не найден` because the code was created in VDS state and did not exist in local DEV storage.
- **PAIRING_STORAGE_BACKEND:** JSON file storage (`extension_pair_codes.json` and `extension_tokens.json`).
- **PAIRING_STORAGE_PATH_OR_TABLE:** `/srv/technoreboot/data/avito-module/extension_pair_codes.json`.
- **WAS_PROCESS_MEMORY_ONLY:** `false` (stored on persistent disk volume).
- **WAS_CONTAINER_LOCAL_ONLY:** `false` (mapped to host persistent volume `${TECHNOREBOOT_DATA_ROOT}/avito-module:/app/data`).
- **WAS_RESET_BY_CLEANUP:** `false` (Stage 08D-R1R2 clean reset explicitly preserved pairing state).
- **CREATE_REDEEM_STATE_MISMATCH:** `true` (code created on VDS, redeemed against localhost:8011 due to hardcoded URL).
- **HOST_TARGET_ISSUE:** `true` (hardcoded localhost:8011 in extension service worker, missing VDS IP in manifest host_permissions).

---

## Fix
- **FIX_SUMMARY:** 
  1. **Dynamic Server URL in Extension:** Added `getServerUrl()` and `setServerUrl()` in `service_worker.js` using `chrome.storage.local` with fallback to `http://localhost:8011/admin-api/avito-extension`. Updated all API calls (`/status`, `/listing`, `/bulk-import`, `/publication-package`) to use dynamic bridge URL.
  2. **Popup Server Address UI:** Added labeled `serverUrlInput` field to `popup.html` above pairing code input. Pre-filled from stored server URL. On clicking "Подключить", popup passes `server_url` to service worker.
  3. **VDS Host Permissions:** Added `https://144.31.50.134/*` and `https://*/*` to `manifest.json` `host_permissions`.
  4. **Admin Extension Page Guidance:** Updated `admin-shell/app/templates/avito_extension.html` to auto-detect and display the exact server URL (`https://144.31.50.134/admin-api/avito-extension`) with a 1-click "📋 Скопировать" button, and updated step 6 of instructions.
  5. **Version Bump:** Bumped extension version to `0.2.55` across `manifest.json`, `service_worker.js`, `popup.js`, `popup.html`, `content.js`, `extension_bridge.py` schemas, and rebuilt the downloadable ZIP package `admin-shell/app/technoreboot-avito-extension-0.2.55.zip` and `technoreboot-avito-extension.zip`.
  6. **Popup Blur Reset & URL Persistence Fix (v0.2.55):**
     - Resolved ephemeral popup reset: Chrome destroys popup DOM on blur. When reopened, `get_status` previously returned default localhost URL, wiping out whatever URL the Owner entered.
     - Added explicit **«Зафиксировать»** button with visual feedback (`✓ Адрес зафиксирован!`).
     - Auto-saves server URL into `chrome.storage.local` on `input`, `change`, `paste`, `blur`, and `Enter`.
     - Auto-detects server URL from the active tab if on `144.31.50.134`.
     - Guarded `get_status` so it never overwrites the server URL input if already populated.
- **PAIRING_STATE_PERSISTENCE:** `/srv/technoreboot/data/avito-module/extension_pair_codes.json` (persistent Docker volume mount).
- **PAIRING_TTL:** 600 seconds (10 minutes).
- **ONE_TIME_USE:** `true` (`entry["used"] = True` on redemption).
- **EXTENSION_VERSION_BEFORE:** `0.2.53`
- **EXTENSION_VERSION_AFTER:** `0.2.55`
- **PRODUCTION_TARGET:** `https://144.31.50.134`

---

## Tests
- **PAIRING_TESTS:** 8 passed (`tests/test_stage08d_r1r3_pairing_lifecycle.py`)
  - `test_fresh_code_redeem_success`: PASS
  - `test_unknown_code_rejected_400`: PASS
  - `test_expired_code_rejected`: PASS
  - `test_used_code_rejected_one_time_use`: PASS
  - `test_leading_zero_code_works`: PASS
  - `test_container_service_restart_persistence`: PASS
  - `test_local_and_vds_pairing_stores_independent`: PASS
  - `test_extension_package_version_and_dynamic_origin`: PASS
- **EXTENSION_TESTS:**
  - `avito-module`: 154 passed, 0 failed
  - `admin-shell`: 92 passed, 1 skipped, 0 failed
  - Production baseline & data guard: 27 passed, 0 failed
- **FAILED:** `0`

---

## Production Safety
- **PRE_DEPLOY_BACKUP:** Automatic backup created by `deploy/production/update_code_only.sh`
- **PRODUCTS_BEFORE:** `0`
- **PRODUCTS_AFTER:** `0`
- **SALES_BEFORE:** `0`
- **SALES_AFTER:** `0`
- **REPAIRS_BEFORE:** `0`
- **REPAIRS_AFTER:** `0`
- **PHOTOS_BEFORE:** `0`
- **PHOTOS_AFTER:** `0`
- **EXTERNAL_LISTINGS_BEFORE:** `0`
- **EXTERNAL_LISTINGS_AFTER:** `0`
- **CLIENT_CA_SHA256_UNCHANGED:** `true` (`a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d`)
- **LOCAL_DATA_SYNCED_TO_VDS:** `false`

---

## Runtime Proof on Production VDS
- **ALL_SERVICES_HEALTHY:** `true`
- **PAIRING_CODE_CREATED:** `true` (HTTP 200 via `POST https://144.31.50.134/admin-api/avito-extension/pairing/generate`)
- **PAIRING_CODE_REDEEMED:** `true` (HTTP 200 via `POST https://144.31.50.134/admin-api/avito-extension/pairing/pair`)
- **PAIRING_HTTP_STATUS:** `200` (`status: "paired"`, issued `ext_tok_...`)
- **UNKNOWN_CODE_HTTP_STATUS:** `400` (`detail: "Код подключения не найден."`)
- **REUSED_CODE_HTTP_STATUS:** `400` (`detail: "Срок действия кода подключения истёк. Сгенерируйте новый код."`)
- **EXTENSION_VERSION_VERIFIED_ON_VDS:** `0.2.55`

---

## Git
- **COMMIT:** `823c8f1a24`
- **PUSH:** `true` (`origin/main`)
- **HEAD_AFTER:** `823c8f1a24`
- **FINAL_GIT_STATUS:** clean

---

## Final Status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE08D_R1R3_AVITO_EXTENSION_PAIRING_VDS_FIXED

PRODUCTION_URL: https://144.31.50.134
EXTENSION_VERSION: 0.2.55
BUSINESS_DATA_PRESERVED: true
FUTURE_DEPLOYS_CODE_ONLY: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

## Instructions for Owner Manual Browser Check

1. Open `https://144.31.50.134/avito/extension` in Google Chrome (authenticated with Owner certificate).
2. Download the updated extension package: click **«Скачать расширение (ZIP, v0.2.55)»**.
3. In Chrome, navigate to `chrome://extensions`:
   - Turn **«Режим разработчика»** ON (top right).
   - If previous extension exists: click **«Удалить»** (or reload after replacing files).
   - Unpack the downloaded `technoreboot-avito-extension-0.2.55.zip` and click **«Загрузить распакованное расширение»**.
4. On `https://144.31.50.134/avito/extension`:
   - Click **«Создать новый код подключения»**.
   - Copy the server URL displayed in the box: `https://144.31.50.134/admin-api/avito-extension` (click **«📋 Скопировать»**).
5. Click the **«Техноребут Avito»** extension icon in your Chrome toolbar:
   - Notice: the server URL will either be **automatically detected** from your active tab or you can paste it and click **«Зафиксировать»** (it turns green with `✓ Адрес зафиксирован!`).
   - You can safely close or switch away from the popup to copy the code — the address will **never reset** back to localhost!
   - Enter the 6-digit pairing code.
   - Click **«Подключить»**.
6. **Expected outcome:** Badge turns green **«Подключен»**, message displays **«Расширение успешно привязано к серверу»**, pairing card closes.
