# TECHNOREBOOT — Stage 08D-R1R6
## OWNER Fast Rollback: pre-update release checkpoint, health preflight, local backup copy, one-click rollback

**Project:** ТехноРебут  
**Local workspace:** `C:\tbootit`  
**Production VDS:** `https://144.31.50.134`  
**SSH:** existing configured key `C:\Users\Apc\.ssh\id_ed25519`  
**Stage:** `Stage 08D-R1R6 — Fast Rollback / Release Checkpoint`

# 0. OWNER GOAL

Extend the existing OWNER-only local operations panel:

```text
https://localhost:8443/system/operations
```

with a fast, safe rollback mechanism for VDS updates.

Permanent data direction remains:

```text
CODE:
LOCAL -> Git -> VDS

BUSINESS DATA:
VDS -> LOCAL

FORBIDDEN:
LOCAL BUSINESS DB/MEDIA -> VDS during ordinary UPDATE or ordinary ROLLBACK
```

The VDS is canonical for business data.

The normal fast rollback is a CODE/RUNTIME rollback, not a database rollback.

Before every UPDATE VDS:

1. verify that VDS is actually alive and healthy enough to snapshot;
2. if VDS is dead/unreachable, show a clear warning and DO NOT create a bogus snapshot;
3. create a pre-update release checkpoint;
4. save the business backup on VDS AND copy the backup/checkpoint metadata to LOCAL;
5. preserve the currently running release identity so it can be quickly restored;
6. only then perform UPDATE.

If UPDATE fails, automatically attempt CODE rollback to the pre-update release.

Also provide an OWNER-only LOCAL button:

```text
[ Откатить VDS к последней рабочей версии ]
```

that restores the most recent valid release checkpoint without overwriting current business data.

---

# 1. IMPORTANT DISTINCTION: CODE ROLLBACK VS DATA RESTORE

Implement two clearly separated concepts.

## A. FAST ROLLBACK — normal operation

Restores:
- previous Git/runtime release;
- previous container application images or previous approved commit;
- previous application configuration version if tracked safely;
- no business DB replacement;
- no media replacement.

This is the button requested in this stage.

## B. BUSINESS DATA RESTORE — emergency only

Restores DB/media from a backup and can destroy newer real user data.

DO NOT attach this to the normal rollback button.

If a full data restore already exists under `/backups`, keep it separate.

The UI must clearly state:

```text
Быстрый откат возвращает только программную версию.
Текущие товары, продажи, ремонты и фотографии VDS не заменяются.
```

---

# 2. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08D_R1R6_OWNER_FAST_ROLLBACK_RELEASE_CHECKPOINT_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08D_R1R6_OWNER_FAST_ROLLBACK_RELEASE_CHECKPOINT_PROMPT.md`

---

# 3. PREFLIGHT CURRENT STATE

Record:

```text
LOCAL_HEAD
ORIGIN_MAIN_HEAD
LOCAL_GIT_STATUS
LOCAL_STACK_HEALTHY

VDS_HEAD
VDS_STACK_HEALTHY
VDS_PRODUCTS
VDS_SALES
VDS_REPAIRS
VDS_PHOTOS
VDS_EXTERNAL_LISTINGS
VDS_DB_SHA256
VDS_SCHEMA_SHA256
VDS_CA_SHA256
VDS_STORAGE_TREE_SHA256
```

Do not assume historical counts.

---

# 4. VDS LIVENESS / HEALTH PREFLIGHT BEFORE UPDATE

Before allowing UPDATE, perform a dedicated preflight.

Required checks:

```text
SSH reachable
HTTPS 443 reachable
OWNER-authenticated health page/API reachable where practical
production data sentinel present
Docker daemon reachable
all expected services discoverable
SQLite DB readable in read-only mode
PRAGMA quick_check = ok
sufficient free disk space for backup + deployment
Git repo readable
current VDS HEAD resolvable
current schema guard status SAFE
```

Classify:

```text
HEALTHY
DEGRADED
UNREACHABLE
```

## UPDATE behavior

### HEALTHY
Continue.

### DEGRADED
Block UPDATE by default and show precise warning.

Example:

```text
VDS отвечает, но состояние нештатное:
- repairs unhealthy
- свободно мало диска

UPDATE отменён.
Сначала устраните проблему или выполните отдельную диагностику.
```

