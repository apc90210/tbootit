# TECHNOREBOOT — Stage 08D-R1R5
## OWNER Operations: VDS→LOCAL Sync + Code-Only UPDATE + DB Schema Guard

**Project:** ТехноРебут  
**Local workspace:** `C:\tbootit`  
**Production VDS:** `https://144.31.50.134`  
**VDS SSH:** `root@144.31.50.134` using the already configured local SSH key  
**Stage:** `Stage 08D-R1R5 — OWNER Sync / Update Control Panel`

# 0. OWNER DECISION

This stage supersedes the separate final parity-only prompt if it has not yet been executed.

The Owner wants two safe operations directly from the web UI:

```text
1. СИНХРОНИЗИРОВАТЬ ДАННЫЕ
2. UPDATE VDS
```

Permanent direction model:

```text
CODE:
LOCAL DEV -> Git -> VDS

BUSINESS DATA:
VDS -> LOCAL

FORBIDDEN:
LOCAL BUSINESS DATA -> VDS
```

The VDS is the canonical source of truth for real business data.

The LOCAL environment is the development/test environment and receives fresh snapshots of VDS business data when the Owner explicitly requests synchronization.

The VDS production database/media must NEVER be replaced by local business data through these buttons.

---

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08D_R1R5_OWNER_OPS_SYNC_UPDATE_SCHEMA_GUARD_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08D_R1R5_OWNER_OPS_SYNC_UPDATE_SCHEMA_GUARD_PROMPT.md`

---

# 2. CURRENT BASELINE / PREFLIGHT

Inspect current repo and current runtime before modifying anything.

Record:

```text
LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
LOCAL_GIT_STATUS:
LOCAL_STACK_HEALTHY:

VDS_HEAD:
VDS_STACK_HEALTHY:
VDS_PRODUCTS:
VDS_SALES:
VDS_REPAIRS:
VDS_PHOTOS:
VDS_EXTERNAL_LISTINGS:
VDS_DB_SHA256:
VDS_STORAGE_TREE_SHA256:
VDS_CA_SHA256:
```

Do NOT assume historical counts such as 149 remain current.

Real users may already be working.

Preserve the CURRENT VDS data exactly.

---

# 3. OWNER-ONLY OPERATIONS UI

Add an OWNER-only system operations section in the existing UI style.

Preferred location:
- dedicated route `/system/operations`
- or an OWNER-only card on the existing administrative page if that fits current navigation better.

The UI must show:

```text
Environment: LOCAL DEV / PRODUCTION VDS
Local Git HEAD
origin/main HEAD
VDS Git HEAD
Last successful VDS→LOCAL sync
Last successful VDS update
Current DB schema compatibility status
Current job status
```

Add two primary buttons:

```text
[ Синхронизировать данные с VDS ]
[ UPDATE VDS ]
```

Both controls are OWNER-only.

USER:
- must not see them;
- must receive HTTP 403 if attempting the endpoints directly.

---

# 4. LOCAL-ONLY HARD GUARD

These operations MUST be executable only from the LOCAL environment.

Use multiple independent guards.

At minimum require:

```text
OWNER certificate
AND ENVIRONMENT != production
AND local DEV sentinel exists
AND production data sentinel is absent locally
```

Create a local sentinel if an equivalent does not already exist:

```text
data/.technoreboot_local_dev
```

Safe content:

```text
environment=development
operations=local_only
```

On VDS:

```text
/srv/technoreboot/data/.technoreboot_production_data
```

already exists.

If production sentinel exists, operations MUST hard reject.

Production UI behavior:
- page may show synchronization/update status;
- action buttons must be disabled or hidden;
- explanatory text: `Операция доступна только на локальном DEV-сервере`;
- direct action endpoint must return 403/409 and perform ZERO action.

Do NOT rely only on Host header / URL / JavaScript hiding.

Backend guard is mandatory.

---

# 5. SAFE LOCAL OPERATIONS EXECUTOR

The existing business sync script runs on the Windows host and may need:
- SSH/SCP;
- filesystem replacement;
- local Docker start/stop/restart.

Do NOT solve this by exposing:
- Docker socket to a public/web-facing production container;
- the Windows SSH private key to VDS;
- production secrets through the browser.

Implement the smallest safe LOCAL-only operations executor.

Preferred architecture:

```text
Admin UI
  ->
OWNER-authenticated LOCAL admin-shell request
  ->
local-only operations job
  ->
