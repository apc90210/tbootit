# TECHNOREBOOT — Stage 10D-R1
## Promote new VDS as canonical production + sync current production data to LOCAL

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`

**NEW canonical production VDS:**
```text
IP: 144.31.15.88
OS: Debian 13
Provider hostname label: atanov822.serv.host
Role after this stage: PRIMARY / CANONICAL PRODUCTION
```

**OLD VDS:**
```text
IP: 144.31.50.134
Role after this stage: LEGACY / RETIRED
```

# 0. OWNER DECISION

Owner confirmed the NEW VDS `144.31.15.88` works correctly both WITH and WITHOUT Amnezia VPN.

Therefore:
```text
144.31.15.88 = canonical production server from now on
144.31.50.134 = legacy server, no routine maintenance/support
```

There is NO deployment of new code in this stage. The goal is to make the new VDS the official production source of truth and refresh LOCAL from it.

Standard workflow from now on:
```text
NEW VDS 144.31.15.88
    ↓ production business-data snapshot
LOCAL C:\tbootit
    ↓ development
LOCAL tests
    ↓ Owner browser acceptance
NEW VDS 144.31.15.88
    ↓ later production deployment stage
```

Critical invariant:
```text
Production business data sync direction:
144.31.15.88 → LOCAL only

Never:
LOCAL business DB/media → production
```

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE10D_R1_PROMOTE_NEW_VDS_AND_SYNC_PRODUCTION_TO_LOCAL_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE10D_R1_PROMOTE_NEW_VDS_AND_SYNC_PRODUCTION_TO_LOCAL_PROMPT.md`

# 2. SAFETY

Preserve all LOCAL source code and uncommitted work.

Before touching LOCAL mutable data, record:
```text
git status
git branch --show-current
git rev-parse HEAD
docker compose state
```

Create a LOCAL rollback snapshot of current mutable data.

Never commit:
- production DB;
- media;
- auth private keys;
- `.env`;
- passwords;
- backups.

Do NOT copy production SSH keys, provider config, TLS private keys, or production server secrets into LOCAL.

# 3. VERIFY NEW PRODUCTION FIRST

Connect to `144.31.15.88` using existing SSH key access if available. If it fails, ask Owner only for the required SSH access.

Verify and record:
```text
TARGET_SSH_OK
TARGET_OS
TARGET_GIT_HEAD
TARGET_6_SERVICES_HEALTHY
TARGET_DB_QUICK_CHECK
TARGET_SCHEMA_SHA
TARGET_PRODUCTS
TARGET_SALES
TARGET_REPAIRS
TARGET_PRODUCT_PHOTOS
TARGET_EXTERNAL_LISTINGS
TARGET_AVITO_POST_SALE_TASKS
TARGET_STORAGE_FILE_COUNT
TARGET_EXTENSION_VERSION
TARGET_MANUAL_PDF_SHA256
```

This server is now the sole source of truth for current production business data.
Do NOT use `144.31.50.134` as the source of current business data.

# 4. CREATE FRESH VERIFIED BACKUP ON NEW VDS

Use existing TechnoReboot backup tooling.

Create a fresh backup containing current mutable production business state:
```text
database
media/storage
required mutable business state
manifest
```

Do NOT require production TLS/private-key material for LOCAL sync.

Verify:
```text
BACKUP_CREATED
BACKUP_SHA256
BACKUP_MANIFEST_OK
BACKUP_DB_QUICK_CHECK
```

# 5. LOCAL PRE-SYNC BACKUP

Before replacing LOCAL business data, create a LOCAL safety backup of:
```text
current LOCAL DB
current LOCAL media/storage
```

Store it in the project's normal ignored backup location. Record path/hash in report, but never commit backup bytes.

# 6. SYNC NEW PRODUCTION BUSINESS DATA → LOCAL

Restore the NEW VDS production snapshot into LOCAL development data.

Sync:
```text
business database
product media/storage
business-state tables stored in DB
Avito listing/task business records stored in DB
```

Do NOT overwrite LOCAL-specific infrastructure:
```text
LOCAL server TLS certificate
LOCAL auth/private keys
LOCAL .env
LOCAL hostname/localhost settings
LOCAL Docker networking
LOCAL SSH config
LOCAL development secrets
LOCAL extension pairing/session state if environment-specific
```

If any Avito state outside the DB contains credentials/pairing tokens, preserve LOCAL state and document the exclusion.

# 7. SCHEMA GUARD

Before starting LOCAL services, compare:
```text
production snapshot schema
LOCAL code expected schema
```

There must be no destructive or implicit migration of the copied production snapshot.
If LOCAL code requires an unaccepted schema migration, STOP and report.
Otherwise continue.

# 8. START / VERIFY LOCAL

Bring LOCAL stack up normally.

Verify current modules:
```text
Core
Admin shell
Inventory / Sales
Repairs
Avito
Gateway
```

Run existing automated tests/smoke tests relevant to current runtime.

LOCAL browser/API smoke must include:
```text
/
inventory/products
sales
repairs
avito/extension
avito/post-sale
help
help/user-manual.pdf
```

Verify no 500/502.

# 9. DATA IDENTITY CHECK

Compare NEW production vs LOCAL after sync:
```text
PROD_PRODUCTS == LOCAL_PRODUCTS
PROD_SALES == LOCAL_SALES
PROD_REPAIRS == LOCAL_REPAIRS
PROD_PRODUCT_PHOTOS == LOCAL_PRODUCT_PHOTOS
PROD_EXTERNAL_LISTINGS == LOCAL_EXTERNAL_LISTINGS
PROD_AVITO_POST_SALE_TASKS == LOCAL_AVITO_POST_SALE_TASKS
PROD_STORAGE_FILE_COUNT == LOCAL_STORAGE_FILE_COUNT
PROD_SCHEMA_SHA == LOCAL_SCHEMA_SHA
LOCAL_DB_QUICK_CHECK == ok
```

