# TECHNOREBOOT — Stage 09C PRODUCTION
## Safe production schema migration + code-only deployment to VDS

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`  
**Production VDS:** `144.31.50.134`  
**Production URL:** `https://144.31.50.134`  
**Stage:** `Stage 09C — Production Migration + Code Deploy`

# 0. OWNER AUTHORIZATION

Owner authorizes the real production deployment now.

This stage must:
1. create a production backup/release checkpoint;
2. migrate the LIVE production DB schema safely;
3. deploy the currently accepted code to VDS;
4. preserve all production business data;
5. verify runtime and business invariants;
6. rollback code automatically if deployment fails;
7. STOP for Owner browser acceptance.

This is a REAL production change.

---

# 1. PROMPT PRESERVATION

Copy unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE09C_PRODUCTION_SCHEMA_MIGRATION_AND_CODE_DEPLOY_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE09C_PRODUCTION_SCHEMA_MIGRATION_AND_CODE_DEPLOY_PROMPT.md`

---

# 2. ACCEPTED INPUT STATE

Use the currently accepted candidate from LOCAL.

Current known accepted facts:

```text
Stage09B isolated VDS compatibility test: PASSED
Production runtime was NOT updated during Stage09B
Production DB was NOT modified during Stage09B
Extension current accepted version: 0.2.62
```

The current production VDS still runs the older production commit.

Do NOT guess the candidate commit. Resolve it from LOCAL at stage start and record:

```text
LOCAL_HEAD:
LOCAL_BRANCH:
LOCAL_GIT_STATUS:
ORIGIN_MAIN_HEAD:
CANDIDATE_HEAD:
```

If LOCAL has uncommitted changes:
- do not discard them;
- inspect and stop if they affect the deploy candidate unexpectedly.

---

# 3. ABSOLUTE DATA SAFETY RULES

NEVER upload/replace LOCAL business data on VDS.

Forbidden:

```text
copy LOCAL technoreboot.db to VDS
copy LOCAL media/storage to VDS
copy LOCAL auth to VDS
copy LOCAL Avito mutable state to VDS
restore production DB from LOCAL
```

Production business data source remains the existing VDS database.

Allowed:

```text
schema-only migration on LIVE production DB
code-only deployment
container rebuild/recreate
```

---

# 4. PRODUCTION PREFLIGHT

Before any write:

## Git/runtime

Record:

```text
VDS_HEAD_BEFORE:
VDS_GIT_STATUS_BEFORE:
LIVE_CONTAINER_IDS_BEFORE:
LIVE_IMAGE_IDS_BEFORE:
LIVE_6_SERVICES_HEALTHY_BEFORE:
LIVE_HTTPS_STATUS_BEFORE:
```

Expected services:

```text
gateway
core
admin-shell
inventory-sales-module
repairs-module
avito-module
```

## DB state

Record:

```text
LIVE_DB_PATH:
LIVE_DB_SHA256_BEFORE:
LIVE_DB_SIZE_BEFORE:
LIVE_DB_SCHEMA_SHA_BEFORE:
LIVE_DB_QUICK_CHECK_BEFORE:
```

Record business counts using actual canonical table names discovered on VDS:

```text
PRODUCTS_BEFORE:
SALES_BEFORE:
PRODUCT_PHOTOS_BEFORE:
PRODUCT_EXTERNAL_LISTINGS_BEFORE:
REPAIRS_OR_REPAIR_RECORDS_BEFORE:
AVITO_POST_SALE_TASKS_BEFORE:
```

If `avito_post_sale_tasks` is absent, report `TABLE_ABSENT`.

Do not fail merely because optional modules/tables are absent; inspect actual schema.

---

# 5. RELEASE CHECKPOINT + BACKUP

Before migration or code deployment, create a release checkpoint using the existing Stage08D-R1R6 infrastructure.

Checkpoint must include:

```text
previous VDS git HEAD
previous image IDs
current schema hash
production DB backup
production storage/auth manifest
timestamp
```

Create a verified SQLite backup of the live production DB.

Required:

```text
DB_BACKUP_CREATED: true
DB_BACKUP_QUICK_CHECK: ok
DB_BACKUP_SHA256:
RELEASE_CHECKPOINT_CREATED: true
```

Do NOT continue if backup/checkpoint fails.

---

# 6. SCHEMA MIGRATION — LIVE PRODUCTION DB

This is the only intended production DB change.

Required migration:

Create table if absent:

```sql
avito_post_sale_tasks
```

with the schema currently required by accepted LOCAL code.

Expected columns include at least:

```text
id
sale_id
product_id
external_listing_id
avito_listing_id
listing_url
status
action
requested_by
requested_at
started_at
finished_at
attempt_count
last_error
execution_mode
result_metadata
```

Expected uniqueness:

```text
(sale_id, product_id, avito_listing_id, action)
```

Expected indexes:
- id
- sale_id
- product_id
- external_listing_id
- avito_listing_id
- status

IMPORTANT:
- derive exact schema from current LOCAL models/schema contract;
- do not invent columns if current code differs;
- use `CREATE TABLE IF NOT EXISTS` / safe idempotent migration;
- do not alter unrelated tables;
- do not rewrite existing business rows.

After migration record:

```text
LIVE_DB_SCHEMA_SHA_AFTER_MIGRATION:
AVITO_POST_SALE_TASKS_EXISTS:
AVITO_POST_SALE_TASKS_ROWS:
```

Expected initial rows on production:

```text
0
```

unless production already legitimately has rows.

Run:

```text
PRAGMA quick_check;
```

Must return `ok`.

---

# 7. BUSINESS DATA INVARIANTS AFTER MIGRATION

Immediately after schema migration verify:

```text
PRODUCTS_AFTER_MIGRATION == PRODUCTS_BEFORE
SALES_AFTER_MIGRATION == SALES_BEFORE
PRODUCT_PHOTOS_AFTER_MIGRATION == PRODUCT_PHOTOS_BEFORE
PRODUCT_EXTERNAL_LISTINGS_AFTER_MIGRATION == PRODUCT_EXTERNAL_LISTINGS_BEFORE
REPAIRS_AFTER_MIGRATION == REPAIRS_BEFORE
```

Production DB SHA is expected to change because schema changed.

Therefore the invariant is:

```text
business row counts unchanged
existing business records unchanged
only schema addition accepted
```

Do not compare final DB SHA to pre-migration SHA as equality requirement.

---

# 8. SCHEMA GUARD

After live migration, run the current schema compatibility guard against production.

Required:

```text
SCHEMA_GUARD_AFTER_MIGRATION: PASS
DEPLOYMENT_COMPATIBLE: true
```

If Schema Guard fails:
- STOP deployment;
- do not update production code;
- leave production runtime on old code;
- report exact mismatch.

Do NOT attempt broad DB repair.

---

# 9. CODE DEPLOYMENT

Deploy the accepted candidate commit only after Schema Guard passes.

Preferred sequence:

```text
fetch exact candidate commit
checkout/update production code to exact candidate
build images
recreate only application containers as required
preserve production data volumes
```

Do not replace production data root.

Record:

```text
VDS_HEAD_AFTER_DEPLOY:
```

Required:

```text
VDS_HEAD_AFTER_DEPLOY == CANDIDATE_HEAD
```

---

# 10. CODE-ONLY UPDATE / CONTAINER SAFETY

Use the existing code-only deployment/update infrastructure where appropriate.

Must preserve:
- production DB volume/path;
- storage;
- auth;
- Avito mutable state.

Do not mount LOCAL data.

Rebuild/recreate only production application containers.

Record new container IDs and image IDs.

---

# 11. AUTOMATIC ROLLBACK ON DEPLOY FAILURE

If candidate containers fail health checks or core smoke tests:

1. rollback code to previous release checkpoint;
2. restore previous image references/build;
3. recreate previous application runtime;
4. DO NOT restore DB automatically;
5. DO NOT remove the newly added schema table unless specifically proven necessary.

Reason:
- schema migration is additive and compatible;
- automatic DB rollback is more dangerous than leaving additive schema in place.

Report:

```text
AUTO_CODE_ROLLBACK_PERFORMED:
```

If rollback occurs, final status must be `BLOCKED`.

---

# 12. PRODUCTION HEALTH CHECK

All 6 services must be healthy after deployment.

Record:

```text
LIVE_6_SERVICES_HEALTHY_AFTER:
```

Verify public HTTPS:

```text
https://144.31.50.134
```

with OWNER mTLS.

Expected:
- HTTP 200 on shell/root;
- no gateway errors;
- no restart loop.

---

# 13. PRODUCTION SMOKE TEST

Smoke at minimum:

```text
/
products list / inventory page
sales page
sales detail route if an existing sale exists
/avito/extension
/avito/extension/download
/avito/post-sale
repairs module route
backup/owner operations route if applicable
```

Verify extension page shows:

```text
v0.2.62
```

Verify ZIP download hash matches accepted LOCAL artifact.

Do NOT perform a real Avito removal in this deployment stage.

---

# 14. MANUAL AVITO FLOW — SERVER-SIDE PRESENCE

Verify only the UI/runtime presence of the accepted manual flow:

```text
after sale / sale detail:
[ Снять с Avito вручную ]