host-side operations runner
```

A file/job-queue based local runner is acceptable and preferred if it avoids exposing a network management port.

Example concept:

```text
data/dev-ops/requests/
data/dev-ops/status/
```

The web application creates an operation request only after OWNER + local-environment authorization.

A LOCAL host-side runner executes the request using existing scripts and writes structured progress/status.

Alternative architecture is acceptable if equally safe.

Hard requirements:
- no production-accessible executor;
- no SSH private key committed;
- no Docker socket exposed to VDS;
- no arbitrary command execution from browser input;
- only allow whitelisted operations: `sync_vds_to_local`, `update_vds_code_only`;
- only one operation at a time;
- operation ID + timestamps + structured log;
- no shell command supplied by the browser.

Integrate the local runner into the project's normal LOCAL startup workflow so the Owner does not need to start it manually every time.

---

# 6. BUTTON 1 — "СИНХРОНИЗИРОВАТЬ ДАННЫЕ С VDS"

The button is ACTIVE only on LOCAL DEV for OWNER.

Before execution show confirmation modal:

```text
Синхронизация заменит локальные рабочие бизнес-данные
актуальной копией данных с VDS.

Перед заменой будет создана локальная резервная копия.

Направление:
VDS -> LOCAL

Данные VDS изменены не будут.

Продолжить?
```

Buttons:

```text
[ Отмена ]
[ Синхронизировать ]
```

---

# 7. SYNC OPERATION BEHAVIOR

Reuse and harden:

```text
scripts/sync_vds_business_to_local.py
```

The UI operation must execute this accepted one-way flow.

Required steps:

1. Check SSH access to `root@144.31.50.134`.
2. Verify production sentinel.
3. Read current VDS counts/hashes.
4. Create a FRESH VDS backup/snapshot.
5. Verify snapshot ZIP SHA256/integrity.
6. Create LOCAL pre-sync safety backup.
7. Stop LOCAL business-writing services only as required.
8. Replace LOCAL canonical business DB from VDS snapshot.
9. Replace LOCAL business storage/media from VDS snapshot.
10. Synchronize approved Avito BUSINESS state.
11. Do NOT import production environment secrets.
12. Start/restart LOCAL stack.
13. Verify business table parity.
14. Verify recursive storage hash parity.
15. Verify VDS was not modified.
16. Save last-sync metadata.

Required direction:

```text
VDS -> LOCAL
```

There must be NO reverse mode.

The sync tool must explicitly refuse:

```text
--push
--upload
--to-vds
```

or any equivalent reverse direction.

---

# 8. WHAT SYNC COPIES

MUST synchronize:

```text
SQLite business DB
product/media storage
business inventory state
sales/repairs/customer business rows
product photos
external listings
approved Avito business/listing/import state
```

Do NOT automatically copy environment secrets such as:

```text
production TLS private key
SSH private keys
production.env
Certbot private state
live pairing codes
live extension tokens
browser cookies/session secrets
```

The shared OWNER client certificate trust model may remain as already configured.

---

# 9. SYNC UI STATUS

During sync, show:

```text
Подготовка
Создание snapshot VDS
Проверка backup
Создание локального backup
Остановка локальных сервисов
Копирование базы
Копирование media
Проверка хэшей
Запуск локальных сервисов
Готово
```

After success show:

```text
Последняя синхронизация:
<timestamp>

VDS products:
LOCAL products:

DB parity:
Storage parity:
Business-table mismatches:
```

If it fails:
- show the actual safe error;
- do not expose secrets;
- leave VDS untouched;
- restore local pre-sync state if replacement had already begun and local cannot be made healthy.

---

# 10. BUTTON 2 — "UPDATE VDS"

This is NOT a business-data upload.

The button means:

```text
Deploy application/source/runtime changes from Git to VDS,
while preserving VDS database/media/business state.
```

Before execution show strong confirmation:

```text
UPDATE обновит программный код и контейнеры VDS.

База данных, товары, продажи, ремонты, фотографии
и остальные рабочие данные VDS заменены НЕ будут.

Перед обновлением будет создан backup VDS.

