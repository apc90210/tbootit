# Stage 12A — Extension Connection Switching

## Overview
Implemented seamless connection switching and reconnection lifecycle for the TechnoReboot Avito Chrome extension (v0.2.63). The extension popup now clearly displays the currently connected server origin (`https://localhost:8443` or `https://144.31.15.88`), provides a prominent `[Отключиться]` button with confirmation prompt, cleanly wipes credentials upon disconnect without touching mTLS browser certificates or business data, and permits pairing with another server via a 6-digit code without browser restart or extension reinstallation.

## UI
CURRENT_SERVER_ADDRESS_VISIBLE: true
PAIRED_STATUS_VISIBLE: true
UNREACHABLE_STATUS_VISIBLE: true
DISCONNECT_BUTTON: true
RECONNECT_FORM: true
ACTIVE_TAB_PREFILL: true

## State
SINGLE_ACTIVE_CONNECTION: true
SERVER_URL_SOURCE_OF_TRUTH: chrome.storage.local (keys: `server_base_url`, `active_connection`, `extension_token`)
OLD_TOKEN_CLEARED_ON_DISCONNECT: true
ATOMIC_SWITCH: true
STALE_SERVER_STATE_PREVENTED: true

## Permissions
MV3_PERMISSION_STRATEGY: `host_permissions` retained for `https://localhost:8443/*` and `https://144.31.15.88/*`. Legacy `144.31.50.134` completely removed. `optional_host_permissions` added for `http://*/*` and `https://*/*` with runtime `chrome.permissions.request()`
RUNTIME_ORIGIN_PERMISSION: true
PERMISSION_DENIAL_HANDLED: true (explicit user warning displayed if permission is denied)

## Server Switching
LOCAL_TO_PROD: supported (disconnect -> prefill/enter `https://144.31.15.88` -> pair)
PROD_TO_LOCAL: supported (disconnect -> prefill/enter `https://localhost:8443` -> pair)
NO_REINSTALL_REQUIRED: true
LEGACY_VDS_NOT_DEFAULT: true (`144.31.50.134` purged from all defaults and active tab auto-detection)

## Security
TOKENS_HIDDEN: true (pairing token never displayed in UI)
SECRETS_NOT_LOGGED: true (no secrets emitted to console)
MTLS_CERT_NOT_REMOVED_BY_DISCONNECT: true (disconnect only clears extension chrome.storage.local state)

## Regression
PAIRING_STILL_WORKS: true
SINGLE_IMPORT_STILL_WORKS: true
PROFILE_IMPORT_STILL_WORKS: true
REVERSE_FLOW_STILL_WORKS: true
AUTO_AVITO_DEACTIVATION_STILL_DISABLED: true

## Build / Tests
EXTENSION_VERSION: 0.2.63
EXTENSION_ZIP: dist/technoreboot-avito-extension-0.2.63.zip
EXTENSION_ZIP_SHA256: bbaf780f75647c598c0725ad2de30239f865ea311ca529d405978960d1a16f9b
AUTOMATED_TESTS: 302 passed, 0 failed (164 targeted backend/integration tests + 138 extension unit and browser tests including 12 Stage 12A switching tests)
LOCAL_SMOKE: passed (verified admin-shell download endpoint v0.2.63, HTML template v0.2.63, and live avito-module /extension/api/pairing/revoke in Docker stack)

## Production
PRODUCTION_TOUCHED: false
PRODUCTION_DB_CHANGED: false
DEPLOYED_TO_144_31_15_88: false

FINAL_STATUS:
TECHNOREBOOT_STAGE12A_LOCAL_READY_FOR_OWNER_ACCEPTANCE

## Owner Browser-Only Acceptance Instructions
Owner does not need to use the command line. All testing is conducted directly in Google Chrome:

1. **Load updated extension in Chrome:**
   - Open `chrome://extensions`.
   - Enable "Developer mode" (Режим разработчика).
   - Click "Load unpacked" (Загрузить распакованное расширение) and select `C:\tbootit\chrome-extension\technoreboot-avito` (or download `https://localhost:8443/avito/extension/download` and unpack it).
   - If previously loaded, click the reload (🔄) button on the TechnoReboot card. Verify version shows `0.2.63`.

2. **Verify Connected State & Disconnect:**
   - Click the TechnoReboot extension icon in Chrome toolbar.
   - Observe the top Connection card:
     - Shows current connected address (e.g., `https://localhost:8443` or `https://144.31.15.88`).
     - Shows green status badge "✓ Подключено к серверу".
     - Displays red button `[Отключиться]`.
   - Click `[Отключиться]`.
   - In the confirmation prompt ("Отключить расширение от <сервер>?"), click "OK".
   - Verify the card transitions to "Расширение не подключено к серверу" and displays the pairing form.

3. **Verify Reconnect to LOCAL:**
   - In Chrome, open `https://localhost:8443/avito/extension` (with Owner client certificate).
   - Open the extension popup. Verify the Server URL field is automatically prefilled with `https://localhost:8443`.
   - In the web interface, click "Сгенерировать код" to get a fresh 6-digit code.
   - Enter the 6-digit code into the extension popup and click `[Подключить]`.
   - Verify the popup instantly updates to connected state showing `https://localhost:8443`.

4. **Verify Offline / Unavailable Indicator (Optional):**
   - If connected to a server that is unreachable or shut down, the popup preserves the saved server address and displays a yellow badge "✕ Сервер недоступен".
   - The `[Отключиться]` button remains fully functional to allow switching to a live server.

5. **Re-pair to Production (Optional):**
   - If Owner wishes to reconnect to production VDS:
     - Click `[Отключиться]`.
     - Enter Server URL: `https://144.31.15.88`.
     - Open `https://144.31.15.88/avito/extension` to generate a 6-digit code.
     - Enter the code and click `[Подключить]`.
     - Extension is now paired with production without reinstalling.
