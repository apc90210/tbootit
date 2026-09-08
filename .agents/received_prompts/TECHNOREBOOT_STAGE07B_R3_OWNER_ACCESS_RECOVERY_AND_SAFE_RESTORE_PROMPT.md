# TECHNOREBOOT — Stage 07B-R3
## Recover existing OWNER access + make Web Restore preserve current auth

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07B-R3 — OWNER Access Recovery and Safe Web Restore`

---

# 0. EXECUTION CONTRACT

Stage 07B-R2 is NOT accepted.

Owner manual check found a critical regression:

- Browser reaches the mTLS certificate chooser.
- Owner selects the already-installed existing `Technoreboot OWNER` certificate.
- The server then returns access denied / 403.
- This OWNER certificate worked before Stage 07B backup/restore work.

This stage has TWO goals only:

1. Recover access for the EXISTING accepted OWNER certificate.
2. Prevent normal Web Restore from overwriting current certificate/auth state again.

Do NOT create a new CA.
Do NOT create a new OWNER identity.
Do NOT ask owner to re-import/reissue certificates unless the existing certificate is proven physically unusable.
Do NOT start Internet deployment.
Do NOT add new auth features.

First copy this exact downloaded prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07B_R3_OWNER_ACCESS_RECOVERY_AND_SAFE_RESTORE_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07B_R3_OWNER_ACCESS_RECOVERY_AND_SAFE_RESTORE_PROMPT.md`

Treat it as authoritative.

---

# 1. ACCEPTED OWNER IDENTITY

The accepted Stage 07A OWNER identity was finalized before backup work.

Known accepted values from project records:

- OWNER serial:
  `CDC5645E6C3FC238CE21EA41195DFC0277F9D7F`

- OWNER SHA-256 fingerprint:
  `022C0AA7804CE8982F66070DEC04E738765EE76453D1C059317CEFA25E26598D`

- accepted Stage07A-R2 commit:
  `17cce6ddaa3176e0ffb37558aef4ede1d982ef37`

Use repository/project records to independently verify these values before changing anything.

The goal is to make THIS SAME OWNER identity work again.

---

# 2. FIRST — DIAGNOSE CURRENT 403 WITHOUT REGENERATING ANYTHING

Before modifications:

1. Record:
   - git status
   - current HEAD
   - docker compose ps

2. Inspect current live:
   - `data/auth/ca/ca.crt`
   - `data/auth/certificates/owner.crt`
   - `data/auth/registry.json`
   - gateway mounted CA
   - admin-shell AuthManager state
   - `/internal-auth/verify` request handling
   - Nginx auth headers
   - current Stage07B-R2 restore behavior.

3. Compare current OWNER certificate:
   - serial
   - SHA-256 fingerprint
   - issuer
   - public key / private key match
   against accepted Stage07A values.

4. Compare current CA fingerprint against project records.

5. Confirm whether the failure is:
   - TLS certificate rejection;
   - registry lookup failure;
   - OWNER flag/role loss;
   - serial/fingerprint formatting mismatch;
   - stale in-memory AuthManager state;
   - stale gateway state;
   - header mapping/order regression;
   - auth registry overwritten by restore;
   - another proven cause.

Do not guess.
Record exact root cause.

---

# 3. IMMEDIATE OWNER RECOVERY

Restore access for the EXISTING accepted OWNER certificate.

Requirements:

- same OWNER serial;
- same OWNER SHA-256 fingerprint;
- same OWNER key;
- same CA;
- no new OWNER;
- no new CA.

If current `registry.json` lost/corrupted the OWNER entry, reconstruct/fix ONLY the registry entry from the existing accepted OWNER certificate and existing CA.

If code/header verification is wrong, fix the code instead.

If services hold stale auth state, implement the minimal safe reload/reinitialization needed.

After correction, browser-equivalent request through real gateway with the accepted existing OWNER certificate must return:

- `/` -> 200
- `/certificates` -> 200
- `/backups` -> 200

No certificate reissue.

---

# 4. CORRECT RESTORE POLICY

The owner clarified the purpose of backup:

PRIMARY:
- database/business data;
- product photos/media;
- other mutable business state.

Auth state is included in the backup for disaster recovery, BUT normal in-place web restore must NOT silently roll back/replace the currently working certificate system.

Therefore change Web Restore behavior:

## Normal Web Restore from `/backups`

Restore:
- database;
- storage/media;
- Avito mutable persistent state;
- other mutable business data.

PRESERVE CURRENT LIVE:
- `data/auth/`
- current CA
- current OWNER
- current USER certificate registry
- current revoke state
- current server auth secrets.

In other words:

`/backups` normal restore must NOT overwrite `data/auth`.

This prevents:
- current OWNER becoming invalid;
- USER certs issued after a backup disappearing;
- revoke state unexpectedly rolling backward.

## Backup ZIP

The ZIP SHOULD STILL INCLUDE `auth/` as an emergency/disaster-recovery component.

Do not remove auth from the archive.

Reason:
if the entire server is destroyed, auth data may be needed to rebuild the same identity.

But normal online restore must preserve currently running auth.

Document this distinction clearly.

Do NOT build the full fresh-server disaster bootstrap in this stage.
That will be handled during Internet deployment/recovery bootstrap later.

---

# 5. UI TEXT

On `/backups`, update restore explanation so it clearly says in Russian:

- Restore replaces business data from the selected backup.
- Current access certificates are preserved during normal online restore.