Продолжить?
```

Buttons:

```text
[ Отмена ]
[ Выполнить UPDATE ]
```

---

# 11. UPDATE PRECONDITIONS

UPDATE must refuse unless ALL are true:

```text
OWNER authenticated
LOCAL DEV environment
local git worktree clean
LOCAL HEAD == origin/main
VDS reachable by SSH
production data guard present
schema compatibility = SAFE
no manual migration required
```

If local changes are not committed/pushed:

```text
UPDATE BLOCKED:
Есть незакоммиченные или не отправленные изменения.
Сначала завершите Git-этап.
```

Do not auto-commit source code from the UI.

---

# 12. DB SCHEMA CHANGE GUARD — CRITICAL

The Owner explicitly requires:

> If development introduces a new table, column, index,
> constraint, migration requirement or another meaningful DB structural change,
> the ordinary UPDATE button must NOT run.

Implement TWO independent schema guards.

## A. Automatic schema contract comparison

Create a deterministic schema contract/fingerprint system, for example:

```text
scripts/db_schema_contract.py
deploy/production/schema_contract.json
```

The normalized contract must include where applicable:

```text
tables
columns
column types
nullable
defaults
primary keys
foreign keys
unique constraints
indexes
```

Generate the expected schema from CURRENT CODE / migrations / model metadata, not merely from the current local runtime DB.

Compare expected schema against LIVE VDS schema before UPDATE.

Any difference means:

```text
SCHEMA_COMPATIBILITY = BLOCKED
```

Conservative rule:

```text
ANY schema structural difference blocks normal UPDATE.
```

Do not try to silently migrate production from this button.

## B. Agent-managed deployment compatibility flag

Create tracked file, for example:

```text
deploy/production/deployment_compatibility.json
```

Suggested structure:

```json
{
  "version": 1,
  "requires_manual_migration": false,
  "database_change": false,
  "reason": "",
  "schema_contract_sha256": "",
  "reviewed_at_commit": ""
}
```

Rules:
- whenever an agent changes DB models/schema/migrations, it MUST set `requires_manual_migration=true` and `database_change=true`;
- it must explain the required migration;
- normal UPDATE refuses while flag is true;
- only a dedicated Owner-approved migration stage may update VDS schema;
- after successful migration and verification the agent may reset the flag.

Do not rely on the manual flag alone.
Automatic live schema comparison is still mandatory.

---

# 13. SCHEMA CONTRACT REGRESSION TEST

Add a test that:
1. generates schema contract from current source;
2. compares it with tracked `schema_contract.json`;
3. fails if code schema changed but tracked contract was not updated.

This ensures a development agent cannot casually forget to record schema changes.

Example expected failure:

```text
DB SCHEMA CONTRACT CHANGED.
Normal VDS UPDATE is blocked.
Manual migration stage required.
```

---

# 14. UPDATE BLOCKED UI

When schema differs, the button must be disabled and show:

```text
UPDATE недоступен.

Обнаружено изменение структуры базы данных:
- <table/column/etc>

Нужна ручная миграция VDS через отдельный этап агента.
Рабочая база VDS не изменена.
```

Display:
- expected schema fingerprint;
- VDS live fingerprint;
- concise structural diff.

Do not expose credentials.

---

# 15. UPDATE EXECUTION

If all guards PASS:

1. Record VDS current business counts.
2. Create fresh VDS backup.
3. Record backup SHA256.
4. Record current VDS DB/content snapshot metadata.
5. Execute ONLY `deploy/production/update_code_only.sh <approved commit>`.
6. Never invoke bootstrap restore.
7. Never copy LOCAL DB/media/auth/Avito runtime to VDS.
8. Rebuild/recreate containers.
9. Wait for all services healthy.
10. Verify VDS business counts/content preserved.
11. Verify Client CA unchanged.
12. Verify primary routes.
13. Save last-update metadata.

If deployment fails:
- rollback CODE;
- preserve VDS data;
- report failure.

---

# 16. UPDATE UI PROGRESS

Show:

```text
Проверка Git
Проверка схемы БД
Проверка VDS
Создание backup VDS
Обновление Git
Сборка контейнеров
Перезапуск
Healthcheck
Проверка данных
Готово
```

After success:

```text
UPDATE выполнен

