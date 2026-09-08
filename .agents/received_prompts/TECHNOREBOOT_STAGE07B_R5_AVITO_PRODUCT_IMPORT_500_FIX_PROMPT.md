# TECHNOREBOOT — Stage 07B-R5
## Fix Avito Extension product import 422 / upstream Core HTTP 500 regression

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07B-R5 — Avito Product Import 500 Regression Fix`

---

# 0. EXECUTION CONTRACT

Stage 07B is still under Owner Check.

A second Avito regression was found manually after Stage 07B restore/auth work.

Current OWNER symptom in the Chrome extension:

```text
✕ Объявление получено, но импорт товара завершился ошибкой.
Ошибка сервера 422:
Не удалось импортировать объявление в Техноребут:
HTTP 500: Internal Server Error
```

Important observation:
- the extension successfully reads the Avito listing;
- the extension is paired and communicates with Technoreboot;
- failure occurs later, during import of the received listing into Technoreboot;
- the extension sees an outer HTTP 422, whose detail says an inner/upstream HTTP 500 occurred.

This is a regression/blocker in an already accepted Avito import workflow.

Goals of this stage ONLY:

1. Reproduce the real extension import failure end-to-end.
2. Find the exact current HTTP 500 root cause.
3. Fix the smallest broken layer.
4. Verify one real listing imports successfully again.
5. Preserve mTLS, backups, OWNER identity, pairing, and existing Avito behavior.

Do NOT redesign Avito.
Do NOT redesign product schema.
Do NOT start Internet deployment.
Do NOT change certificate architecture.
Do NOT bump Chrome extension version unless extension source itself must change.

First copy this exact prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07B_R5_AVITO_PRODUCT_IMPORT_500_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07B_R5_AVITO_PRODUCT_IMPORT_500_FIX_PROMPT.md`

Treat the copied prompt as authoritative.

---

# 1. ACCEPTED BASELINE

Current accepted/working baseline before this defect:

- Existing Stage 07A OWNER mTLS identity is preserved and works.
- `/certificates` works.
- `/backups` works.
- Normal web restore preserves current `data/auth`.
- Avito Chrome Extension current version is `0.2.43`.
- Pairing code generation was fixed in Stage 07B-R4.
- Pairing code -> extension token -> heartbeat works.
- Current R4 commit:
  `5d6e2ec717e1329c366ff2f4bf6c003fa8a362bf`

Do not regress any of these.

---

# 2. REPRODUCE THE REAL OWNER FAILURE

Do not start by changing code.

First reproduce the actual import path.

Use the current running stack and the same endpoint chain used by the extension.

Identify the complete current request flow, for example:

```text
Chrome Extension
    ->
Avito extension bridge endpoint
    ->
avito-module
    ->
Core API product import/create endpoint
    ->
DB / photo storage
```

The exact current route names must be discovered from code and logs.

Capture:

- outer request path;
- outer HTTP status (`422`);
- outer response JSON;
- inner/upstream request path;
- inner HTTP status (`500`);
- exact exception stack trace from the service that generated 500;
- relevant `avito-module` logs;
- relevant `core` logs;
- relevant `admin-shell/gateway` logs only if they participate in this flow.

Do not infer root cause from the frontend message alone.

---

# 3. DETERMINE WHETHER mTLS IS INVOLVED

The owner suspects recent certificate protection might have broken plugin work.

Explicitly prove or disprove this.

Check:

- Does extension traffic go through the mTLS browser gateway?
- Or does extension use its own extension token / bridge port?
- Is Core receiving the request before the 500?
- Is the failure authentication/authorization, routing, persistence, schema, DB, media storage, or another runtime exception?

Final report must clearly state:

```text
MTLS_CAUSED_THIS_FAILURE: true/false
```

with evidence.

Do NOT bypass mTLS or extension token security just to make import work.

---

# 4. INSPECT PERSISTENT MOUNTS AFTER RESTORE WORK

