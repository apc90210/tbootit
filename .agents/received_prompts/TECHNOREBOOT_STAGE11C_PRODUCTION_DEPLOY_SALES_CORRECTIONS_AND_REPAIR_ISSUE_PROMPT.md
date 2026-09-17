# TECHNOREBOOT — Stage 11C PRODUCTION
## Deploy accepted Stage 11A + 11B to canonical VDS without replacing business data

Project: ТехноРебут
LOCAL workspace: C:\tbootit
Canonical production VDS: 144.31.15.88
Legacy VDS: 144.31.50.134 — DO NOT DEPLOY / DO NOT MAINTAIN

Accepted LOCAL feature commit: 9b18611
Scope: deploy accepted Stage 11A + Stage 11B to canonical production.

# 0. OWNER DECISION

Owner browser acceptance is complete.

Accepted locally:
- Stage 11A — correction of completed sales with immutable revision/audit history;
- Stage 11B — repair workflow Готов -> Выдан, payment finalization, exactly one linked repair sale, warranty/repair receipt.

Deploy these accepted changes to:
144.31.15.88

Important business-data rule:

DO NOT replace production DB with LOCAL DB.
DO NOT upload LOCAL media/business data to production.

Production DB/media remain authoritative and must be preserved.

However, Stage 11A/11B introduced NEW DATABASE SCHEMA elements.
Therefore a purely code-only deployment with zero schema change is NOT valid.

Allowed database operation in this stage:
SAFE ADDITIVE SCHEMA MIGRATION ONLY

Meaning:
- add required tables/columns/indexes/constraints;
- preserve every existing production row;
- no destructive migration;
- no DB replacement;
- no LOCAL business-data import;
- no media replacement.

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:
C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE11C_PRODUCTION_DEPLOY_SALES_CORRECTIONS_AND_REPAIR_ISSUE_PROMPT.md

to:
C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE11C_PRODUCTION_DEPLOY_SALES_CORRECTIONS_AND_REPAIR_ISSUE_PROMPT.md

# 2. PREFLIGHT — LOCAL

Record:
LOCAL_BRANCH:
LOCAL_HEAD:
LOCAL_GIT_STATUS:
EXPECTED_ACCEPTED_HEAD: 9b18611

If LOCAL HEAD contains later commits, inspect them.
Deploy only the accepted runtime changes needed for Stage 11A/11B and any required deployment tooling/docs.

Do not deploy unrelated unaccepted work.

Verify LOCAL accepted state:
- Schema Guard passes;
- targeted/system tests pass;
- no uncommitted runtime changes.

# 3. PREFLIGHT — PRODUCTION

Connect to:
root@144.31.15.88

Record:
PROD_HEAD_BEFORE:
PROD_GIT_STATUS:
PROD_6_SERVICES_HEALTHY_BEFORE:
PROD_DB_QUICK_CHECK_BEFORE:
PROD_SCHEMA_SHA_BEFORE:
PROD_PRODUCTS_BEFORE:
PROD_SALES_BEFORE:
PROD_REPAIRS_BEFORE:
PROD_PRODUCT_PHOTOS_BEFORE:
PROD_EXTERNAL_LISTINGS_BEFORE:
PROD_AVITO_POST_SALE_TASKS_BEFORE:
PROD_STORAGE_FILE_COUNT_BEFORE:

Also record:
- current gateway/mTLS state;
- current server cert validity for 144.31.15.88;
- disk free space.

STOP if production is unhealthy before deployment unless the issue is clearly unrelated and documented.

# 4. CREATE PRODUCTION SAFETY BACKUP + CHECKPOINT

Before any schema or code change:

1. Create a fresh production backup using existing TechnoReboot backup mechanism.
2. Verify:
   - manifest;
   - SHA256;
   - SQLite quick_check.
3. Create release/deployment checkpoint using existing infrastructure if available.

Required:
BACKUP_CREATED:
BACKUP_PATH:
BACKUP_SHA256:
BACKUP_MANIFEST_OK:
BACKUP_DB_QUICK_CHECK:
CHECKPOINT_CREATED:
CHECKPOINT_ID:

