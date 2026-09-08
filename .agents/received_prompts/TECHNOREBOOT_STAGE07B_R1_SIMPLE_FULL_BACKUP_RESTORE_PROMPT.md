# TECHNOREBOOT — Stage 07B-R1
## Simple Full Backup / Restore

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07B-R1 — Simple Full Backup / Restore`

---

# 0. EXECUTION CONTRACT

This is the next owner-approved stage after accepted Stage 07A certificate access.

The goal is a SIMPLE and PRACTICAL full-system backup/restore mechanism.

Do NOT deploy to the Internet yet.
Do NOT redesign the application.
Do NOT add cloud backup.
Do NOT add schedulers/cron unless strictly needed for the local test.
Do NOT add complex backup infrastructure.

First copy this exact downloaded file:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07B_R1_SIMPLE_FULL_BACKUP_RESTORE_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07B_R1_SIMPLE_FULL_BACKUP_RESTORE_PROMPT.md`

Create the destination directory if needed.

Treat the copied file as authoritative.

---

# 1. ACCEPTED BASELINE

Stage 07A is accepted.

Current system includes:

- Docker-based modular Technoreboot stack;
- Core + DB/data;
- Inventory/Sales;
- Repairs;
- Avito;
- Admin Shell;
- mTLS gateway;
- persistent auth data under the current project/runtime structure;
- accepted commit from Stage 07A-R2.

Do not modify accepted business logic.

---

# 2. OWNER GOAL

The owner wants a backup that can be copied to a local PC / hard drive and later used to restore the entire working system after a complete server loss.

The backup must contain enough information to restore:

- application data;
- database data;
- uploaded/product photos and other persistent files;
- authentication CA / OWNER / certificate registry and required auth state;
- required configuration files;
- any other persistent runtime state actually required by the current project.

The restore flow must be simple.

Target practical model:

```text
running Technoreboot
        ↓
one backup command/script
        ↓
one timestamped backup folder/archive
        ↓
copy that backup to owner PC / external disk

and later:

fresh/new server with repository/runtime
        ↓
one restore command/script
        ↓
select backup
        ↓
restore persistent state
        ↓
start Technoreboot
```

---

# 3. FIRST — ANALYZE ACTUAL PERSISTENT STATE

Before implementation, inspect the current project and identify ALL data that must survive total server loss.

At minimum inspect:

- docker-compose volumes;
- bind mounts;
- Core/database storage;
- photo/media storage;
- repair/inventory/sales persistent data;
- Avito persistent state if any;
- `data/auth` / mTLS persistent state;
- `.env` / runtime configuration;
- gateway/auth certificates;
- any local SQLite/PostgreSQL/files used by modules;
- any runtime files needed to reproduce the current working system.

Do not assume.
Document the actual discovered list.

Do NOT include disposable items such as:

- Docker image layers;
- caches;
- temporary files;
- logs that are not needed for recovery;
- build artifacts;
- node_modules / venv / __pycache__;
- generated test artifacts unless recovery requires them.

---

# 4. IMPLEMENTATION — KEEP IT SIMPLE

Preferred implementation:

Create a dedicated directory, for example:

`backup/`

with simple Windows-friendly scripts.

At minimum provide:

```text
backup\
  backup_full.cmd
  restore_full.cmd
  README.md
```

Python/PowerShell helper scripts are allowed if they make the implementation reliable.

The owner should not need to manually collect individual files.

---

# 5. BACKUP BEHAVIOR

`backup_full.cmd` must:

1. Run from the project root or resolve `C:\tbootit` reliably.
2. Create a timestamped backup destination, for example:

