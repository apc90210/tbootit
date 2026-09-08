# TECHNOREBOOT — Stage 07B-R5-R1
## Remove unsafe temporary photo fallback and enforce persistent Avito photo storage

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07B-R5-R1 — Persistent Photo Storage Safety Fix`

---

# 0. EXECUTION CONTRACT

Stage 07B-R5 fixed the real Avito import regression caused by a broken Docker bind mount.

However, the R5 implementation introduced a new data-integrity risk:

- `core/app/routers/integrations.py` may fall back from persistent
  `/data/storage/product_photos`
  to temporary
  `/tmp/product_photos`;
- on photo write failure it may keep only `media_url=source_url`.

This is NOT acceptable as the normal persistence contract for Technoreboot.

A product import must not silently report durable photo success when photos were only stored in container `/tmp` or only referenced from an external Avito URL.

This corrective stage must keep the R5 bind-mount fix but remove unsafe persistence fallback behavior.

Do NOT redesign Avito.
Do NOT change mTLS.
Do NOT change backup UI.
Do NOT start Internet deployment.
Do NOT bump extension version unless extension source changes.

First copy this prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07B_R5_R1_PERSISTENT_PHOTO_STORAGE_SAFETY_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07B_R5_R1_PERSISTENT_PHOTO_STORAGE_SAFETY_FIX_PROMPT.md`

---

# 1. REQUIRED STORAGE CONTRACT

Canonical persistent product-photo storage remains:

`/data/storage/product_photos`

backed by host persistent storage.

Requirements:

1. Never use `/tmp/product_photos` as a successful persistence fallback.
2. Never report a photo as locally persisted unless the file really exists in persistent storage.
3. Do not depend on an Avito remote URL as the only durable copy when the import contract says the photo was imported.
4. Backup must continue to include all successfully imported local photos.

---

# 2. FAILURE BEHAVIOR

If persistent photo storage is unavailable:

Preferred behavior:

- Product import may still succeed if the existing product-import contract allows partial photo failure.
- The response must explicitly include a safe warning that photos were not persisted.
- Photo DB rows must accurately reflect reality.
- Do NOT create a fake/local `storage_path`.
- Do NOT store files in `/tmp` and treat them as success.

If the current contract requires all photos to persist atomically, return a structured server error such as `503 STORAGE_UNAVAILABLE`.

Choose the behavior consistent with the existing accepted import semantics, but do not silently degrade.

---

# 3. STARTUP / HEALTH

Core should validate its persistent storage path on startup or before photo import.

At minimum:
- ensure `/data/storage/product_photos` exists or can be created;
- verify it is a real accessible directory;
- verify a safe write/delete probe if appropriate;
- log a clear server-side diagnostic when unavailable.

Do not expose filesystem internals or stack traces to the extension.

---

# 4. KEEP THE REAL R5 FIX

Preserve the actual regression fix:

- restore logic must synchronize bind-mounted directories in place;
- it must not delete/recreate bind-mount root directories;
- current OWNER/CA/auth preservation remains intact;
- Avito pairing remains intact;
- Avito product import remains intact.

Do not revert those fixes.

---

# 5. REQUIRED TESTS

## TEST A
Normal persistent storage available:
- Avito import succeeds;
- photos are physically saved under persistent `/data/storage/product_photos`;
- files survive Core container restart;
- files are served via `/media/...`.

## TEST B
Simulated persistent storage unavailable:
- no `/tmp/product_photos` success fallback;
- no false local `storage_path`;
- response is either explicit partial-success warning or structured failure according to existing contract;
- no raw HTTP 500/plain stack trace.

## TEST C
Backup created after successful photo import contains the imported photo.

## TEST D
Web restore preserves valid storage mount inode and imported photos remain available.

## TEST E
Real extension-equivalent Avito import still succeeds with photos.

## TEST F
Existing OWNER:
- `/` 200
- `/certificates` 200
- `/backups` 200

## TEST G
Avito pairing/heartbeat still pass.

## TEST H
Relevant Core tests pass.

## TEST I
Relevant Avito module tests pass.

Report exact totals.

---

# 6. OWNER MANUAL CHECK

Browser/extension only:

1. Open one Avito listing containing photos.
2. Press `Передать в Техноребут`.
3. Confirm import succeeds.
4. Open imported product in Technoreboot.
5. Confirm photos display.
6. Refresh/reopen the product and confirm photos still display.

No CMD/terminal instructions for Owner.

---

# 7. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07B_R5_R1_PERSISTENT_PHOTO_STORAGE_SAFETY_FIX_PROMPT.md`

Create/update:

`docs\stage07b_r5_r1_persistent_photo_storage_safety_fix.md`

`reports\stage07b_r5_r1_persistent_photo_storage_safety_fix_report.md`

`logs\2026-09-08.md`

---

# 8. GIT / SECRET SAFETY

Before commit:
- no runtime DB;
- no backup ZIP;
- no actual product photos;
- no auth secrets;
- no extension tokens;
- no pairing codes.

Commit and push to `origin/main`.

---

# 9. FINAL REPORT CONTRACT

Return:

```text
# Stage 07B-R5-R1 — Persistent Photo Storage Safety Fix

## Unsafe Behavior Removed
TMP_PHOTO_FALLBACK_REMOVED:
REMOTE_URL_ONLY_REPORTED_AS_LOCAL_SUCCESS:
PERSISTENT_STORAGE_REQUIRED_FOR_LOCAL_PHOTO_SUCCESS:

## Failure Contract
STORAGE_UNAVAILABLE_BEHAVIOR:
STRUCTURED_ERROR_OR_WARNING:

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

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser/extension-only steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07B_R5_R1_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If persistent storage unavailability can still be silently treated as successful photo persistence, return BLOCKED.

---

# 10. STOP

After fix, tests, docs, commit/push and report:

STOP.

Do not start Internet deployment.
Wait for owner acceptance.
