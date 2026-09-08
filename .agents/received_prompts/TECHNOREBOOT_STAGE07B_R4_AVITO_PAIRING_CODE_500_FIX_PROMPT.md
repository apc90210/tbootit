# TECHNOREBOOT — Stage 07B-R4
## Fix Avito Extension Pairing Code 500 / Unexpected token I regression

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07B-R4 — Avito Pairing Code 500 Regression Fix`

---

# 0. EXECUTION CONTRACT

Stage 07B is still under Owner Check.

A new regression was found manually after the recent mTLS / backup / restore work.

OWNER symptom:

1. Open Technoreboot through the current mTLS gateway.
2. Open the Avito Extension page.
3. Download the current extension ZIP successfully.
4. Click the button to generate/create a new 6-digit pairing code.
5. UI fails with:

`Ошибка генерации кода: Unexpected token 'I', "Internal S"... is not valid JSON`

This is a BLOCKER because Avito extension pairing is part of the already accepted project baseline and must continue to work after Stage 07A/07B changes.

Do NOT redesign Avito.
Do NOT change extension publication logic.
Do NOT change certificate architecture.
Do NOT start Internet deployment.
Do NOT change business data.
Do NOT bump extension version unless a real extension-file change is required.

First copy this exact prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07B_R4_AVITO_PAIRING_CODE_500_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07B_R4_AVITO_PAIRING_CODE_500_FIX_PROMPT.md`

Treat the copied prompt as authoritative.

---

# 1. IMPORTANT HISTORICAL CONTEXT

This exact JavaScript symptom has happened before in the project:

`Unexpected token 'I' ... "Internal Server Error" ... is not valid JSON`

Historical Stage 06A-R8-R8-R3 proved that this means the frontend called `response.json()` while the backend/proxy actually returned plain-text HTTP 500 `Internal Server Error`.

Historical fixes included:
- fixing the backend/proxy root cause;
- making frontend error handling robust to non-JSON responses.

Do NOT assume the old root cause is the current root cause.

Pairing code generation should be fast, so diagnose the CURRENT 500 empirically.

Relevant accepted Avito pairing architecture historically includes:
- Admin Shell Avito extension page;
- pairing code generation button;
- Admin Shell proxy;
- Avito module endpoint:
  `POST /extension/api/pairing/generate`
- response containing a 6-digit `pair_code`;
- pairing endpoint:
  `POST /extension/api/pairing/pair`.

Current implementation may have evolved; inspect actual current code.

---

# 2. BASELINE / PREFLIGHT

Before changing code:

1. Record:
   - `git status --short`
   - current branch
   - current HEAD
   - `docker compose ps`

2. Confirm current accepted mTLS OWNER access works.

3. Determine current installed/downloadable extension version from:
   - source manifest;
   - downloadable ZIP;
   - Admin Shell UI.

4. Do not downgrade or replace the accepted extension package accidentally.

5. Read current:
   - `admin-shell/app/main.py`
   - `admin-shell/app/templates/avito_extension.html`
   - relevant Admin Shell Avito proxy tests
   - `avito-module/app/routers/extension_bridge.py`
   - Avito pairing tests
   - current gateway/Nginx config
   - current Docker networking/config for `admin-shell` and `avito-module`.

---

# 3. REPRODUCE THE OWNER BUG THROUGH THE REAL PATH

Do NOT test only the Avito module directly.

Reproduce the actual OWNER path through:

`https://127.0.0.1:8443`

using the existing accepted OWNER certificate.

Identify the exact browser/API endpoint used when the owner presses:

`Создать код подключения`
or
`Создать новый код подключения`

Capture and record:

- request URL;
- HTTP method;
- response status;
- response content-type;
- response body safely;
- relevant `admin-shell` log;
- relevant `avito-module` log;
- relevant `gateway` log.

Also test the direct internal Avito endpoint separately to isolate where the failure occurs:

`POST /extension/api/pairing/generate`

Expected successful JSON shape must be confirmed from current code/tests, typically containing:

`pair_code`

Do not expose actual generated pairing codes in final report unless necessary; redact if practical.

---

# 4. ROOT CAUSE MUST BE PROVEN

Determine whether the 500 is caused by any of the following, or something else:

- Admin Shell proxy target/path regression;
- gateway route/header regression after mTLS;
- proxy exception / connection failure;
- Avito module not reachable from Admin Shell;
- malformed restored `data/avito-module` state;
- pairing token/pairing-code storage format regression after backup/restore;
- file permission/path problem;
- stale runtime state;
- timeout;
- exception in pairing code generation;
- non-JSON upstream error being blindly parsed by UI.

Do not guess.

Final report must include the exact exception/root cause.

---

# 5. REQUIRED FIX

Fix the actual root cause with the smallest possible change.

The accepted behavior must be:

OWNER opens Avito extension management page through mTLS gateway.

Clicks:

`Создать код подключения`

Result:

- HTTP success;
- valid JSON from backend/proxy;
- exactly one 6-digit pairing code appears in UI;
- no JavaScript `Unexpected token` error.

Then the code must be usable by the current downloadable Chrome extension.

Do not alter unrelated Avito logic.

---

# 6. ROBUST FRONTEND ERROR HANDLING — REQUIRED

Regardless of backend root cause, harden the pairing-code generation UI so this class of error never appears as a raw JavaScript parsing exception again.

Do NOT blindly call `response.json()` on an unknown/error response.

Required behavior:

1. Inspect HTTP status/content-type.
2. If JSON:
   - parse JSON safely.
3. If non-JSON:
   - read text safely.