`C:\tbootit\backups\TECHNOREBOOT_BACKUP_2026-09-08_143000\`

or a single archive:

`TECHNOREBOOT_BACKUP_2026-09-08_143000.zip`

3. Safely capture all required persistent data.

4. If the DB requires a logical dump for reliable recovery, create one.
   Prefer the existing database's supported dump mechanism rather than copying a live DB file unsafely.

5. Include auth persistent state required to preserve:
   - CA identity;
   - OWNER identity;
   - USER certificate registry;
   - certificate revoke state;
   - server/auth persistent secrets required by the current implementation.

6. Include a manifest describing:
   - backup creation time;
   - git commit;
   - included components;
   - backup format version;
   - source project path;
   - any DB dump filenames.

7. Produce a clear final message with:
   - success/failure;
   - exact backup output path;
   - approximate size.

8. Return non-zero exit code on real failure.

Do not silently continue after a failed critical backup step.

---

# 6. BACKUP DESTINATION / OWNER COPY

The immediate local workflow must support:

- creating the backup under `C:\tbootit\backups\...`;
- then owner can manually copy the resulting folder/archive to another local disk.

Do not add cloud services.

Do not require network storage.

Do not hardcode an external drive letter.

If easy, optionally allow passing a destination path:

```text
backup_full.cmd D:\TechnorebootBackups
```

But default behavior must work without arguments.

---

# 7. RESTORE BEHAVIOR

`restore_full.cmd` must restore from one selected backup.

Keep the interface simple.

Preferred usage:

```text
restore_full.cmd "D:\TechnorebootBackups\TECHNOREBOOT_BACKUP_....zip"
```

or a backup folder path.

Required behavior:

1. Validate the backup/manifest before destructive changes.
2. Confirm required files are present.
3. Stop only the containers/services necessary for safe restore.
4. Restore DB data.
5. Restore photos/media/persistent files.
6. Restore auth persistent state.
7. Restore required runtime configuration that belongs in backup.
8. Start the Technoreboot stack.
9. Run basic health/smoke checks.
10. Report success/failure clearly.

Avoid partial restore where possible.

If restore fails, print the exact failing step.

---

# 8. SAFETY RULES

Restore is destructive by nature.

At minimum:

- require explicit confirmation before overwriting current persistent data;
- never delete the selected backup;
- validate backup manifest first;
- do not overwrite the Git repository/source tree with arbitrary backup content unless the actual architecture proves that source files must be part of the recovery package.

The repository itself is already in GitHub.
The backup is primarily for persistent runtime/data recovery.

If specific non-Git configuration files are required for recovery, include only those.

---

# 9. AUTH BACKUP IS MANDATORY

Stage 07A auth state must be recoverable.

After restore, the SAME existing OWNER certificate must still work.

Required proof:

- OWNER cert identity before backup recorded internally;
- after destructive test restore, OWNER cert identity remains the same;
- CA remains the same;
- revoked USER remains revoked.

Do NOT generate a new CA or OWNER during restore if the backup contains them.

---

# 10. REAL RESTORE TEST — REQUIRED

Do not stop after creating scripts.

Perform an actual controlled local backup/restore validation.

Required minimum scenario:

1. Record baseline:
   - one known product/data record;
   - one persistent photo/media object if available;
   - OWNER certificate fingerprint/serial;
   - one revoked USER status if available.

2. Create full backup.

3. Make a controlled temporary change to persistent data after backup, for example:
   - add/edit a disposable test record;
   - or change a test value specifically created for this restore test.

Do NOT damage real owner data.

4. Execute restore from the created backup.

5. Verify:
   - pre-backup baseline data is restored;
   - post-backup disposable test change is gone/reverted as expected;
   - photos/media still work;
   - OWNER certificate still works;
   - CA identity unchanged;
   - revoked certificate state preserved;
   - application starts;
   - relevant healthchecks pass.

If a full destructive test cannot be done safely, construct an isolated duplicate/test target and explain exactly how it proves recovery.

But prefer a real controlled restore if safe.

---

# 11. TESTS

At minimum verify:

## TEST A
Backup script completes successfully.

## TEST B
Timestamped backup is created.

## TEST C
Manifest exists and is valid.

## TEST D
Database backup exists and is restorable.

## TEST E
Photos/media/persistent files are included.

## TEST F
Auth persistent state is included.

## TEST G
Restore script rejects an invalid/incomplete backup.

## TEST H
Restore from valid backup completes.

## TEST I
Core/application health after restore is good.

## TEST J
OWNER identity unchanged after restore.

## TEST K
CA identity unchanged after restore.

## TEST L
Revoked certificate remains revoked after restore.

## TEST M
Relevant project regression/backup contract tests pass.

Report exact executed commands and exact totals.

---

# 12. DO NOT OVERBUILD

Do NOT add now:

- S3;
- Yandex Object Storage;
- Google Drive;
- Dropbox;
- remote rsync server;
- scheduled daily jobs;
- retention policies;
- incremental backups;
- deduplication;
- encryption infrastructure;
- backup web dashboard;
- cloud monitoring;
- Kubernetes backup tools.

This stage is deliberately simple.

One backup.
One restore.
Easy to copy to owner's disk.

---

# 13. DOCUMENTATION

Preserve this received prompt:

`.agents\received_prompts\TECHNOREBOOT_STAGE07B_R1_SIMPLE_FULL_BACKUP_RESTORE_PROMPT.md`

Create:

`docs\stage07b_r1_simple_full_backup_restore.md`

`reports\stage07b_r1_simple_full_backup_restore_report.md`

Update:

`logs\2026-09-08.md`

README must include exact owner commands:

### Create backup

```text
cd /d C:\tbootit
backup\backup_full.cmd
```

### Restore backup

```text
cd /d C:\tbootit
backup\restore_full.cmd "<backup path>"
```

Document the exact resulting backup location.

---

# 14. GIT / SECRET SAFETY

Before commit:

- inspect `git status`;
- inspect staged diff;
- ensure no actual runtime backup archive is committed;
- ensure no database dump with owner data is committed;
- ensure no private auth keys/certificates are committed;
- backup output directory must be gitignored;
- scripts/docs/reports are committed.

Do not print passwords or private key contents in the report.

---

# 15. COMMIT / PUSH

After successful implementation and verification:

1. inspect diff;
2. stage safe implementation files only;
3. commit;
4. push to `origin/main`;
5. verify final HEAD;
6. verify final git status.

Do not start Internet deployment.

---

# 16. FINAL REPORT CONTRACT

Return:

```text
# Stage 07B-R1 — Simple Full Backup / Restore