# 5. SCHEMA GUARD BEFORE MIGRATION

Compare current production schema to accepted Stage11A/11B schema contract.

Expected additive changes include:

Sales:
- sale_revisions table;
- sales.revision_count;
- required indexes/relations for sale revision history.

Repairs:
- final_amount;
- payment_method;
- warranty_days;
- sale_id.

Use accepted migration scripts and current schema contract as source of truth.

Inspect:
scripts/migrate_stage11a_sale_revisions.py
scripts/migrate_stage11b_repair_issue.py

Before applying:
- confirm additive/idempotent;
- confirm no DROP/DELETE/data replacement;
- confirm existing issued historical repairs do NOT get fake sales automatically.

# 6. APPLY SAFE ADDITIVE MIGRATION

Apply migrations to CURRENT production DB in place.

Absolutely forbidden:
- copying data/db/technoreboot.db from LOCAL;
- restoring LOCAL backup over production;
- replacing production media;
- resetting IDs;
- reseeding;
- deleting/recreating business tables.

After migration verify:
PRAGMA quick_check = ok
existing business counts unchanged
new columns/tables present
no historical sale revisions fabricated
no historical repair sales fabricated

Schema Guard must report SAFE / expected contract.

# 7. DEPLOY ACCEPTED CODE

Deploy accepted Stage11A/11B runtime to 144.31.15.88 using existing production update workflow.

Preferred:
backup/checkpoint already complete
-> git fetch
-> checkout/update accepted commit
-> docker compose build
-> docker compose up -d --remove-orphans

Do not touch legacy VDS.
Do not copy source tree manually if current production deployment tooling handles code-only updates safely.

# 8. PRODUCTION RUNTIME HEALTH

Verify all six production services:
- core
- admin-shell
- inventory-sales
- repairs
- avito
- gateway

Required:
- healthy/up;
- no crash loops;
- no 500/502;
- internal ports private;
- mTLS mandatory.

# 9. BUSINESS-DATA INVARIANTS AFTER DEPLOY

Compare BEFORE/AFTER:
PRODUCTS_AFTER == PRODUCTS_BEFORE
SALES_AFTER == SALES_BEFORE
REPAIRS_AFTER == REPAIRS_BEFORE
PRODUCT_PHOTOS_AFTER == PRODUCT_PHOTOS_BEFORE
EXTERNAL_LISTINGS_AFTER == EXTERNAL_LISTINGS_BEFORE
AVITO_POST_SALE_TASKS_AFTER == AVITO_POST_SALE_TASKS_BEFORE
STORAGE_FILE_COUNT_AFTER == STORAGE_FILE_COUNT_BEFORE

No new sale/repair revision should appear merely because code was deployed.

Allowed schema metadata changes do not count as business-data changes.

# 10. PRODUCTION SMOKE — READ-ONLY FIRST

Using valid OWNER client certificate verify:
https://144.31.15.88/
https://144.31.15.88/inventory/products
https://144.31.15.88/sales/
https://144.31.15.88/repairs/
https://144.31.15.88/avito/extension
https://144.31.15.88/avito/post-sale
https://144.31.15.88/help
https://144.31.15.88/help/user-manual.pdf

Verify:
- HTTP 200 where expected;
- without client cert HTTPS rejected;
- port 80 redirects to HTTPS.

# 11. FEATURE SMOKE — NO REAL BUSINESS MUTATION

Do not automatically edit/correct real production sales or issue real customer repairs just for testing.

Verify structurally/read-only:
- sales detail has correction action for eligible completed sale;
- revision history area renders;
- repair detail distinguishes Ready / Issued flow;
- issue modal/form renders;
- repair receipt route exists;
- API endpoints/routes registered.

If safe synthetic transaction test is required, use transaction rollback or isolated test data that cannot affect real reports/stock.

# 12. AVITO SAFETY

Verify:
AUTO_AVITO_DEACTIVATION_DISABLED: true

Do not enable automatic Avito actions.
Manual post-sale flow remains canonical.

# 13. OWNER BROWSER ACCEPTANCE

After deployment, tell Owner to verify via browser only:
https://144.31.15.88