Do not create a "healthy pre-update checkpoint" from a degraded server.

### UNREACHABLE
Hard block UPDATE.

Example:

```text
VDS недоступен.
SSH/HTTPS не отвечает.

Snapshot и UPDATE не выполнялись.
```

Critical Owner requirement:

```text
DO NOT SNAPSHOT A DEAD / UNREACHABLE VDS.
```

---

# 5. RELEASE CHECKPOINT MODEL

Create a structured release checkpoint before UPDATE.

Recommended local metadata root:

```text
.local-recovery/vds-releases/
```

Recommended VDS metadata root:

```text
/srv/technoreboot/data/backups/release-checkpoints/
```

For every checkpoint create a manifest, e.g.:

```text
release_20260912_191500_<short-head>.json
```

Required fields:

```text
checkpoint_id
created_at
status
vds_ip
previous_head
target_head
previous_schema_sha256
target_schema_sha256
business_backup_file
business_backup_sha256
business_counts
storage_tree_sha256
ca_sha256
production_guard_verified
health_preflight
rollback_allowed
rollback_reason
```

Do not store credentials.

---

# 6. PRE-UPDATE BUSINESS BACKUP

For HEALTHY VDS only:

Create a fresh normal production backup using the accepted VDS backup mechanism.

Record:

```text
BACKUP_FILE
BACKUP_SHA256
BACKUP_CREATED_AT
```

Verify ZIP integrity and manifest.

The backup must stay on VDS.

Additionally COPY the exact backup archive to LOCAL recovery storage:

```text
.local-recovery/vds-releases/<checkpoint_id>/
```

Required local artifacts:

```text
checkpoint.json
business-backup.zip
business-backup.sha256
```

Verify:

```text
LOCAL_COPY_SHA256 == VDS_BACKUP_SHA256
```

Do not commit local recovery artifacts.

---

# 7. PRESERVE PREVIOUS APPLICATION RELEASE FOR FAST ROLLBACK

Fast rollback should not need a full fresh rebuild if avoidable.

Before UPDATE, preserve the currently running release.

Preferred implementation:

- record exact previous Git HEAD;
- record exact image IDs/digests for all application services;
- tag/preserve the currently running application images with checkpoint-specific rollback tags.

Example conceptual tags:

```text
technoreboot-rollback/<checkpoint_id>/core
technoreboot-rollback/<checkpoint_id>/admin-shell
technoreboot-rollback/<checkpoint_id>/inventory-sales
technoreboot-rollback/<checkpoint_id>/repairs
technoreboot-rollback/<checkpoint_id>/avito
```

Gateway can also be preserved if its image/config changed.

Do NOT depend only on Git checkout + full rebuild if a safe image-level rollback can be implemented.

If image preservation is impractical with current compose architecture, implement a deterministic fallback:

```text
checkout previous_head
rebuild previous release
recreate containers
```

but report expected rollback time.

---

# 8. LAST KNOWN GOOD RELEASE

Maintain:

```text
data/dev-ops/status/last_known_good_vds_release.json
```

LOCAL only.

After successful UPDATE + health/data verification:
- the NEW release becomes `last_known_good`;
- the previous release checkpoint remains available for rollback/history.

Keep at least:

```text
3 most recent valid release checkpoints
```

or a configurable retention count.

Do not automatically delete the only known-good checkpoint.

---

# 9. UPDATE WORKFLOW WITH CHECKPOINT

Modify existing `UPDATE VDS` workflow:

```text
1. OWNER / LOCAL-only guard
2. operation lock
3. Git clean/pushed check
4. DB schema guard
5. VDS liveness/health preflight
6. if not HEALTHY -> STOP, no checkpoint, no update
7. create VDS business backup
8. verify backup
9. copy backup to LOCAL recovery
10. create release checkpoint manifest
11. preserve current application images/release
12. execute code-only UPDATE
13. wait for health
14. validate routes
15. validate business counts/content
16. validate CA
17. mark update SUCCESS
18. mark new release known-good
```

---

# 10. AUTOMATIC ROLLBACK ON FAILED UPDATE

If UPDATE reaches deployment phase and then fails:

Automatically attempt fast CODE rollback to the pre-update checkpoint.

Required:

```text
AUTO_ROLLBACK_ATTEMPTED = true
```