## Preflight
BRANCH:
HEAD_BEFORE:
PERSISTENT_STATE_DISCOVERED:

## Backup Design
FORMAT:
DEFAULT_OUTPUT:
INCLUDED_COMPONENTS:
EXCLUDED_DISPOSABLE_COMPONENTS:

## Restore Design
RESTORE_COMMAND:
VALIDATION:
OVERWRITE_CONFIRMATION:
SERVICE_STOP_START_FLOW:

## Files Created / Changed

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

## Actual Backup Produced
BACKUP_PATH:
BACKUP_SIZE:
MANIFEST:
DB_DUMP:
MEDIA_INCLUDED:
AUTH_INCLUDED:

## Actual Restore Test
BASELINE:
CONTROLLED_POST_BACKUP_CHANGE:
RESTORE_RESULT:
DATA_RESTORED:
MEDIA_RESTORED:
OWNER_IDENTITY_PRESERVED:
CA_IDENTITY_PRESERVED:
REVOKED_STATE_PRESERVED:
HEALTH_AFTER_RESTORE:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
1.
2.
3.
4.
5.

FINAL_STATUS:
TECHNOREBOOT_STAGE07B_R1_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If any critical backup/restore verification fails, return a truthful BLOCKED status.

---

# 17. STOP

After implementation, verification, documentation, commit/push and final report:

STOP.

Do not deploy to Internet.
Do not add scheduled backups.
Do not add cloud backup.
Wait for owner acceptance.
