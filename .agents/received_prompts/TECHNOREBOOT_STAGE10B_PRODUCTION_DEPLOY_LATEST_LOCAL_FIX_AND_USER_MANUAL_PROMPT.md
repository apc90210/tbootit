# TECHNOREBOOT — Stage 10B PRODUCTION
## Deploy latest accepted LOCAL fix + User Manual to VDS (code-only)

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`  
**Production VDS:** `144.31.50.134`  
**Production URL:** `https://144.31.50.134`  
**Stage:** `Stage 10B — Production deploy latest accepted LOCAL state`

# 0. OWNER AUTHORIZATION

Owner explicitly authorizes deployment of the latest accepted LOCAL state to production now.

This deployment must include:
- the latest accepted Avito/manual-flow fixes already present in LOCAL;
- current Chrome Extension package/version;
- Stage10A User Manual PDF;
- permanent `📘 Инструкция` link in the unified top navigation;
- `/help`;
- `/help/user-manual.pdf`.

This is a **code/artifact-only production deployment**.

The production DB schema was already migrated successfully in Stage09C.
Do NOT run any new DB migration unless preflight proves it is unexpectedly required.

Do NOT copy LOCAL business DB/media/auth to VDS.

---

# 1. PROMPT PRESERVATION

Copy unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE10B_PRODUCTION_DEPLOY_LATEST_LOCAL_FIX_AND_USER_MANUAL_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE10B_PRODUCTION_DEPLOY_LATEST_LOCAL_FIX_AND_USER_MANUAL_PROMPT.md`

---

# 2. LOCAL PREFLIGHT

Record:

```text
LOCAL_HEAD:
LOCAL_BRANCH:
LOCAL_GIT_STATUS:
ORIGIN_MAIN_HEAD:
EXTENSION_VERSION:
USER_MANUAL_PDF_EXISTS:
USER_MANUAL_PDF_SHA256:
USER_MANUAL_PDF_SIZE:
```

Expected accepted LOCAL state:
- User Manual Stage10A accepted by Owner;
- PDF exists at current configured static path;
- extension currently expected around `0.2.62`, but discover actual version from `manifest.json`;
- worktree should be clean.

If latest LOCAL commit is not pushed to `origin/main`, push it before deployment.

Do not deploy uncommitted code.

---

# 3. PRODUCTION PREFLIGHT

Before any production change record:

```text
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
```

Discover actual table names rather than assuming.

Required:
- current production healthy;
- Stage09C schema already compatible;
- `deployment_compatibility.json` allows code-only deploy.

If Schema Guard says migration required:
- STOP;
- do NOT deploy;
- return BLOCKED.

---

# 4. RELEASE CHECKPOINT / BACKUP

Use existing production checkpoint/rollback infrastructure.

Create a fresh release checkpoint before deploy.

Required:

```text
RELEASE_CHECKPOINT_CREATED: true
PREVIOUS_HEAD_RECORDED:
PREVIOUS_IMAGE_IDS_RECORDED:
DB_BACKUP_CREATED: true
DB_BACKUP_QUICK_CHECK: ok
DB_BACKUP_SHA256:
```

Do not continue if checkpoint/backup fails.

---

# 5. DEPLOY EXACT LATEST LOCAL CANDIDATE

Deploy exact accepted LOCAL commit.

Preferred:
- `origin/main` must point to the accepted candidate;
- production checkout updated to exact candidate;
- run existing code-only UPDATE/deploy infrastructure;
- preserve production data volumes.

Strictly forbidden:

```text
copy LOCAL technoreboot.db to VDS
copy LOCAL storage/media to VDS
copy LOCAL auth to VDS
copy LOCAL Avito mutable state to VDS
run schema migration unnecessarily
```

Required:

```text
VDS_HEAD_AFTER == LOCAL_HEAD
```

---

# 6. CONTAINER DEPLOYMENT

Rebuild/recreate only required application containers.

Preserve:
- production DB;
- media/storage;
- auth;
- existing production mutable state.

All six production services must become healthy.

Record:

```text
LIVE_6_SERVICES_HEALTHY_AFTER:
LIVE_CONTAINER_IDS_AFTER:
LIVE_IMAGE_IDS_AFTER:
```

---

# 7. REQUIRED PRODUCTION SMOKE TESTS

Using OWNER mTLS, verify:

```text
/
inventory/products
sales
repairs
reports route if available
/avito/extension
/avito/extension/download
/avito/post-sale
/help
/help/user-manual.pdf
```

Expected:
- HTTP 200 where applicable;
- no 500/502;
- extension page shows current deployed version;
- extension download works;
- User Manual PDF downloads successfully.

For PDF endpoint verify:

```text
Content-Type: application/pdf
Content-Disposition: attachment
bytes start with %PDF
served SHA256 == LOCAL PDF SHA256
```

Verify `/help` includes:
- `Руководство пользователя`;
- download link.

Verify unified nav includes:

```text
📘 Инструкция
```

from at least:
- main/admin shell;
- inventory/sales;
- repairs.

---

# 8. USER MANUAL PRODUCTION VERIFICATION

Verify on production:

```text
MANUAL_ROUTE: /help/user-manual.pdf
PDF_DOWNLOAD_OK: true
PDF_SHA_MATCH_LOCAL: true
PDF_PAGE_COUNT: expected current LOCAL value
CLICKABLE_TOC_ARTIFACT_PRESENT: true
```

Do not regenerate PDF on VDS if artifact is already tracked and identical.
Deploy the exact accepted LOCAL PDF.

---

# 9. AVITO / SALES UX PRESENCE

Verify only UI presence and routes; do not create fake production sales.

Required current behavior present in code/templates:
- `Снять с Avito вручную`;
- `Не снимать`;
- optional `Я снял объявление`;
- no automatic Avito DOM deactivation.

Do not trigger real external Avito action during smoke.

---

# 10. DATA INTEGRITY AFTER DEPLOY

Recompute:

```text
LIVE_DB_SHA256_AFTER:
LIVE_DB_SCHEMA_SHA_AFTER:
LIVE_DB_QUICK_CHECK_AFTER:
PRODUCTS_AFTER:
SALES_AFTER:
PRODUCT_PHOTOS_AFTER:
PRODUCT_EXTERNAL_LISTINGS_AFTER:
REPAIRS_AFTER:
AVITO_POST_SALE_TASKS_AFTER:
PROD_STORAGE_FILE_COUNT_AFTER:
PROD_AUTH_CA_SHA256_AFTER:
```

Since this is code-only:

```text
LIVE_DB_SCHEMA_SHA_AFTER == LIVE_DB_SCHEMA_SHA_BEFORE
PRODUCTS_AFTER == PRODUCTS_BEFORE
SALES_AFTER == SALES_BEFORE
PRODUCT_PHOTOS_AFTER == PRODUCT_PHOTOS_BEFORE
PRODUCT_EXTERNAL_LISTINGS_AFTER == PRODUCT_EXTERNAL_LISTINGS_BEFORE
REPAIRS_AFTER == REPAIRS_BEFORE
PROD_STORAGE_FILE_COUNT_AFTER == PROD_STORAGE_FILE_COUNT_BEFORE
PROD_AUTH_CA_SHA256_AFTER == PROD_AUTH_CA_SHA256_BEFORE
```

DB file SHA may change from normal live writes during the window; if it changes, explain and prove business/schema invariants. Do not require byte equality if production is active.

---

# 11. FAILURE / ROLLBACK

If deploy or smoke fails:

- automatically rollback CODE to previous checkpoint;
- restore previous images/runtime;
- do NOT restore DB unless explicitly required;
- do NOT perform schema changes;
- verify production healthy after rollback.

Return BLOCKED.

---

# 12. DOCUMENTATION

Update locally:

```text
reports/stage10b_production_deploy_latest_fix_and_manual_report.md
docs/production_status.md
logs/2026-09-14.md
```

Record:
- deployed commit;
- extension version;
- manual PDF hash;
- smoke results;
- data integrity;
- rollback status.

---

# 13. GIT

After deployment documentation:
- commit report/docs locally;
- push `origin/main` if appropriate;
- do not include secrets.

Report:

```text
DEPLOYED_CODE_HEAD:
DOCUMENTATION_COMMIT:
ORIGIN_MAIN_HEAD_AFTER:
FINAL_LOCAL_GIT_STATUS:
```

Note:
It is acceptable for VDS runtime HEAD to equal the deployed code commit while `origin/main` later advances by one documentation-only commit.

---

# 14. FINAL REPORT CONTRACT

Return:

```text
# Stage 10B — Production Deploy Latest Fix + User Manual