Rollback:
- must NOT restore business DB/media;
- must restore previous code/runtime release;
- must wait for all services healthy;
- must verify business counts/content still present;
- must verify Client CA unchanged.

Final job status examples:

```text
UPDATE_FAILED_ROLLBACK_SUCCESS
UPDATE_FAILED_ROLLBACK_FAILED
```

If rollback fails:
- preserve all checkpoint artifacts;
- do not attempt a data restore automatically;
- show emergency message and diagnostic details.

Never automatically overwrite business DB after a failed code deploy.

---

# 11. MANUAL "ROLLBACK VDS" BUTTON

Add OWNER-only LOCAL button to `/system/operations`:

```text
[ Откатить VDS к последней рабочей версии ]
```

Only active when:
- environment = LOCAL DEV;
- OWNER;
- no operation running;
- VDS reachable;
- valid rollback checkpoint exists;
- rollback compatibility guard passes.

On VDS itself:
- disabled;
- direct POST rejected.

---

# 12. ROLLBACK CONFIRMATION MODAL

Show:

```text
ОТКАТ VDS

Будет восстановлена предыдущая рабочая версия
программного кода и контейнеров VDS.

Текущая база данных, товары, продажи, ремонты,
фотографии и другие рабочие данные VDS
заменены НЕ будут.

Последняя рабочая версия:
<commit / timestamp>

Текущая версия:
<commit>

Продолжить?
```

Buttons:

```text
[ Отмена ]
[ Откатить VDS ]
```

---

# 13. ROLLBACK COMPATIBILITY / SCHEMA GUARD

Fast code rollback is allowed only if current VDS DB schema is compatible with the target previous release.

Before rollback compare:

```text
current VDS live schema contract
target rollback release schema contract
```

If exact schema differs:

```text
ROLLBACK BLOCKED
```

Show:

```text
Быстрый откат заблокирован:
структура базы данных отличается от структуры
предыдущей версии приложения.

Нужен отдельный ручной recovery/migration этап.
База VDS не изменена.
```

This is critical.

A schema migration can make old code incompatible with the new DB.

Do NOT auto-restore the old DB to "fix" this.

---

# 14. ROLLBACK EXECUTION

If schema-compatible:

1. Check VDS liveness.
2. Record current HEAD and counts.
3. Create a SMALL fresh safety business backup of current VDS before rollback if VDS is healthy.
4. Copy that rollback-safety backup to LOCAL recovery.
5. Restore previous application release/images.
6. Recreate application containers.
7. Healthcheck all 6 services.
8. Verify primary routes.
9. Verify business data still present.
10. Verify CA unchanged.
11. Record rollback audit.

The backup from step 3 is for disaster recovery only.
The fast rollback itself still does NOT restore DB/media.

---

# 15. WHAT IF VDS IS DEAD WHEN OWNER PRESSES ROLLBACK?

Distinguish network/server-down from app-broken.

## SSH unreachable
Show:

```text
VDS полностью недоступен по SSH.
Автоматический откат невозможен.

Последний локальный recovery checkpoint сохранён:
<path / timestamp>
```

Do not pretend rollback succeeded.

## SSH reachable but application HTTPS/services broken
Allow rollback if:
- production sentinel can be verified;
- filesystem/repo/Docker reachable;
- DB is readable;
- schema compatibility can be checked.

This is an important use case:
application can be broken while server itself is alive.

---

# 16. LOCAL RECOVERY INVENTORY UI

In `/system/operations` show a section:

```text
Последние точки восстановления VDS
```

Columns:

```text
Дата
Commit
Schema hash
Backup
Backup SHA256
Status
Can rollback?
```

Allow selecting only valid rollback-compatible checkpoints.

For this stage, the main button may default to the newest valid previous checkpoint.

Do NOT provide browser download of SSH/private secrets.

---

# 17. RETENTION

Implement safe retention:

Default:

```text
keep last 3 complete release checkpoints locally
keep existing normal VDS backup policy unchanged
```

A checkpoint is complete only if:
- VDS backup verified;
- local copy verified;
- manifest complete.

Never delete:
- current known-good checkpoint;
- newest pre-update checkpoint while update is in progress.

---

# 18. STORAGE / DISK SPACE GUARD

Before making backup/checkpoint, estimate required space.

Check:
- VDS free disk;
- LOCAL free disk.