Because Stage 07B already caused one Docker Desktop bind-mount inode regression, explicitly inspect all writable paths touched during Avito import.

At minimum inspect inside relevant containers and on host:

- Core DB path;
- Core/product photo storage path;
- Avito module data path;
- any temp/import directory;
- any bind-mounted directory used during product/photo creation.

Verify they are actual accessible directories/files from inside the running containers.

Check for:
- dead/unlinked mount inode;
- `ENOENT`;
- `FileExistsError`;
- permission errors;
- read-only mount;
- missing directory;
- database locked/unavailable.

Do not assume the R4 fix automatically covered every writable mount.

---

# 5. INSPECT THE EXACT IMPORT PAYLOAD

Use one current Avito listing that reproduces the issue.

Capture the normalized payload sent from extension/avito-module to Core, redacting secrets/tokens.

Verify current fields against Core schema:

- title/name;
- price;
- description;
- category;
- brand;
- model;
- condition;
- address/city;
- source Avito ID/URL;
- characteristics;
- photos;
- any new/legacy fields.

Check whether the 500 is caused by:
- schema drift;
- unexpected/null field;
- duplicate uniqueness constraint;
- malformed photo URL;
- image download exception;
- category/characteristic mapping;
- DB constraint;
- serialization;
- filesystem write;
- another concrete exception.

Do NOT loosen validation blindly.

---

# 6. FIX THE ROOT CAUSE ONLY

Apply the minimum correct fix after proving the exception.

Examples of acceptable fixes depending on evidence:

- repair writable bind mount handling;
- fix path handling after restore;
- fix Core import exception handling;
- fix schema/mapping incompatibility;
- fix photo storage write;
- fix stale restored runtime state;
- fix duplicate/source-id handling;
- fix proxy/bridge error translation.

Do not add unrelated features.

---

# 7. ERROR CONTRACT HARDENING

The current outer response is:

```text
HTTP 422
Не удалось импортировать объявление в Техноребут: HTTP 500: Internal Server Error
```

Improve observability without leaking secrets.

Required:

1. The service that calls Core should preserve a safe structured error.
2. If Core returns non-JSON/plain-text 500, do not expose raw parser errors.
3. Extension/UI should receive a controlled error message.
4. Server logs must retain the real exception for diagnosis.
5. Do not expose stack traces, tokens, private keys, or passwords to the extension.

Do NOT mask real HTTP failures as success.

---

# 8. REAL END-TO-END IMPORT VERIFICATION

This is mandatory.

After the fix, perform a real import through the same path the Chrome extension uses.

Required sequence:

1. Existing extension token is valid or pair current extension.
2. Obtain one actual Avito listing through the extension flow.
3. Send/import it into Technoreboot.
4. Confirm request returns success.
5. Confirm a product record exists in Core/DB.
6. Confirm source Avito ID/URL is attached correctly.
7. Confirm title and price are correct.
8. Confirm description is present.
9. Confirm photos are imported if the listing contains photos.
10. Confirm characteristics are imported according to the current accepted capability of v0.2.43.
11. Confirm no duplicate unexpected product is created if the same import contract is retried according to current behavior.

Do not publish anything back to Avito.

---

# 9. PHOTO IMPORT CHECK

Photos have historically been important and worked in accepted Avito versions.

If listing has photos:

- verify Core downloads/stores them;
- verify files exist in current product photo storage;
- verify product card can serve/display them;
- verify restore changes did not break storage path.

If photo download is the actual 500 cause, fix it specifically and add regression coverage.

---

# 10. REQUIRED TESTS

## TEST A
Existing OWNER access still works:
- `/` -> 200
- `/certificates` -> 200
- `/backups` -> 200

## TEST B
Avito pairing remains working.

## TEST C
Extension heartbeat/status remains working.

## TEST D
Reproduce old import failure before fix and record exact 500 exception.

## TEST E
Direct Core import endpoint succeeds after fix with the reproduced payload.

## TEST F
Avito-module/bridge import endpoint succeeds after fix.