## Candidate
LOCAL_HEAD:
DEPLOYED_CODE_HEAD:
VDS_HEAD_AFTER:
VDS_HEAD_MATCHES_DEPLOYED_CODE:
EXTENSION_VERSION:
LOCAL_MANUAL_PDF_SHA256:

## Backup
RELEASE_CHECKPOINT_CREATED:
DB_BACKUP_CREATED:
DB_BACKUP_SHA256:
DB_BACKUP_QUICK_CHECK:

## Production Smoke
ROOT_OK:
PRODUCTS_OK:
SALES_OK:
REPAIRS_OK:
AVITO_EXTENSION_PAGE_OK:
AVITO_EXTENSION_DOWNLOAD_OK:
AVITO_POST_SALE_PAGE_OK:
HELP_PAGE_OK:
USER_MANUAL_DOWNLOAD_OK:
USER_MANUAL_PDF_SHA_MATCH:
TOP_NAV_INSTRUCTION_LINK_OK:
MANUAL_AVITO_FLOW_PRESENT:

## Runtime
LIVE_6_SERVICES_HEALTHY_AFTER:
AUTO_CODE_ROLLBACK_PERFORMED:

## Data Integrity
LIVE_DB_SCHEMA_SHA_BEFORE:
LIVE_DB_SCHEMA_SHA_AFTER:
SCHEMA_UNCHANGED:
PRODUCTS_BEFORE:
PRODUCTS_AFTER:
SALES_BEFORE:
SALES_AFTER:
PRODUCT_PHOTOS_BEFORE:
PRODUCT_PHOTOS_AFTER:
PRODUCT_EXTERNAL_LISTINGS_BEFORE:
PRODUCT_EXTERNAL_LISTINGS_AFTER:
REPAIRS_BEFORE:
REPAIRS_AFTER:
AVITO_POST_SALE_TASKS_BEFORE:
AVITO_POST_SALE_TASKS_AFTER:
PROD_STORAGE_UNCHANGED:
PROD_AUTH_CA_UNCHANGED:
PRODUCTION_BUSINESS_DATA_OVERWRITTEN: false

## Git
DOCUMENTATION_COMMIT:
ORIGIN_MAIN_HEAD_AFTER:
FINAL_LOCAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE10B_PRODUCTION_DEPLOYMENT_SUCCESS

READY_FOR_OWNER_BROWSER_ACCEPTANCE:
true
```

Return BLOCKED if:
- Schema Guard requires migration;
- backup/checkpoint fails;
- VDS HEAD mismatch;
- any critical smoke test fails;
- PDF hash mismatches;
- business-data counts unexpectedly change;
- production does not return healthy after deploy/rollback.

---

# 15. STOP

After successful deployment and verification:

STOP.

Do not start another feature.

Wait for Owner acceptance.