Owner should confirm:
- Sales page opens;
- completed sale detail exposes Изменить продажу;
- edited-history UI is present where applicable;
- Repairs page opens;
- Ready/Issued controls are present;
- issue/payment form is available;
- receipt/warranty functionality is present.

Do NOT ask Owner to modify a real production sale unless explicitly chosen.

# 14. ROLLBACK PLAN

If runtime failure occurs:
1. stop new containers;
2. restore previous code checkpoint;
3. if schema migration itself causes failure, restore verified pre-deploy production backup;
4. restart previous stack;
5. verify counts/integrity.

Because migrations are additive, prefer code rollback without DB rollback when safe.
Never perform destructive rollback blindly.

# 15. DOCUMENTATION

Create:
reports/stage11c_production_deploy_sales_corrections_and_repair_issue_report.md

Update:
docs/production_status.md
logs/<current-date>.md

Document:
- previous prod HEAD;
- deployed HEAD;
- backup/checkpoint;
- schema before/after;
- migration result;
- business invariants;
- smoke tests;
- mTLS/Avito safety.

# 16. GIT

Commit only deployment report/docs/tooling changes that belong in repo.

Never commit:
- production DB;
- backups;
- media;
- secrets;
- private keys.

Push main if appropriate.

# 17. FINAL REPORT CONTRACT

Return:

# Stage 11C — Production Deploy Stage11A + Stage11B

## Target
PRODUCTION_VDS: 144.31.15.88
LEGACY_VDS_TOUCHED: false

## Preflight
PROD_HEAD_BEFORE:
LOCAL_ACCEPTED_HEAD:
PROD_6_SERVICES_HEALTHY_BEFORE:
PROD_DB_QUICK_CHECK_BEFORE:

## Safety
BACKUP_CREATED:
BACKUP_SHA256:
BACKUP_MANIFEST_OK:
CHECKPOINT_CREATED:
CHECKPOINT_ID:

## Schema Migration
MIGRATION_REQUIRED: true
MIGRATION_TYPE: additive_only
STAGE11A_MIGRATION_APPLIED:
STAGE11B_MIGRATION_APPLIED:
SCHEMA_GUARD_AFTER:
PROD_DB_QUICK_CHECK_AFTER:
LOCAL_DB_COPIED_TO_PROD: false
LOCAL_MEDIA_COPIED_TO_PROD: false

## Business Invariants
PRODUCTS_BEFORE:
PRODUCTS_AFTER:
SALES_BEFORE:
SALES_AFTER:
REPAIRS_BEFORE:
REPAIRS_AFTER:
PHOTOS_BEFORE:
PHOTOS_AFTER:
EXTERNAL_LISTINGS_BEFORE:
EXTERNAL_LISTINGS_AFTER:
AVITO_TASKS_BEFORE:
AVITO_TASKS_AFTER:
STORAGE_FILES_BEFORE:
STORAGE_FILES_AFTER:
BUSINESS_DATA_PRESERVED:

## Runtime
PROD_HEAD_AFTER:
PROD_6_SERVICES_HEALTHY_AFTER:
ROOT_OK:
SALES_OK:
REPAIRS_OK:
AVITO_OK:
HELP_OK:
MTLS_STILL_REQUIRED:
INTERNAL_PORTS_PRIVATE:
AUTO_AVITO_DEACTIVATION_DISABLED:

## Feature Availability
SALE_CORRECTION_ROUTE_PRESENT:
SALE_REVISION_HISTORY_PRESENT:
REPAIR_READY_ISSUED_FLOW_PRESENT:
REPAIR_PAYMENT_FORM_PRESENT:
REPAIR_RECEIPT_PRESENT:

## Owner Acceptance
OWNER_BROWSER_ACCEPTANCE: PENDING

FINAL_STATUS:
TECHNOREBOOT_STAGE11C_PRODUCTION_DEPLOY_READY_FOR_OWNER_ACCEPTANCE

# 18. STOP

STOP after production deploy + non-destructive smoke.

Do not touch legacy VDS.
Do not replace production business DB/media.
Wait for Owner browser acceptance.