## TEST G
Real extension-equivalent end-to-end import succeeds.

## TEST H
Imported product exists in DB/Core.

## TEST I
Title/price/description/source Avito metadata correct.

## TEST J
Photos import and are readable if present.

## TEST K
Characteristics behavior matches current accepted extension capability.

## TEST L
Safe structured error handling works for simulated Core 500.

## TEST M
Relevant Core tests pass.

## TEST N
Relevant Avito module tests pass.

## TEST O
Relevant extension tests pass.

## TEST P
Relevant Admin Shell tests pass if Admin Shell code is touched.

## TEST Q
Backup/restore regression smoke:
normal `/backups` restore policy still preserves current auth and does not break writable bind mounts used by Avito/Core.

Report exact totals.

---

# 11. EXTENSION VERSION RULE

Current extension version is `0.2.43`.

If the defect is entirely server-side:
- do NOT change extension source;
- do NOT bump extension version;
- verify downloadable ZIP remains v0.2.43.

If extension source must change:
- bump version exactly once;
- rebuild/package;
- verify manifest/UI/downloaded ZIP all match;
- report new version and why it was necessary.

---

# 12. OWNER MANUAL CHECK

Final Owner Check must be browser/extension only.

Expected steps:

1. Open Technoreboot.
2. Open/download current Avito extension if needed.
3. Confirm extension is connected.
4. Open one Avito listing.
5. Trigger `Передать в Техноребут`.
6. Confirm success instead of:
   `Ошибка сервера 422 ... HTTP 500`.
7. Open Technoreboot and confirm imported product exists with correct main data/photos.

No terminal instructions for Owner.

---

# 13. PROJECT RECORDS

Preserve prompt:

`.agents\received_prompts\TECHNOREBOOT_STAGE07B_R5_AVITO_PRODUCT_IMPORT_500_FIX_PROMPT.md`

Create/update:

`docs\stage07b_r5_avito_product_import_500_fix.md`

`reports\stage07b_r5_avito_product_import_500_fix_report.md`

`logs\2026-09-08.md`

Document:
- exact reproduced failure;
- exact inner 500 exception;
- whether mTLS was involved;
- exact root cause;
- exact fix;
- real imported listing verification;
- extension version decision.

Do not include tokens/secrets.

---

# 14. GIT

Before commit:

- inspect diff;
- no runtime DB;
- no product owner data dumps;
- no backup ZIP;
- no auth secrets;
- no extension tokens;
- no pairing codes.

Then:

- commit;
- push `origin/main`;
- report commit hash;
- verify clean tracked worktree.

---

# 15. FINAL REPORT CONTRACT

Return:

```text
# Stage 07B-R5 — Avito Product Import 500 Regression Fix

## Owner Bug Reproduced
OUTER_STATUS:
OUTER_RESPONSE:
INNER_SERVICE:
INNER_PATH:
INNER_STATUS:
EXACT_EXCEPTION:

## Root Cause
PROVEN_ROOT_CAUSE:
MTLS_CAUSED_THIS_FAILURE:
RESTORE/BIND_MOUNT_RELATED:
SCHEMA_RELATED:
PHOTO_STORAGE_RELATED:

## Fix
FILES_CHANGED:
EXTENSION_CHANGED:
EXTENSION_VERSION:

## Real Import Verification
AVITO_LISTING_ID:
IMPORT_RESULT:
PRODUCT_ID:
TITLE_OK:
PRICE_OK:
DESCRIPTION_OK:
SOURCE_METADATA_OK:
PHOTOS_OK:
CHARACTERISTICS_OK:

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
TEST O:
TEST P:
TEST Q:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser/extension-only steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07B_R5_AVITO_PRODUCT_IMPORT_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If real extension-equivalent import still returns 422/500, return BLOCKED.

---

# 16. STOP

After diagnosis, fix, live verification, docs, commit/push and report:

STOP.

Do not start Internet deployment.
Do not start a new Avito feature stage.
Wait for owner acceptance.