optional:
[ Я снял объявление ]

cancel:
[ Не снимать ]
```

Do not create artificial production sales merely for this smoke test.

If production currently has zero sales, it is acceptable to verify:
- route/template presence;
- queue route;
- backend endpoints;
- no runtime errors.

Owner will perform browser acceptance separately.

---

# 15. BUSINESS DATA POST-DEPLOYMENT PROOF

Recompute counts:

```text
PRODUCTS_AFTER:
SALES_AFTER:
PRODUCT_PHOTOS_AFTER:
PRODUCT_EXTERNAL_LISTINGS_AFTER:
REPAIRS_AFTER:
AVITO_POST_SALE_TASKS_AFTER:
```

Required:

```text
PRODUCTS_AFTER == PRODUCTS_BEFORE
SALES_AFTER == SALES_BEFORE
PRODUCT_PHOTOS_AFTER == PRODUCT_PHOTOS_BEFORE
PRODUCT_EXTERNAL_LISTINGS_AFTER == PRODUCT_EXTERNAL_LISTINGS_BEFORE
REPAIRS_AFTER == REPAIRS_BEFORE
```

For the new table:

```text
AVITO_POST_SALE_TASKS_AFTER >= 0
```

No synthetic production rows should be created by deployment smoke tests.

Also verify:
- storage file count unchanged;
- auth CA hash unchanged.

---

# 16. EXTENSION ARTIFACT IDENTITY

Compare:

```text
LOCAL extension ZIP SHA256
VDS served extension ZIP SHA256
```

Required:

```text
EXTENSION_ZIP_HASH_MATCH: true
EXTENSION_VERSION: 0.2.62
```

---

# 17. PRODUCTION CHECKPOINT RETENTION

Preserve the prior release checkpoint according to existing retention policy.

Do not delete the previous known-good checkpoint immediately after deploy.

---

# 18. DOCUMENTATION

Update locally:

```text
reports/stage09c_production_schema_migration_and_code_deploy_report.md
docs/production_status.md
logs/2026-09-14.md
```

State clearly:
- production schema migrated;
- production code deployed;
- business data preserved;
- extension version deployed;
- rollback checkpoint retained.

---

# 19. GIT

If required, push the accepted deployment commit/branch.

Do not include production secrets or mutable VDS data.

Record:

```text
CANDIDATE_HEAD:
ORIGIN_MAIN_HEAD_AFTER:
VDS_HEAD_AFTER:
LOCAL_FINAL_GIT_STATUS:
```

---

# 20. FINAL REPORT CONTRACT

Return:

```text
# Stage 09C — Production Schema Migration + Code Deploy

