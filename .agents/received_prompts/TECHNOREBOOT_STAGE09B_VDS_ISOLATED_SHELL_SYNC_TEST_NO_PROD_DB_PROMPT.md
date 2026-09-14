# TECHNOREBOOT — Stage 09B
## Isolated VDS sync test of the updated shell/runtime — ZERO production DB modification

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`  
**Production VDS:** `144.31.50.134`  
**Production URL:** `https://144.31.50.134`  
**Stage:** `Stage 09B — VDS Isolated Shell Sync Test / No Production DB Touch`

# 0. OWNER GOAL

Test that the currently updated LOCAL code/shell can be synchronized to and run on the production VDS host **without touching the real production business database**.

This is NOT the final production deployment.

Required principle:

```text
LOCAL candidate
↓
temporary isolated test release on the VDS host
↓
run updated containers against a disposable COPY of production data
↓
verify UI/runtime/extension package
↓
prove live production DB and live production containers were untouched
↓
tear down isolated test stack
```

Do NOT perform normal `UPDATE VDS`.
Do NOT migrate the real production DB.
Do NOT restart/recreate live production services.

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE09B_VDS_ISOLATED_SHELL_SYNC_TEST_NO_PROD_DB_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE09B_VDS_ISOLATED_SHELL_SYNC_TEST_NO_PROD_DB_PROMPT.md`

# 2. CURRENT CONTEXT

Current LOCAL development contains Stage09A changes and the latest extension/shell fixes.

Schema Guard is expected to indicate:

```text
requires_manual_migration = true
database_change = true
```

Therefore:

```text
FULL PRODUCTION UPDATE IS FORBIDDEN IN THIS STAGE
```

If the isolated test copy requires the new schema, migration may be applied ONLY to the disposable test DB copy.

Never to the live production DB.

# 3. PREFLIGHT — LOCAL

Record:

```text
LOCAL_HEAD:
LOCAL_BRANCH:
LOCAL_GIT_STATUS:
ORIGIN_MAIN_HEAD:
DEPLOYMENT_COMPATIBILITY_REQUIRES_MIGRATION:
SCHEMA_CONTRACT_SHA:
EXTENSION_VERSION:
EXTENSION_ZIP_SHA256:
```

Run:

```text
docker compose ps
```

Required:
- LOCAL stack healthy;
- current candidate commit identified;
- no accidental mutable business-data files prepared for transfer.

If current LOCAL commit is not available remotely, push a dedicated temporary branch, e.g.:

```text
stage09b-vds-sync-test-<shortsha>
```

Do NOT move production to `origin/main` merely for this test.

# 4. PREFLIGHT — LIVE PRODUCTION VDS

Before creating any test stack, record the live production state.

## Runtime

```text
VDS_LIVE_HEAD:
VDS_LIVE_CONTAINER_IDS:
VDS_LIVE_IMAGE_IDS:
VDS_LIVE_6_SERVICES_HEALTHY:
VDS_LIVE_HTTPS_STATUS:
```

Expected live services:

```text
gateway
core
admin-shell
inventory-sales-module
repairs-module
avito-module
```

## Live DB fingerprint

Record BEFORE:

```text
LIVE_DB_PATH:
LIVE_DB_SHA256_BEFORE:
LIVE_DB_SIZE_BEFORE:
LIVE_DB_SCHEMA_SHA_BEFORE:
LIVE_DB_QUICK_CHECK_BEFORE:
PRODUCTS_BEFORE:
SALES_BEFORE:
REPAIRS_BEFORE:
PHOTOS_BEFORE:
EXTERNAL_LISTINGS_BEFORE:
AVITO_POST_SALE_TASKS_BEFORE:
```

If `avito_post_sale_tasks` does not exist, record:

```text
AVITO_POST_SALE_TASKS_BEFORE: TABLE_ABSENT
```

## Mutable data proof

Record:

```text
PROD_STORAGE_FILE_COUNT_BEFORE:
PROD_AUTH_CA_SHA256_BEFORE:
```

# 5. HARD SAFETY RULES

During this stage:

```text
LIVE_PROD_DB_WRITE = forbidden
LIVE_PROD_SCHEMA_CHANGE = forbidden
LIVE_PROD_DB_MIGRATION = forbidden
LIVE_PROD_MEDIA_WRITE = forbidden
LIVE_PROD_AUTH_WRITE = forbidden
LIVE_PROD_AVITO_STATE_WRITE = forbidden
LIVE_PROD_CONTAINER_RESTART = forbidden
LIVE_PROD_CONTAINER_RECREATE = forbidden
UPDATE_VDS = forbidden
```

Do not run:

```text
deploy/production/update_code_only.sh
```

Do not use the production UPDATE button.
Do not change firewall rules.
Do not expose the isolated test stack publicly on 80/443.

# 6. CREATE AN ISOLATED VDS TEST RELEASE

Create a temporary isolated release area outside the live app/runtime, for example:

```text
/srv/technoreboot-sync-test/<shortsha>/
```

Fetch/checkout the exact LOCAL candidate commit using a separate clone or Git worktree.

Record:

```text
TEST_RELEASE_HEAD:
```

It must equal the LOCAL candidate HEAD.

Do not change the live production checkout if avoidable.

# 7. CREATE A DISPOSABLE TEST DATA ROOT

Create an isolated data root, for example:

```text
/srv/technoreboot-sync-test/<shortsha>/test-data/
```

The test runtime must NOT mount the real writable production DB.

Create a consistent disposable DB copy using a safe read-only backup/copy mechanism such as:
- SQLite backup API;
- `sqlite3 .backup`;
- equivalent transactionally safe method.

Do NOT stop production for the copy.

Record:

```text
TEST_DB_SOURCE_SHA_REFERENCE:
TEST_DB_SHA256_INITIAL:
```

If the candidate requires the Stage09A schema:
- apply migration/schema initialization ONLY to the disposable test DB;
- record exact test-copy schema changes;
- immediately verify the live production DB hash remains unchanged.

Media:
- prefer read-only mount;
- or copy only what the isolated test needs.

Auth:
- use a disposable copy if mTLS is required;
- never modify live `/srv/technoreboot/data/auth`.

Avito:
- do not execute real publish/remove actions from this isolated test stack.

# 8. ISOLATED COMPOSE PROJECT

Run a separate Compose project such as:

```text
technoreboot-sync-test-<shortsha>
```

Requirements:
- separate project namespace;
- separate containers;
- separate network;
- isolated test data root;
- zero writable mounts to live production DB/media/auth;
- no container-name collisions;
- no ports 80/443.

Expose the test gateway only on loopback high port, for example:

```text
127.0.0.1:18443
```

Use another high port if occupied.

Do NOT open it in nftables.

# 9. BUILD AND START UPDATED RELEASE

Build candidate images on the VDS host from the exact test release commit.

Record:

```text
TEST_CONTAINER_IDS:
TEST_IMAGE_IDS:
TEST_6_SERVICES_HEALTHY:
```

If candidate startup requires schema migration:
- migrate ONLY the disposable test DB;
- restart ONLY isolated test services.

# 10. CODE IDENTITY PROOF

Prove:

```text
LOCAL_HEAD == TEST_RELEASE_HEAD
```

Compare SHA256 for at least:

```text
admin-shell/app/templates/avito_extension.html
admin-shell/app/technoreboot-avito-extension.zip
chrome-extension/technoreboot-avito/manifest.json
chrome-extension/technoreboot-avito/popup.html
chrome-extension/technoreboot-avito/popup.js
chrome-extension/technoreboot-avito/service_worker.js
```

Record:

```text
CODE_IDENTITY_MATCH:
EXTENSION_ZIP_HASH_MATCH:
```

# 11. ISOLATED RUNTIME SMOKE TEST

Run smoke tests against the isolated stack only.

Use the VDS loopback endpoint, e.g.:

```text
https://127.0.0.1:18443
```

Use `-k` only if loopback TLS hostname mismatch is expected.

Verify:

```text
/
health endpoints
/avito/extension
/avito/extension/download
```

Expected:
- current LOCAL extension version;
- matching ZIP hash;
- pairing page renders;
- current copy-code UI renders.

If the disposable DB has the required Stage09A schema, also smoke:

```text
/sales/1
/avito/post-sale
```

Do NOT perform real Avito actions.

# 12. LIVE PRODUCTION ISOLATION CHECK DURING TEST

While isolated test stack is running, verify live production:

```text
https://144.31.50.134
```

Check:

```text
LIVE_CONTAINER_IDS_UNCHANGED:
LIVE_IMAGE_IDS_UNCHANGED:
LIVE_PUBLIC_SITE_HEALTHY:
```

All six live production containers must retain their original IDs.

# 13. LIVE PRODUCTION DB PROOF — AFTER TEST

Recompute live production DB fingerprints:

```text
LIVE_DB_SHA256_AFTER:
LIVE_DB_SIZE_AFTER:
LIVE_DB_SCHEMA_SHA_AFTER:
LIVE_DB_QUICK_CHECK_AFTER:
PRODUCTS_AFTER:
SALES_AFTER:
REPAIRS_AFTER:
PHOTOS_AFTER:
EXTERNAL_LISTINGS_AFTER:
AVITO_POST_SALE_TASKS_AFTER:
```

Required:

```text
LIVE_DB_SHA256_BEFORE == LIVE_DB_SHA256_AFTER
LIVE_DB_SCHEMA_SHA_BEFORE == LIVE_DB_SCHEMA_SHA_AFTER
PRODUCTS_BEFORE == PRODUCTS_AFTER
SALES_BEFORE == SALES_AFTER
REPAIRS_BEFORE == REPAIRS_AFTER
PHOTOS_BEFORE == PHOTOS_AFTER
EXTERNAL_LISTINGS_BEFORE == EXTERNAL_LISTINGS_AFTER
```

If `avito_post_sale_tasks` was absent before, it must still be absent after.

This is the critical proof.

# 14. MEDIA / AUTH PROOF

Verify:

```text
PROD_STORAGE_FILE_COUNT_BEFORE == PROD_STORAGE_FILE_COUNT_AFTER
PROD_AUTH_CA_SHA256_BEFORE == PROD_AUTH_CA_SHA256_AFTER
```

# 15. CLEANUP

After proof:

1. stop/remove only isolated test containers/network;
2. remove disposable test DB/data;
3. remove temporary VDS worktree/release directory if no longer needed;
4. retain only a small manifest/report if useful.

Do NOT remove or restart live production containers.

Record:

```text
ISOLATED_STACK_REMOVED:
TEMP_TEST_DB_REMOVED:
LIVE_PRODUCTION_STILL_HEALTHY:
```

# 16. FAILURE BEHAVIOR

If the isolated candidate fails:
- do not deploy to production;
- do not touch live DB;
- collect isolated logs;
- tear down isolated test stack;
- report exact failure.

Return:

```text
BLOCKED_FOR_PRODUCTION_DEPLOYMENT
```

# 17. DOCUMENTATION

Create/update locally:

```text
reports/stage09b_vds_isolated_shell_sync_no_prod_db_report.md
logs/2026-09-14.md
docs/production_status.md
```

State explicitly:

```text
VDS_HOST_COMPATIBILITY_TESTED = true/false
PRODUCTION_RUNTIME_UPDATED = false
PRODUCTION_DB_MODIFIED = false
```

# 18. GIT

Preserve this prompt.

If a temporary remote test branch was pushed, report it.

Do not merge/deploy to production.

Record:

```text
LOCAL_HEAD_AFTER:
TEMP_REMOTE_BRANCH:
ORIGIN_MAIN_CHANGED:
FINAL_LOCAL_GIT_STATUS:
```

# 19. FINAL REPORT CONTRACT

Return:

```text
# Stage 09B — VDS Isolated Shell Sync / No Production DB Touch