For example:

`Восстановление заменит базу данных и изменяемые данные системы состоянием из резервной копии. Текущие сертификаты доступа при обычном онлайн-восстановлении сохраняются.`

Keep UI simple.

---

# 6. REQUIRED TESTS

## TEST A — Existing OWNER identity
Current live OWNER serial/fingerprint exactly match accepted Stage07A values.

## TEST B — Existing OWNER access
Through real gateway:
- `/` -> 200
- `/certificates` -> 200
- `/backups` -> 200

## TEST C — No new identity
CA unchanged.
OWNER unchanged.
No second OWNER generated.

## TEST D — Create backup
Web backup still downloads valid ZIP.

## TEST E — Backup still includes auth
ZIP contains emergency `auth/` component.

## TEST F — Normal restore preserves live auth
1. Create web backup.
2. Record current live auth hashes/registry.
3. AFTER backup, issue a disposable USER cert (or otherwise make a safe disposable auth registry change).
4. Perform normal web restore from the older backup.
5. Verify that the post-backup auth change is STILL PRESENT because live auth is preserved.

This is the critical regression test.

## TEST G — Business data restores
Make a disposable post-backup database change.
Perform web restore.
Verify DB rolls back to backup state.

## TEST H — Media restores
Make disposable post-backup media change.
Perform web restore.
Verify media rolls back.

## TEST I — OWNER remains working immediately after restore
Without reissuing/reimporting OWNER:
- `/` -> 200
- `/certificates` -> 200
- `/backups` -> 200

## TEST J — Existing USER/revoked states preserved
Normal restore does not roll back current certificate registry.

## TEST K — USER denied from owner pages
Normal USER -> 403 `/certificates` and `/backups`.

## TEST L — Invalid archive rejected
No live data touched.

## TEST M — relevant admin-shell tests
Run exact suite and report exact totals.

---

# 7. IMPORTANT: TEST THE SAME PATH THE BROWSER USES

Do not only test AuthManager directly.

The final access tests MUST go through:

`https://127.0.0.1:8443`

using the existing OWNER certificate/key corresponding to the accepted OWNER identity.

Verify Nginx -> auth_request -> admin-shell end-to-end.

If possible, also inspect actual gateway/admin-shell logs for the successful request.

The user-facing symptom is gateway access denied, so a direct Python class test alone is insufficient.

---

# 8. REMOVE DANGEROUS/CONFUSING BEHAVIOR

Normal web restore must not:
- overwrite `data/auth`;
- regenerate CA;
- regenerate OWNER;
- reset registry;
- reset REVOKED/ACTIVE states.

Any backend helper inherited from Stage07B-R1/R2 that restores auth in the normal `/admin-api/backups/restore` path must be changed accordingly.

The backup may still package auth for future disaster recovery.

---

# 9. PROJECT RECORDS

Preserve prompt:

`.agents\received_prompts\TECHNOREBOOT_STAGE07B_R3_OWNER_ACCESS_RECOVERY_AND_SAFE_RESTORE_PROMPT.md`

Create/update:

`docs\stage07b_r3_owner_access_recovery_and_safe_restore.md`

`reports\stage07b_r3_owner_access_recovery_and_safe_restore_report.md`

`logs\2026-09-08.md`

Document:
- proven root cause;
- exact recovery;
- restore policy distinction;
- exact tests.

No passwords/private keys in docs/report/log.

---

# 10. GIT

Before commit:
- inspect git status/diff;
- no runtime auth files staged;
- no backup ZIP staged;
- no DB owner data staged;
- no private keys/passwords staged.

Then:
- commit;
- push origin/main;
- report commit hash;
- verify clean tracked worktree.

---

# 11. FINAL REPORT CONTRACT

Return:

```text
# Stage 07B-R3 — OWNER Access Recovery and Safe Web Restore

## Root Cause
PROVEN_ROOT_CAUSE:
WHY_OWNER_GOT_403:

## Existing OWNER Recovery
OWNER_SERIAL_EXPECTED:
OWNER_SERIAL_CURRENT:
OWNER_FINGERPRINT_EXPECTED:
OWNER_FINGERPRINT_CURRENT:
OWNER_IDENTITY_CHANGED: false
CA_CHANGED: false
NEW_OWNER_CREATED: false

## Live Access
OWNER_ROOT:
OWNER_CERTIFICATES:
OWNER_BACKUPS:

## Restore Policy
BACKUP_INCLUDES_AUTH: true
NORMAL_WEB_RESTORE_OVERWRITES_AUTH: false
NORMAL_WEB_RESTORE_PRESERVES_CURRENT_CERTIFICATES: true

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

## Exact Test Results

## Files Changed

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only:
1. Open https://127.0.0.1:8443/
2. Choose the already-installed Technoreboot OWNER certificate.
3. Confirm normal system opens.
4. Open /certificates.
5. Open /backups.
6. Download backup.
7. Restore it through web UI.
8. Confirm the SAME existing OWNER still works and certificates did not roll back.

FINAL_STATUS:
TECHNOREBOOT_STAGE07B_R3_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If the accepted OWNER still cannot pass the real gateway, return BLOCKED and do NOT claim success.

---

# 12. STOP

After implementation, verification, docs, commit/push and final report:

STOP.

Do not deploy to Internet.
Do not create new OWNER.
Do not add cloud backup.
Wait for owner acceptance.