Commit:
Backup:
VDS services:
Business data preserved:
```

---

# 17. PRODUCTION-SIDE BEHAVIOR

Deploy this UI code to both LOCAL and VDS so code remains identical.

On VDS:

```text
Синхронизация данных -> disabled
UPDATE VDS -> disabled
```

Text:

```text
Управление синхронизацией доступно только
из локальной DEV-среды ТехноРебут.
```

Direct POST/action calls on VDS must:
- reject with 403/409;
- create no jobs;
- execute no SSH;
- execute no deploy;
- mutate no data.

---

# 18. OWNER / USER RBAC

OWNER:
- can see operations page;
- LOCAL: may use sync/update subject to guards;
- VDS: sees disabled status/read-only view.

USER:
- operations navigation item hidden;
- `/system/operations` -> 403;
- all operation APIs -> 403.

Keep all previously accepted RBAC protections.

---

# 19. AUDIT LOG

Every requested operation must write an audit record:

```text
operation_id
operation_type
requested_at
started_at
finished_at
result
local_head
vds_head_before
vds_head_after
backup_file
safe summary
```

Do NOT record:
- private key contents;
- passwords;
- tokens;
- environment secrets.

---

# 20. CONCURRENCY / LOCKING

Only one system operation at a time.

If sync/update already running:

```text
409 Operation already in progress
```

Do not allow:
- sync during update;
- update during sync.

Use an atomic local lock/job-state mechanism.

Stale locks must have a safe recovery rule.

---

# 21. CURRENT INITIAL IMPLEMENTATION FLOW

After implementing the feature locally:

1. Run all tests.
2. Commit/push source.
3. Confirm DB schema guard reports SAFE for current release.
4. Create VDS backup.
5. Deploy code to VDS through existing code-only mechanism.
6. Verify VDS business data preserved.
7. Use the NEW synchronization operation (button backend / same operation executor) to take a brand-new VDS snapshot and sync business data VDS→LOCAL.
8. Prove exact final parity.
9. Leave both stacks running.

This stage must therefore finish with both code and current business data aligned according to the model:

```text
CODE:
LOCAL HEAD == origin/main == VDS HEAD

BUSINESS DATA AT LAST SYNC:
LOCAL business snapshot == VDS snapshot
```

---

# 22. EXACT PARITY VERIFICATION

For the final fresh sync compute:

```text
VDS snapshot DB SHA256
LOCAL raw DB SHA256 before local startup
recursive storage tree SHA256
business table content hashes
```

Required:

```text
RAW_DB_MATCH = true
STORAGE_TREE_MATCH = true
BUSINESS_TABLE_MISMATCHES = 0
```

After local services start, raw SQLite file hash may legitimately change.

Then compare deterministic BUSINESS content hashes, not merely raw DB bytes.

---

# 23. TESTS

Add and run at minimum:

### RBAC
- USER operations page forbidden.
- USER sync API forbidden.
- USER update API forbidden.
- OWNER local accepted.
- OWNER VDS action rejected.

### Environment guard
- production sentinel blocks operations.
- local sentinel required.

### Sync
- VDS→LOCAL allowed.
- reverse direction rejected.
- local safety backup required.
- VDS not mutated.
- parity checks.

### Update
- dirty Git blocks.
- unpushed Git blocks.
- missing production sentinel blocks.
- failed VDS backup blocks.
- update uses code-only deploy.
- no local data upload path exists.

### Schema guard
- identical schema -> SAFE.
- new table -> BLOCKED.
- new column -> BLOCKED.
- changed type -> BLOCKED.
- changed FK/index/constraint -> BLOCKED as supported.
- `requires_manual_migration=true` -> BLOCKED.
- source schema vs tracked contract mismatch -> test failure.

### Regression
Run the previously accepted production/data guard/RBAC/Avito suites.

Required:

```text
FAILED = 0
```

---

# 24. SECURITY REQUIREMENTS

Never commit:
- SSH private key;
- TLS private key;
- OWNER private key;
- passwords;
- production.env;
- pairing tokens/codes;
- production backup ZIP;
- runtime DB;
- media.

The local runner may use the existing SSH key path through local configuration only.

Do not expose that path/value to normal USER UI.

Do not create a generic remote shell endpoint.

---

# 25. FILES / DOCUMENTATION

Create/update as appropriate:

```text
docs/owner_operations_sync_update.md
docs/vds_to_local_data_sync.md
docs/production_deployment_model.md
docs/production_status.md

reports/stage08d_r1r5_owner_ops_sync_update_schema_guard_report.md

tests/test_owner_operations_rbac.py
tests/test_owner_operations_environment_guard.py
tests/test_owner_operations_schema_guard.py
tests/test_owner_operations_direction_guard.py

deploy/production/schema_contract.json
deploy/production/deployment_compatibility.json
scripts/db_schema_contract.py
```

Reuse:

```text
scripts/sync_vds_business_to_local.py
deploy/production/update_code_only.sh
```

Create local operations runner/helper only if needed by architecture.

Update:

```text
logs/2026-09-12.md
```

Preserve received prompt.

---

# 26. FUTURE AGENT RULE

Add an explicit developer/agent rule to project documentation/instructions:

```text
If a task changes database schema/model structure,
the agent MUST:

1. regenerate schema contract;
2. set requires_manual_migration=true;
3. explain the schema diff;
4. NOT deploy that change to VDS through ordinary UPDATE;
5. prepare a separate migration stage for Owner approval.
```

The normal UPDATE button is for schema-compatible code changes only.

---

# 27. FINAL MANUAL OWNER CHECK

At the end provide browser-only steps.

LOCAL `https://localhost:8443`:

1. Login with OWNER certificate.
2. Open system operations page.
3. Verify buttons active.
4. Verify current environment = LOCAL DEV.
5. Verify schema status = SAFE.
6. Press `Синхронизировать данные с VDS`.
7. Confirm modal.
8. Observe progress.
9. Verify success/parity.
10. Press `UPDATE VDS`.
11. Verify confirmation modal.
12. CANCEL — do not unnecessarily redeploy a second time if stage already performed the deployment.
13. Confirm USER cannot see page.

VDS `https://144.31.50.134`:

1. Open same system operations page as OWNER.
2. Verify both operation buttons disabled.
3. Verify message: `Доступно только на LOCAL DEV`.
4. USER remains forbidden.

---

# 28. FINAL REPORT CONTRACT

Return:

```text
# Stage 08D-R1R5 — OWNER Operations Sync / Update / Schema Guard

## Environment
LOCAL_URL:
VDS_URL:
LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
VDS_HEAD:
CODE_PARITY:

## OWNER Operations UI
OPERATIONS_ROUTE:
OWNER_LOCAL_ACCESS:
USER_ACCESS:
VDS_ACTIONS_DISABLED:
LOCAL_SENTINEL:
PRODUCTION_SENTINEL_GUARD:

## Sync Button
SYNC_BUTTON_LOCAL_ACTIVE:
SYNC_BUTTON_VDS_DISABLED:
SYNC_DIRECTION: VDS_TO_LOCAL
FRESH_VDS_SNAPSHOT:
LOCAL_PRE_SYNC_BACKUP:
RAW_DB_MATCH:
STORAGE_TREE_MATCH:
BUSINESS_TABLE_MISMATCHES:
VDS_MUTATED_BY_SYNC:
REVERSE_SYNC_AVAILABLE: false

## Update Button
UPDATE_BUTTON_LOCAL_ACTIVE:
UPDATE_BUTTON_VDS_DISABLED:
CONFIRMATION_REQUIRED:
GIT_CLEAN_REQUIRED:
HEAD_PUSHED_REQUIRED:
PRE_UPDATE_VDS_BACKUP_REQUIRED:
DEPLOY_SCRIPT:
LOCAL_DB_UPLOAD_PATH_EXISTS: false
LOCAL_MEDIA_UPLOAD_PATH_EXISTS: false
BOOTSTRAP_RESTORE_USED: false
CODE_ONLY_DEPLOY_PROVEN:
VDS_BUSINESS_DATA_PRESERVED:

## Schema Guard
SCHEMA_CONTRACT_FILE:
LOCAL_EXPECTED_SCHEMA_SHA256:
VDS_LIVE_SCHEMA_SHA256:
SCHEMA_COMPATIBILITY:
DEPLOYMENT_COMPATIBILITY_FILE:
REQUIRES_MANUAL_MIGRATION:
NEW_TABLE_BLOCK_TEST:
NEW_COLUMN_BLOCK_TEST:
TYPE_CHANGE_BLOCK_TEST:
TRACKED_CONTRACT_DRIFT_TEST:

## Local Operations Executor
EXECUTOR_ARCHITECTURE:
ARBITRARY_COMMAND_EXECUTION: false
SSH_PRIVATE_KEY_COMMITTED: false
DOCKER_SOCKET_EXPOSED_TO_VDS: false
SINGLE_OPERATION_LOCK:
AUDIT_LOG:

## Tests
FAILED:

## VDS Safety
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
TECHNOREBOOT_STAGE08D_R1R5_OWNER_OPS_SYNC_UPDATE_SCHEMA_GUARD_READY

CODE_DIRECTION: LOCAL_TO_VDS
DATA_DIRECTION: VDS_TO_LOCAL
VDS_IS_CANONICAL_BUSINESS_DATA: true
LOCAL_BUSINESS_DATA_MUST_NEVER_OVERWRITE_VDS: true
SCHEMA_CHANGES_REQUIRE_MANUAL_MIGRATION_STAGE: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- operations can execute on VDS;
- USER can invoke operations;
- sync has any LOCAL→VDS path;
- update can upload local business data;
- schema difference does not block UPDATE;
- schema contract can drift silently;
- VDS business data changes unexpectedly;
- tests fail.

---

# 29. STOP

After implementation, deployment, fresh sync and proof:

STOP.

Wait for Owner browser acceptance.