## Candidate
LOCAL_HEAD:
CANDIDATE_HEAD:
EXTENSION_VERSION: 0.2.62
LOCAL_EXTENSION_ZIP_SHA256:

## Production Before
VDS_HEAD_BEFORE:
LIVE_6_SERVICES_HEALTHY_BEFORE:
LIVE_CONTAINER_IDS_BEFORE:
LIVE_IMAGE_IDS_BEFORE:
LIVE_DB_SHA256_BEFORE:
LIVE_DB_SCHEMA_SHA_BEFORE:
LIVE_DB_QUICK_CHECK_BEFORE:
PRODUCTS_BEFORE:
SALES_BEFORE:
PRODUCT_PHOTOS_BEFORE:
PRODUCT_EXTERNAL_LISTINGS_BEFORE:
REPAIRS_BEFORE:
AVITO_POST_SALE_TASKS_BEFORE:
PROD_STORAGE_FILE_COUNT_BEFORE:
PROD_AUTH_CA_SHA256_BEFORE:

## Backup / Checkpoint
RELEASE_CHECKPOINT_CREATED:
DB_BACKUP_CREATED:
DB_BACKUP_SHA256:
DB_BACKUP_QUICK_CHECK:
PREVIOUS_HEAD_RECORDED:
PREVIOUS_IMAGE_IDS_RECORDED:

## Migration
MIGRATION_APPLIED:
AVITO_POST_SALE_TASKS_EXISTS:
AVITO_POST_SALE_TASKS_ROWS_AFTER_MIGRATION:
LIVE_DB_SCHEMA_SHA_AFTER_MIGRATION:
LIVE_DB_QUICK_CHECK_AFTER_MIGRATION:
BUSINESS_COUNTS_UNCHANGED_AFTER_MIGRATION:

## Schema Guard
SCHEMA_GUARD_AFTER_MIGRATION:
DEPLOYMENT_COMPATIBLE:

## Deployment
VDS_HEAD_AFTER:
VDS_HEAD_MATCHES_CANDIDATE:
LIVE_6_SERVICES_HEALTHY_AFTER:
LIVE_CONTAINER_IDS_AFTER:
LIVE_IMAGE_IDS_AFTER:
AUTO_CODE_ROLLBACK_PERFORMED:

## Smoke
ROOT_OK:
PRODUCTS_OK:
SALES_OK:
AVITO_EXTENSION_PAGE_OK:
AVITO_EXTENSION_DOWNLOAD_OK:
AVITO_POST_SALE_PAGE_OK:
REPAIRS_OK:
MANUAL_AVITO_FLOW_PRESENT:
EXTENSION_ZIP_HASH_MATCH:

## Production Data After
PRODUCTS_AFTER:
SALES_AFTER:
PRODUCT_PHOTOS_AFTER:
PRODUCT_EXTERNAL_LISTINGS_AFTER:
REPAIRS_AFTER:
AVITO_POST_SALE_TASKS_AFTER:
BUSINESS_DATA_COUNTS_UNCHANGED:
PROD_STORAGE_FILE_COUNT_AFTER:
PROD_STORAGE_UNCHANGED:
PROD_AUTH_CA_SHA256_AFTER:
PROD_AUTH_CA_UNCHANGED:

## Safety
LOCAL_DB_UPLOADED_TO_VDS: false
LOCAL_MEDIA_UPLOADED_TO_VDS: false
LOCAL_AUTH_UPLOADED_TO_VDS: false
PRODUCTION_BUSINESS_DATA_OVERWRITTEN: false

## Git
ORIGIN_MAIN_HEAD_AFTER:
LOCAL_FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE09C_PRODUCTION_DEPLOYMENT_SUCCESS

READY_FOR_OWNER_BROWSER_ACCEPTANCE:
true
```

Return BLOCKED if:
- backup/checkpoint fails;
- Schema Guard fails;
- candidate HEAD mismatch;
- any business-data count unexpectedly changes;
- production containers fail health checks;
- extension artifact mismatch;
- rollback is required.

---

# 21. STOP

After successful production migration + deployment:

STOP.

Do not perform additional features or data sync.

Wait for Owner browser acceptance.