Byte-identical DB hash is not required after LOCAL services start. Business counts/schema/integrity are required.

# 10. PROMOTE NEW VDS IN ACTIVE PROJECT CONFIG / DOCS

Search active repository configuration/scripts/docs for old production IP `144.31.50.134`.

Update ONLY active/current references so future production deployment/maintenance targets `144.31.15.88`.

Examples:
- current production status;
- active deployment scripts;
- active backup/verification scripts;
- active operator/developer documentation;
- current environment templates that intentionally contain production host reference.

Do NOT rewrite historical:
- old reports;
- old logs;
- completed stage records;
- forensic evidence;
- archived migration notes.

Historical documents must keep the IP that was true at that time.

Add/confirm explicit canonical state:
```text
PRIMARY_PRODUCTION_VDS=144.31.15.88
LEGACY_VDS=144.31.50.134
```

If the project already has a central deployment-host setting, update that instead of adding duplicate hard-coded constants.

# 11. OLD VDS POLICY

Do not run routine verification against `144.31.50.134`.
Do not keep it synchronized.
Do not deploy future code to it.
Do not use it as source of truth.
Do not delete it automatically.

Document:
```text
OLD_VDS_STATUS=legacy-retained
OLD_VDS_ROUTINE_SUPPORT=false
```

It may be used only if Owner explicitly requests rollback/history/recovery.

# 12. NEW STANDARD WORKFLOW

Record in current project docs:
```text
1. Production source of truth for business data:
   144.31.15.88

2. Development:
   LOCAL C:\tbootit

3. Business-data refresh:
   VDS 144.31.15.88 → LOCAL only

4. New work:
   LOCAL implementation → automated tests → Owner browser acceptance

5. Deployment:
   separate production deployment stage → 144.31.15.88

6. Never:
   LOCAL business DB/media → VDS
```

# 13. GIT

Commit only:
- prompt receipt;
- active config/script host-reference changes;
- docs/report/log updates;
- safe sync tooling if created.

Never commit production business data or secrets.
Push `main` if the commit contains only appropriate tracked changes.

# 14. REPORT

Create:
`reports/stage10d_r1_promote_new_vds_and_sync_production_to_local_report.md`

Update:
```text
docs/production_status.md
logs/<current-date>.md
```

# 15. FINAL CONTRACT

Return:
```text
# Stage 10D-R1 — Promote New VDS + Sync Production to LOCAL

## Canonical Production
PRIMARY_PRODUCTION_VDS: 144.31.15.88
PRIMARY_PRODUCTION_HEALTHY:
PRIMARY_PRODUCTION_GIT_HEAD:
PRIMARY_PRODUCTION_DB_QUICK_CHECK:

## Legacy
LEGACY_VDS: 144.31.50.134
LEGACY_VDS_ROUTINE_SUPPORT: false
LEGACY_VDS_MODIFIED: false

## Fresh Production Snapshot
BACKUP_CREATED:
BACKUP_SHA256:
BACKUP_MANIFEST_OK:

## LOCAL Safety
LOCAL_PRE_SYNC_BACKUP_CREATED:
LOCAL_PRE_SYNC_BACKUP_PATH:
LOCAL_CODE_UNCOMMITTED_WORK_PRESERVED:

## Production -> LOCAL Sync
PROD_PRODUCTS:
LOCAL_PRODUCTS:
PROD_SALES:
LOCAL_SALES:
PROD_REPAIRS:
LOCAL_REPAIRS:
PROD_PRODUCT_PHOTOS:
LOCAL_PRODUCT_PHOTOS:
PROD_EXTERNAL_LISTINGS:
LOCAL_EXTERNAL_LISTINGS:
PROD_AVITO_POST_SALE_TASKS:
LOCAL_AVITO_POST_SALE_TASKS:
PROD_STORAGE_FILE_COUNT:
LOCAL_STORAGE_FILE_COUNT:
SCHEMA_MATCH:
LOCAL_DB_QUICK_CHECK:
DATA_SYNC_MATCH:

## LOCAL Runtime
LOCAL_6_SERVICES_HEALTHY:
LOCAL_ROOT_OK:
LOCAL_PRODUCTS_OK:
LOCAL_SALES_OK:
LOCAL_REPAIRS_OK:
LOCAL_AVITO_EXTENSION_OK:
LOCAL_AVITO_POST_SALE_OK:
LOCAL_HELP_OK:
LOCAL_USER_MANUAL_OK:

## Project Target Update
ACTIVE_DEPLOYMENT_TARGET: 144.31.15.88
OLD_IP_REMOVED_FROM_ACTIVE_TARGETS:
HISTORICAL_RECORDS_PRESERVED:

## Workflow
PRODUCTION_SOURCE_OF_TRUTH: 144.31.15.88
BUSINESS_SYNC_DIRECTION: VDS_TO_LOCAL_ONLY
FUTURE_DEPLOY_TARGET: 144.31.15.88

FINAL_STATUS:
TECHNOREBOOT_STAGE10D_R1_NEW_VDS_CANONICAL_LOCAL_SYNC_COMPLETE
```

# 16. STOP

STOP after:
- new VDS is documented as canonical;
- production business data is synchronized to LOCAL;
- LOCAL runtime is healthy;
- active deployment target points to `144.31.15.88`.

Do NOT deploy any new LOCAL code to production in this stage.
Do NOT modify the old VDS.