## Candidate
LOCAL_HEAD:
TEST_RELEASE_HEAD:
CODE_IDENTITY_MATCH:
EXTENSION_VERSION:
EXTENSION_ZIP_HASH_MATCH:

## Live Production Before
VDS_LIVE_HEAD:
LIVE_6_SERVICES_HEALTHY_BEFORE:
LIVE_CONTAINER_IDS_BEFORE:
LIVE_IMAGE_IDS_BEFORE:
LIVE_DB_SHA256_BEFORE:
LIVE_DB_SCHEMA_SHA_BEFORE:
LIVE_DB_QUICK_CHECK_BEFORE:
PRODUCTS_BEFORE:
SALES_BEFORE:
REPAIRS_BEFORE:
PHOTOS_BEFORE:
EXTERNAL_LISTINGS_BEFORE:
AVITO_POST_SALE_TASKS_BEFORE:

## Isolated VDS Test
ISOLATED_PROJECT_NAME:
ISOLATED_PORT:
DISPOSABLE_DB_USED: true
LIVE_DB_MOUNTED_WRITABLE: false
TEST_DB_MIGRATED_IF_NEEDED:
TEST_6_SERVICES_HEALTHY:
ROOT_PAGE_OK:
AVITO_EXTENSION_PAGE_OK:
AVITO_EXTENSION_DOWNLOAD_OK:
SALES_PAGE_OK:
POST_SALE_PAGE_OK:

## Sync Identity
LOCAL_HEAD_EQUALS_TEST_HEAD:
CRITICAL_ASSET_HASHES_MATCH:
EXTENSION_ZIP_HASH_MATCH:

## Live Production After
LIVE_6_SERVICES_HEALTHY_AFTER:
LIVE_CONTAINER_IDS_UNCHANGED:
LIVE_IMAGE_IDS_UNCHANGED:
LIVE_DB_SHA256_AFTER:
LIVE_DB_SCHEMA_SHA_AFTER:
LIVE_DB_QUICK_CHECK_AFTER:
PRODUCTS_AFTER:
SALES_AFTER:
REPAIRS_AFTER:
PHOTOS_AFTER:
EXTERNAL_LISTINGS_AFTER:
AVITO_POST_SALE_TASKS_AFTER:
PROD_STORAGE_UNCHANGED:
PROD_AUTH_CA_UNCHANGED:

## Cleanup
ISOLATED_STACK_REMOVED:
TEMP_TEST_DB_REMOVED:
TEMP_RELEASE_REMOVED_OR_ARCHIVED:
LIVE_PRODUCTION_STILL_HEALTHY:

## Safety
UPDATE_VDS_RUN: false
PRODUCTION_RUNTIME_UPDATED: false
PRODUCTION_DB_MODIFIED: false
PRODUCTION_SCHEMA_MODIFIED: false
PRODUCTION_MEDIA_MODIFIED: false
PRODUCTION_AUTH_MODIFIED: false

## Git
TEMP_REMOTE_BRANCH:
ORIGIN_MAIN_CHANGED:
FINAL_LOCAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE09B_VDS_ISOLATED_SYNC_TEST_PASSED_NO_PROD_DB_TOUCH

READY_FOR_SEPARATE_PRODUCTION_DEPLOYMENT_STAGE:
true/false
```

Return BLOCKED if:
- live production DB hash/schema changes;
- any live production container restarts/recreates;
- production media/auth changes;
- code identity mismatch exists;
- isolated candidate is unhealthy;
- tests fail.

# 20. STOP

After isolated VDS compatibility/synchronization proof:

STOP.

Do NOT perform the real production deployment.

Wait for Owner acceptance and a separate deployment prompt.
