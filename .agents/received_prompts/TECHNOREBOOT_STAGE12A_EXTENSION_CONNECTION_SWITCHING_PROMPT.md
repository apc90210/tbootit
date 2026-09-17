# TECHNOREBOOT — Stage 12A LOCAL
## Avito Extension: show current TechnoReboot server + disconnect/reconnect/switch server

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`  
**Environment:** LOCAL FIRST  
**Canonical production VDS:** `144.31.15.88` — DO NOT DEPLOY IN THIS STAGE

# 0. OWNER GOAL

Improve the TechnoReboot Avito browser extension so the operator always understands which TechnoReboot instance the extension is paired with and can easily disconnect and pair it with another server.

Required user-facing behavior:

1. The extension popup must clearly show the currently connected TechnoReboot address, at minimum:
   ```text
   Подключено к:
   https://144.31.15.88
   ```
   or:
   ```text
   https://localhost:8443
   ```

2. There must be an explicit action:
   ```text
   [Отключиться]
   ```

3. After disconnecting, the extension must be able to pair again with another TechnoReboot instance without reinstalling/resetting the browser extension.

4. Pairing to another server must replace the active connection cleanly and must not reuse stale credentials/token from the previous server.

This stage is LOCAL-only. Do not deploy to production until Owner browser acceptance.

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE12A_EXTENSION_CONNECTION_SWITCHING_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE12A_EXTENSION_CONNECTION_SWITCHING_PROMPT.md`

# 2. PREFLIGHT

Before coding:

```text
git status
git branch --show-current
git rev-parse HEAD
docker compose ps
```

Inspect current extension implementation:

```text
chrome-extension/technoreboot-avito/
```

At minimum inspect:
- `manifest.json`;
- popup HTML/CSS/JS;
- service worker/background worker;
- pairing state storage;
- current active-tab server auto-detection;
- current 6-digit pairing flow;
- server URL normalization;
- existing host permissions;
- extension build script;
- `/avito/extension` server-side pairing page/API.

Do not change unrelated Avito import/reverse-publication behavior.

# 3. SINGLE ACTIVE CONNECTION MODEL

For this stage, keep the extension simple:

```text
ONE extension = ONE active TechnoReboot connection at a time
```

Do not implement a multi-server account list.

Store one canonical active connection record, conceptually:

```json
{
  "origin": "https://144.31.15.88",
  "paired": true,
  "paired_at": "...",
  "server_label": null
}
```

Use current storage architecture/naming conventions rather than inventing duplicate state.

The server origin must be normalized:
- remove trailing `/`;
- preserve explicit non-default port;
- reject malformed URLs;
- accept only `http://` or `https://`;
- prefer HTTPS in normal use.

# 4. POPUP — CURRENT CONNECTION CARD

At the top of the popup add a compact connection/status block.

When paired:

```text
ТехноРебут
Подключено к:
https://144.31.15.88

Статус: Подключено
[Отключиться]
```

When the stored server is temporarily unreachable:

```text
Подключено к:
https://144.31.15.88

Статус: Сервер недоступен
[Отключиться]
```

Important:
"server unreachable" is NOT the same as "not paired".

When not paired:

```text
ТехноРебут не подключён
[Подключить]
```

Do not hide the saved address merely because the server is offline.

# 5. OPTIONAL SERVER LABEL

If an existing safe API already exposes a server/environment label, instance name, or hostname, it may be shown as secondary text.

Example:

```text
ТехноРебут — Production
https://144.31.15.88
```

But this is optional.

The address/origin is mandatory and is the source of truth for the popup display.

Do NOT add a new complicated server identity subsystem only for this UI.

# 6. DISCONNECT / UNPAIR

Add:

```text
[Отключиться]
```

Behavior:

1. Ask for a lightweight confirmation:
   ```text
   Отключить расширение от https://144.31.15.88?
   ```
2. On confirmation:
   - clear active pairing token/credentials used by the extension;
   - clear active server origin;
   - clear cached pairing/session state tied to that server;
   - cancel/reject any in-flight extension request cleanly where practical;
   - popup moves to unpaired state immediately.

Do NOT:
- modify server business data;
- delete Avito listings;
- revoke OWNER/USER mTLS browser certificates;
- delete browser-wide certificates;
- delete extension package/config unrelated to pairing;
- delete server-side products/import history.

If the server has an existing safe pairing-revoke endpoint, use it.
If no such endpoint exists, local unpairing is sufficient for Stage12A.

Document which behavior is used.