If insufficient:

```text
UPDATE BLOCKED:
Недостаточно места для безопасной точки восстановления.
```

Do not proceed without backup.

---

# 19. OWNER / USER / ENVIRONMENT GUARDS

OWNER local:
- may update;
- may sync;
- may rollback.

USER:
- cannot see controls;
- action endpoints 403.

VDS production UI:
- actions disabled;
- direct endpoints rejected.

Reuse Stage08D-R1R5 local sentinel + production sentinel protections.

---

# 20. OPERATIONS / JOB LOCKING

Rollback joins the existing operation queue.

Allowed operation types:

```text
sync_vds_to_local
update_vds_code_only
rollback_vds_code_only
```

Only one operation at a time.

No generic shell action.

---

# 21. AUDIT LOG

For UPDATE checkpoint record:

```text
operation_id
checkpoint_id
health_preflight
previous_head
target_head
backup_file_vds
backup_file_local
backup_sha256
previous_image_ids
schema_sha256
started_at
finished_at
update_result
auto_rollback_result
```

For manual rollback:

```text
rollback_operation_id
source_checkpoint_id
current_head_before
target_head
safety_backup_before_rollback
health_result
data_preservation_result
final_head
result
```

No secrets.

---

# 22. OPTIONAL VM SNAPSHOT / PROVIDER SNAPSHOT

Do NOT make this stage depend on a Serv.Host/provider VM snapshot API unless that API is already safely available.

Application-level release checkpoint is the canonical mechanism.

Document:

```text
VM/provider snapshot can be added later as an extra disaster-recovery layer.
It is NOT required for normal fast rollback.
```

Reason:
normal code rollback should be faster and should not revert newer business data.

---

# 23. TESTS

Add tests for:

## Preflight
- unreachable SSH -> update blocked;
- dead HTTPS + alive SSH classified correctly;
- unhealthy service -> update blocked;
- unreadable DB -> update blocked;
- low VDS disk -> update blocked;
- low local disk -> update blocked.

## Checkpoint
- business backup created only when healthy;
- backup copied VDS -> LOCAL;
- SHA match required;
- manifest required;
- previous HEAD/images captured.

## Update
- update cannot start without complete checkpoint;
- failed update invokes automatic code rollback;
- successful update does not rollback;
- business DB never restored during auto rollback.

## Manual rollback
- OWNER local allowed;
- USER forbidden;
- VDS action forbidden;
- no checkpoint -> disabled/blocked;
- schema mismatch -> blocked;
- compatible schema -> rollback allowed;
- DB/media remain unchanged.

## Direction safety
- no LOCAL DB upload path;
- no LOCAL media upload path;
- rollback does not restore old business backup automatically.

## Retention
- keep minimum 3;
- do not delete known-good/current checkpoint.

Required:

```text
FAILED = 0
```

---

# 24. LIVE SAFE TEST PLAN

Do NOT intentionally break production.

Perform a safe live proof:

1. run VDS preflight;
2. create a real release checkpoint from current healthy VDS;
3. verify local backup copy SHA;
4. do NOT force a failed production deploy;
5. test automatic rollback using mocked/integration environment locally;
6. test manual rollback endpoint in dry-run/preflight mode against VDS;
7. confirm schema compatibility;
8. confirm actual rollback button becomes available with checkpoint;
9. do NOT actually roll production backward if current release is healthy unless strictly necessary for proof.

If an actual rollback is performed for proof:
- only between schema-identical releases;
- first create fresh safety backup;
- immediately verify all data;
- return to intended current release afterward through normal code-only UPDATE;
- document exact sequence.

Prefer no unnecessary production churn.

---

# 25. UI STATUS

Operations page should show:

```text
VDS Health:
Healthy / Degraded / Unreachable

Current VDS release:
<commit>

Last known good:
<commit>

Latest recovery checkpoint:
<timestamp>

Local backup copy:
Verified

Rollback available:
Yes / No
```

Buttons:

```text
[ Синхронизировать данные с VDS ]
[ UPDATE VDS ]
[ Откатить VDS к последней рабочей версии ]
```

---

# 26. DOCUMENTATION

Create/update:

```text
docs/owner_operations_sync_update_rollback.md
docs/vds_fast_rollback.md
docs/production_deployment_model.md
docs/production_status.md

reports/stage08d_r1r6_fast_rollback_release_checkpoint_report.md

tests/test_owner_operations_preflight.py
tests/test_owner_operations_checkpoint.py
tests/test_owner_operations_rollback.py
tests/test_owner_operations_rollback_schema_guard.py
```

Update:

```text
logs/2026-09-12.md
```

Preserve received prompt.

---

# 27. FINAL REPORT CONTRACT

Return:

```text
# Stage 08D-R1R6 — Fast Rollback / Release Checkpoint

## VDS Preflight
HEALTH_PROBE_IMPLEMENTED:
SSH_CHECK:
HTTPS_CHECK:
DOCKER_CHECK:
SERVICES_CHECK:
DB_READ_CHECK:
DB_QUICK_CHECK:
DISK_SPACE_CHECK:
DEAD_VDS_SNAPSHOT_BLOCKED:
DEGRADED_VDS_UPDATE_BLOCKED:

## Release Checkpoint
CHECKPOINT_ROOT_LOCAL:
CHECKPOINT_ROOT_VDS:
CHECKPOINT_ID:
PREVIOUS_HEAD:
TARGET_HEAD:
VDS_BACKUP_FILE:
VDS_BACKUP_SHA256:
LOCAL_BACKUP_COPY:
LOCAL_BACKUP_SHA256:
BACKUP_HASH_MATCH:
PREVIOUS_IMAGES_CAPTURED:
SCHEMA_SHA256_CAPTURED:
CHECKPOINT_COMPLETE:

## UPDATE Integration
UPDATE_REQUIRES_CHECKPOINT:
CODE_ONLY_DEPLOY:
LOCAL_DB_UPLOADED_TO_VDS: false
LOCAL_MEDIA_UPLOADED_TO_VDS: false
AUTO_ROLLBACK_ON_UPDATE_FAILURE:
AUTO_ROLLBACK_RESTORES_DB: false
LAST_KNOWN_GOOD_TRACKED:

## Manual Rollback
ROLLBACK_BUTTON_ROUTE:
OWNER_LOCAL_ALLOWED:
USER_FORBIDDEN:
VDS_ACTION_FORBIDDEN:
ROLLBACK_TARGET:
ROLLBACK_SCHEMA_COMPATIBILITY:
ROLLBACK_RESTORES_CODE_ONLY:
ROLLBACK_RESTORES_BUSINESS_DB: false
ROLLBACK_RESTORES_MEDIA: false
ROLLBACK_SAFETY_BACKUP_BEFORE_ACTION:
ROLLBACK_HEALTH_VERIFY:
ROLLBACK_DATA_PRESERVATION_VERIFY:

## Dead / Broken VDS
SSH_UNREACHABLE_BEHAVIOR:
SSH_ALIVE_APP_BROKEN_BEHAVIOR:
NO_FAKE_SUCCESS:

## Retention
CHECKPOINT_RETENTION_COUNT:
KNOWN_GOOD_PROTECTED:

## Tests
FAILED:

## Current Production Safety
VDS_PRODUCTS_BEFORE:
VDS_PRODUCTS_AFTER:
VDS_SALES_BEFORE:
VDS_SALES_AFTER:
VDS_REPAIRS_BEFORE:
VDS_REPAIRS_AFTER:
VDS_PHOTOS_BEFORE:
VDS_PHOTOS_AFTER:
VDS_LISTINGS_BEFORE:
VDS_LISTINGS_AFTER:
CLIENT_CA_SHA256_UNCHANGED:
ALL_VDS_SERVICES_HEALTHY:

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08D_R1R6_FAST_ROLLBACK_RELEASE_CHECKPOINT_READY

NORMAL_ROLLBACK_IS_CODE_ONLY: true
BUSINESS_DATA_RESTORE_REMAINS_SEPARATE: true
VDS_IS_CANONICAL_BUSINESS_DATA: true
DEAD_VDS_IS_NEVER_SNAPSHOTTED_AS_GOOD: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- UPDATE can start without healthy preflight/checkpoint;
- dead VDS can be snapshotted as healthy;
- checkpoint local copy hash mismatches;
- rollback overwrites business DB/media;
- rollback ignores schema incompatibility;
- USER or VDS can execute rollback;
- tests fail.

---

# 28. STOP

After implementation and safe proof:

STOP.

Wait for Owner browser acceptance.