4. On failure display a controlled Russian message such as:

`Не удалось создать код подключения: сервер вернул ошибку 500.`

Optionally append a short safe backend message if available.

Never show:
- `Unexpected token 'I'`
- raw stack trace
- HTML error page
- secrets.

The backend should also prefer structured JSON error responses for the Admin Shell proxy where practical.

---

# 7. DO NOT BREAK mTLS / OWNER SECURITY

The fix must preserve:

- mTLS gateway;
- OWNER certificate access;
- USER restrictions;
- `/certificates`;
- `/backups`;
- normal restore preserving current auth.

Do not bypass authentication just to make the Avito endpoint work.

The Avito management page remains accessed through the normal authenticated Technoreboot owner UI.

---

# 8. DO NOT BREAK THE EXTENSION BRIDGE

After fixing code generation, validate the full minimal pairing handshake.

Required real/runtime sequence:

1. Generate 6-digit pairing code from Technoreboot UI/API through gateway.
2. Call/use current pairing endpoint with that code.
3. Receive a valid extension token.
4. Check status/heartbeat with that token.
5. Confirm paired state is valid.
6. Confirm code is single-use / expiry behavior remains according to current contract.

Do not perform actual Avito publication.
Do not mutate product listings as part of this regression test.

---

# 9. DOWNLOAD PACKAGE CHECK

Because Owner manually downloaded the extension before finding this bug, verify that the current download endpoint still serves the intended current package.

Check:

- response 200;
- valid ZIP;
- manifest version matches current source/current accepted version;
- no stale downgrade;
- required extension files present.

Do not bump version if no extension code changes.

If frontend/service-worker extension code must be changed, then follow the established version bump/build/package/hash consistency workflow and explicitly report it.

---

# 10. REQUIRED TESTS

At minimum:

## TEST A
OWNER can open current Avito extension page through mTLS gateway.

## TEST B
Current extension ZIP downloads successfully.

## TEST C
Direct Avito-module `POST /extension/api/pairing/generate` returns valid JSON and a 6-digit code.

## TEST D
Admin Shell proxy pairing-generate endpoint returns valid JSON through internal proxy path.

## TEST E
Real OWNER gateway path for pairing-generate returns success JSON.

## TEST F
UI JavaScript handles successful JSON correctly.

## TEST G
UI JavaScript handles simulated/plain-text 500 without throwing `Unexpected token`.

Expected controlled Russian error.

## TEST H
Generated pairing code can be exchanged for extension token.

## TEST I
Heartbeat/status with paired token succeeds.

## TEST J
Pairing code single-use/expiry contract remains intact.

## TEST K
Current Avito module tests pass.

## TEST L
Current Admin Shell tests pass.

## TEST M
Relevant Chrome extension tests pass.

## TEST N
mTLS regression smoke:
- OWNER `/` 200
- OWNER `/certificates` 200
- OWNER `/backups` 200

Report exact commands and exact totals.

---

# 11. OWNER LIVE CHECK

Before declaring READY, perform browser-equivalent end-to-end validation through:

`https://127.0.0.1:8443`

with the EXISTING accepted OWNER identity.

The final manual Owner Check must be simple:

1. Open Technoreboot.
2. Open Avito extension page.
3. Click `Создать код подключения`.
4. Confirm a 6-digit code appears.
5. Open installed/downloaded extension.
6. Enter the code.
7. Confirm extension shows connected/paired.

No terminal instructions for Owner.

---

# 12. PROJECT RECORDS

Preserve prompt:

`.agents\received_prompts\TECHNOREBOOT_STAGE07B_R4_AVITO_PAIRING_CODE_500_FIX_PROMPT.md`

Create/update:

`docs\stage07b_r4_avito_pairing_code_500_fix.md`

`reports\stage07b_r4_avito_pairing_code_500_fix_report.md`

`logs\2026-09-08.md`

Document:
- exact reproduced 500;
- exact root cause;
- exact fix;
- exact pairing verification;
- exact extension version/package verification.

Do not include secrets or actual extension tokens.

---

# 13. GIT

Before commit:
- inspect diff;
- no runtime auth secrets;
- no backup ZIP;
- no production DB data;
- no pairing tokens;
- no private certs.

Then:
- commit;
- push `origin/main`;
- report commit hash;
- verify clean tracked worktree.

---

# 14. FINAL REPORT CONTRACT

Return:

```text
# Stage 07B-R4 — Avito Pairing Code 500 Regression Fix

## Owner Bug Reproduced
OWNER_ERROR:
REQUEST_PATH:
HTTP_STATUS:
CONTENT_TYPE:
SAFE_RESPONSE_BODY:

## Root Cause
PROVEN_ROOT_CAUSE:
EXACT_EXCEPTION:
REGRESSION_INTRODUCED_BY:

## Fix
BACKEND_FIXED:
PROXY_FIXED:
FRONTEND_NON_JSON_HANDLING_FIXED:
EXTENSION_CHANGED:
EXTENSION_VERSION:

## Runtime Verification
TEST A:
TEST B:
TEST C:
TEST D:
TEST E:
TEST F:
TEST G:
TEST H:
TEST I:
TEST J:
TEST K:
TEST L:
TEST M:
TEST N:

## Exact Test Results

## Files Changed

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07B_R4_AVITO_PAIRING_CODE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If pairing generation through the real OWNER gateway path still fails, return BLOCKED.

---

# 15. STOP

After fix, tests, docs, commit/push and report:

STOP.

Do not start Internet deployment.
Do not start a new Avito stage.
Wait for owner acceptance.