# 7. RECONNECT / PAIR WITH ANOTHER SERVER

After disconnecting, show pairing UI directly in the popup.

Required fields/actions:

```text
Адрес ТехноРебут:
[ https://... ]

Код подключения:
[ 123456 ]

[Подключить]
```

The address field must support:
- `https://localhost:8443`
- `https://144.31.15.88`
- another valid TechnoReboot HTTP/HTTPS origin, subject to browser extension permissions.

Preserve the current 6-digit pairing workflow.

Do not require extension reinstall.

# 8. ACTIVE-TAB AUTO-DETECTION

Preserve the current convenience behavior:

If the active browser tab is clearly a TechnoReboot page, the extension may prefill the address from the active tab origin.

Example:

Active tab:
```text
https://localhost:8443/avito/extension
```

Prefill:
```text
https://localhost:8443
```

Active tab:
```text
https://144.31.15.88/avito/extension
```

Prefill:
```text
https://144.31.15.88
```

But:
- do not silently overwrite an already paired active server;
- only use auto-detection as a suggestion/prefill while unpaired or explicitly reconnecting.

# 9. SERVER PERMISSIONS / MV3

Audit current Manifest V3 host permissions.

Goal:
The user must be able to reconnect to another TechnoReboot server without rebuilding the extension merely because the host changed.

Prefer the narrowest practical implementation.

Options, in order of preference:

1. Existing permissions already safely cover the required TechnoReboot endpoints.
2. `optional_host_permissions` + runtime `chrome.permissions.request()` for the exact target origin.
3. A broader permission only if technically necessary and clearly justified.

Do not silently request `<all_urls>` unless there is no practical narrower solution.

When pairing to a new host:
- request origin permission if required;
- if denied, show a clear popup error;
- do not save pairing as successful.

If permission for old host is optional/runtime-granted, removing it during disconnect is optional; do not break browser behavior merely to clean it up.

# 10. ONE SOURCE OF TRUTH FOR SERVER URL

Search extension code for:
- hard-coded `localhost`;
- `144.31.15.88`;
- legacy `144.31.50.134`;
- duplicated `baseUrl`, `serverUrl`, `apiUrl`, etc.

Refactor so all extension API operations use the active stored canonical connection origin.

This includes, as applicable:
- pair;
- pairing status;
- listing import;
- profile import;
- reverse browser-assisted flow;
- health/status checks;
- any extension-side API request.

Do not let one code path accidentally keep using the old server after switching.

Legacy VDS `144.31.50.134` must not remain an active default.

Historical docs/tests may keep it as historical evidence.

# 11. CONNECTION STATE MACHINE

Keep a simple explicit state machine:

```text
UNPAIRED
PAIRING
PAIRED
PAIRED_SERVER_UNREACHABLE
PAIRING_ERROR
```

Avoid ambiguous combinations such as:
- token exists but no server;
- server exists but token belongs to old server;
- UI says paired while service worker uses another origin.

On any pairing success:
- atomically persist the new server + token/connection state together.

On failure:
- do not partially switch.

# 12. SWITCH SERVER UX

The normal switch workflow should be:

```text
Current:
https://144.31.15.88

[Отключиться]
        ↓
Unpaired
        ↓
enter/prefill https://localhost:8443
enter 6-digit code
        ↓
[Подключить]
        ↓
Current:
https://localhost:8443
```

No browser restart and no extension reinstall.

# 13. SECURITY

Never show:
- pairing token;
- secret token;
- passwords;
- private keys.

Showing the TechnoReboot origin/address is allowed.

Do not log secrets to console.

Pairing token from old server must not be reused against new server.

If pairing credentials are keyed by server today, ensure switching does not accidentally select stale credentials.

# 14. SERVER-SIDE CHANGES

Prefer no server-side schema change.

If current pairing API is tied to assumptions about one hard-coded server, make only minimal API changes required for reconnect/unpair.

No DB migration unless absolutely necessary.

Do not change:
- sales;
- repairs;
- inventory;
- Avito business data;
- automatic Avito deactivation policy.

# 15. TESTS

Add automated extension tests or equivalent script-level tests for at least:

1. Paired state displays current server origin.
2. Offline paired server still displays saved origin + "server unavailable".
3. Disconnect clears active connection state.
4. Disconnect does not touch browser mTLS certificate.
5. Reconnect to same server works.
6. Switch LOCAL -> production works.
7. Switch production -> LOCAL works.
8. Pairing failure does not partially replace existing state.
9. Old server token is not used on new server.
10. Active-tab origin prefills only when appropriate.
11. URL normalization removes trailing slash and preserves port.
12. Invalid URL rejected.
13. Runtime host permission denial produces clear error.
14. All extension API requests use active connection origin.
15. Legacy `144.31.50.134` is not an active default/fallback.
16. Existing import/pairing regression tests remain green.

Run official project test suite relevant to extension/server integration.

# 16. BUILD

Rebuild the extension ZIP using the canonical build script.

Verify:
- manifest valid;
- ZIP version updated if project convention requires it;
- popup files included;
- service worker syntax valid;
- no CSP violation;
- no secret files.

If version is incremented, use the next appropriate patch version and report it.

# 17. LOCAL OWNER BROWSER ACCEPTANCE

Leave LOCAL TechnoReboot available at:

```text
https://localhost:8443
```

Provide Owner with this browser-only acceptance flow:

1. Open extension popup.
2. Confirm it shows the currently connected TechnoReboot address.
3. Click `Отключиться`.
4. Confirm popup becomes unpaired.
5. Open LOCAL TechnoReboot `/avito/extension`.
6. Use active-tab prefill or enter:
   `https://localhost:8443`
7. Enter a new 6-digit pairing code.
8. Click `Подключить`.
9. Confirm popup now shows:
   `https://localhost:8443`
10. Disconnect again.
11. Pair back to:
   `https://144.31.15.88`
   only if Owner explicitly wants to test production pairing; otherwise stop after LOCAL acceptance.

No CMD/PowerShell for Owner.

# 18. PRODUCTION

Do NOT deploy this extension/server change to production in Stage12A.

Do NOT modify production database.

Do NOT touch legacy VDS.

After Owner accepts LOCAL behavior, prepare a separate deployment stage.

# 19. DOCUMENTATION

Create:

```text
reports/stage12a_extension_connection_switching_report.md
```

Update:

```text
docs/production_status.md
logs/<current-date>.md
```

Document:
- connection state storage;
- disconnect semantics;
- host permission strategy;
- server URL source of truth;
- tests/build result.

# 20. GIT

Commit tracked code/tests/docs only.

Never commit:
- pairing secrets;
- tokens;
- DB;
- media;
- private keys;
- local browser profile data.

Push main after tests pass.

# 21. FINAL REPORT CONTRACT

Return:

```text
# Stage 12A — Extension Connection Switching

## UI
CURRENT_SERVER_ADDRESS_VISIBLE:
PAIRED_STATUS_VISIBLE:
UNREACHABLE_STATUS_VISIBLE:
DISCONNECT_BUTTON:
RECONNECT_FORM:
ACTIVE_TAB_PREFILL:

## State
SINGLE_ACTIVE_CONNECTION:
SERVER_URL_SOURCE_OF_TRUTH:
OLD_TOKEN_CLEARED_ON_DISCONNECT:
ATOMIC_SWITCH:
STALE_SERVER_STATE_PREVENTED:

## Permissions
MV3_PERMISSION_STRATEGY:
RUNTIME_ORIGIN_PERMISSION:
PERMISSION_DENIAL_HANDLED:

## Server Switching
LOCAL_TO_PROD:
PROD_TO_LOCAL:
NO_REINSTALL_REQUIRED:
LEGACY_VDS_NOT_DEFAULT:

## Security
TOKENS_HIDDEN:
SECRETS_NOT_LOGGED:
MTLS_CERT_NOT_REMOVED_BY_DISCONNECT:

## Regression
PAIRING_STILL_WORKS:
SINGLE_IMPORT_STILL_WORKS:
PROFILE_IMPORT_STILL_WORKS:
REVERSE_FLOW_STILL_WORKS:
AUTO_AVITO_DEACTIVATION_STILL_DISABLED:

## Build / Tests
EXTENSION_VERSION:
EXTENSION_ZIP:
EXTENSION_ZIP_SHA256:
AUTOMATED_TESTS:
LOCAL_SMOKE:

## Production
PRODUCTION_TOUCHED: false
PRODUCTION_DB_CHANGED: false
DEPLOYED_TO_144_31_15_88: false

FINAL_STATUS:
TECHNOREBOOT_STAGE12A_LOCAL_READY_FOR_OWNER_ACCEPTANCE
```

# 22. STOP

STOP after LOCAL implementation + tests + extension build + LOCAL smoke.

Do NOT deploy to production.
Wait for Owner browser acceptance.
