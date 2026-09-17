# TECHNOREBOOT — Stage 12B PRODUCTION
## Deploy accepted Avito Extension v0.2.63 connection switching to canonical production

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`  
**Canonical production VDS:** `144.31.15.88`  
**Legacy VDS:** `144.31.50.134` — DO NOT TOUCH  
**Environment:** PRODUCTION DEPLOYMENT

# 0. OWNER ACCEPTANCE

Stage 12A has been manually accepted by Owner in browser.

Accepted behavior:
- popup shows current TechnoReboot server address;
- paired/unreachable state is visible;
- `[Отключиться]` works;
- reconnect to another server works without reinstalling extension;
- LOCAL ↔ production switching works;
- old server token/state is cleared on disconnect;
- active-tab prefill works;
- legacy VDS is no longer an active default;
- extension version: `0.2.63`;
- accepted ZIP SHA256 from Stage12A:
  `bbaf780f75647c598c0725ad2de30239f865ea311ca529d405978960d1a16f9b`.

Deploy this accepted implementation to canonical production:

```text
https://144.31.15.88
```

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE12B_PRODUCTION_DEPLOY_EXTENSION_CONNECTION_SWITCHING_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE12B_PRODUCTION_DEPLOY_EXTENSION_CONNECTION_SWITCHING_PROMPT.md`

# 2. SCOPE

Deploy only Stage12A-related production changes:
- Avito extension package v0.2.63;
- admin-shell extension download/version UI;
- avito-module pairing revoke/unpair API;
- required extension static/source files tracked in repo;
- related tests/docs/tooling.

Do NOT change:
- production business DB;
- media/storage;
- sales;
- repairs;
- inventory;
- mTLS PKI;
- Avito listing/business state;
- manual post-sale policy.

No DB migration is expected for Stage12B.

If any schema migration appears necessary, STOP and report instead of applying it.

# 3. LOCAL PREFLIGHT

Record:

```text
LOCAL_BRANCH:
LOCAL_HEAD:
LOCAL_GIT_STATUS:
EXTENSION_VERSION:
EXTENSION_ZIP_SHA256:
```

Verify:
- worktree clean;
- Stage12A report exists;
- extension tests passed;
- targeted suite passed;
- canonical ZIP exists;
- manifest version is `0.2.63`.

Check exact accepted local HEAD rather than relying on a hard-coded hash.

# 4. PRODUCTION PREFLIGHT

Connect only to:

```text
root@144.31.15.88
```

Record:

```text
PROD_HEAD_BEFORE:
PROD_GIT_STATUS:
PROD_6_SERVICES_HEALTHY_BEFORE:
PROD_DB_QUICK_CHECK_BEFORE:
PROD_PRODUCTS_BEFORE:
PROD_SALES_BEFORE:
PROD_REPAIRS_BEFORE:
PROD_PHOTOS_BEFORE:
PROD_EXTERNAL_LISTINGS_BEFORE:
PROD_AVITO_TASKS_BEFORE:
PROD_STORAGE_FILES_BEFORE:
```

Verify:
- mTLS works;
- internal ports are private;
- disk space sufficient.

Do NOT access legacy VDS.

# 5. SAFETY BACKUP / CHECKPOINT

Before deployment create a fresh production backup/checkpoint using current TechnoReboot tooling.

Even though Stage12B is code-only, preserve rollback capability.

Record:

```text
BACKUP_CREATED:
BACKUP_SHA256:
BACKUP_MANIFEST_OK:
BACKUP_DB_QUICK_CHECK:
CHECKPOINT_CREATED:
CHECKPOINT_ID:
```

Do not restore or modify business data.

# 6. CODE UPDATE

Update `/srv/technoreboot/app` to the accepted Stage12A code.

Use normal Git deployment workflow:

```text
git fetch
git pull / checkout accepted main HEAD
```

Confirm production worktree HEAD exactly matches the intended accepted Stage12A runtime before rebuild.

# 7. REBUILD ONLY AFFECTED SERVICES

Expected affected production services:

```text
admin-shell
avito-module
```

Rebuild/recreate these services using the canonical production compose file.

Rebuild any additional service ONLY if code dependency analysis proves it is required.

Do not rebuild unrelated services merely for convenience.

Gateway should not require changes for Stage12A.

# 8. PRODUCTION EXTENSION PACKAGE

Verify production serves the accepted extension:

```text
VERSION: 0.2.63
EXPECTED SHA256:
bbaf780f75647c598c0725ad2de30239f865ea311ca529d405978960d1a16f9b
```

Verify:
- `/avito/extension` displays v0.2.63;
- `/avito/extension/download` downloads v0.2.63;
- ZIP manifest contains version `0.2.63`;
- ZIP hash matches accepted Stage12A build.

If packaging on production is byte-different for a legitimate deterministic-build reason, investigate.
Do not silently accept a different package.

# 9. SERVER API VERIFICATION

Verify on production, non-destructively:

```text
POST /extension/api/pairing/revoke
POST /extension/api/pairing/unpair
```

Requirements:
- endpoints exist;
- invalid/missing token does not revoke unrelated connection state;
- valid test token lifecycle may be tested using an isolated newly-generated pairing code/token;
- do not invalidate Owner's current real extension token unless explicitly using a disposable test token;
- no business records touched.

If an isolated token is created, clean it up through the canonical revoke path.

# 10. EXTENSION HOST / SWITCHING SAFETY

Inspect deployed package to confirm:
- `144.31.50.134` is not an active default/fallback;
- `144.31.15.88` is supported;
- `localhost:8443` is supported;
- dynamic host permissions are available as designed;
- all extension API calls use active stored origin;
- disconnect clears active extension pairing state;
- browser mTLS cert handling is untouched.

# 11. PRODUCTION RUNTIME HEALTH

After deployment verify all six services:

```text
core
admin-shell
inventory-sales
repairs
avito
gateway
```

Required:
- healthy/up;
- no crash loops;
- no 500/502;
- mTLS still required;
- only gateway exposes public 80/443;
- HTTP 80 redirects to HTTPS.

# 12. BUSINESS DATA INVARIANTS

Compare before/after counts:

```text
PRODUCTS_AFTER == PRODUCTS_BEFORE
SALES_AFTER == SALES_BEFORE
REPAIRS_AFTER == REPAIRS_BEFORE
PHOTOS_AFTER == PHOTOS_BEFORE
EXTERNAL_LISTINGS_AFTER == EXTERNAL_LISTINGS_BEFORE
AVITO_TASKS_AFTER == AVITO_TASKS_BEFORE
STORAGE_FILES_AFTER == STORAGE_FILES_BEFORE
```

Run:
- `PRAGMA quick_check`;
- `PRAGMA foreign_key_check`.

Expected:
- no business rows changed by deployment;
- no DB schema change;
- no media change.

# 13. READ-ONLY WEB SMOKE

Using OWNER mTLS cert verify:

```text
https://144.31.15.88/
https://144.31.15.88/avito/extension
https://144.31.15.88/avito/extension/download
https://144.31.15.88/sales/
https://144.31.15.88/repairs/
https://144.31.15.88/help
```

Without client cert:
- protected HTTPS remains rejected.

# 14. OWNER BROWSER ACCEPTANCE

After successful deploy leave production ready for browser-only Owner test.

Owner flow:

1. Open:
   `https://144.31.15.88/avito/extension`
2. Download/install/update extension v0.2.63 if needed.
3. Open popup.
4. Confirm current server address is visible.
5. Confirm `[Отключиться]` is present.
6. Disconnect.
7. Generate a fresh 6-digit code on production.
8. Reconnect to:
   `https://144.31.15.88`
9. Confirm popup again shows exactly:
   `https://144.31.15.88`

Do not require CMD/PowerShell.

# 15. ROLLBACK

If production issue occurs:
- restore previous code checkpoint/images;
- keep business DB/media untouched;
- restore previous extension ZIP if required;
- do not roll back business data unless a proven DB issue occurred.

# 16. DOCUMENTATION

Create:

```text
reports/stage12b_production_deploy_extension_connection_switching_report.md
```

Update:

```text
docs/production_status.md
logs/<current-date>.md
```

Document:
- pre/post HEAD;
- backup/checkpoint;
- rebuilt services;
- extension version/hash;
- pairing API verification;
- business invariants;
- runtime health.

# 17. GIT

Commit tracked deployment report/docs/tooling only.

Never commit:
- DB;
- media;
- tokens;
- pairing secrets;
- certificates/private keys;
- backups.

Push `main`.

# 18. FINAL REPORT CONTRACT

Return:

```text
# Stage 12B — Production Deploy Extension Connection Switching

## Target
PRODUCTION_VDS: 144.31.15.88
LEGACY_VDS_TOUCHED: false

## Preflight
LOCAL_ACCEPTED_HEAD:
PROD_HEAD_BEFORE:
PROD_6_SERVICES_HEALTHY_BEFORE:
PROD_DB_QUICK_CHECK_BEFORE:

## Safety
BACKUP_CREATED:
BACKUP_SHA256:
BACKUP_MANIFEST_OK:
CHECKPOINT_CREATED:
CHECKPOINT_ID:

## Deployment
PROD_HEAD_AFTER:
ADMIN_SHELL_REBUILT:
AVITO_MODULE_REBUILT:
OTHER_SERVICES_REBUILT:
DB_MIGRATION_APPLIED: false
LOCAL_DB_COPIED_TO_PROD: false
LOCAL_MEDIA_COPIED_TO_PROD: false

## Extension
EXTENSION_VERSION: 0.2.63
EXTENSION_DOWNLOAD_OK:
EXTENSION_ZIP_SHA256:
EXTENSION_HASH_MATCHES_ACCEPTED:
CURRENT_SERVER_ADDRESS_UI_PRESENT:
DISCONNECT_UI_PRESENT:
RECONNECT_UI_PRESENT:
LEGACY_VDS_NOT_DEFAULT:
DYNAMIC_HOST_PERMISSION_PRESENT:

## Pairing API
REVOKE_ENDPOINT_PRESENT:
UNPAIR_ENDPOINT_PRESENT:
ISOLATED_TOKEN_REVOKE_TEST:
REAL_OWNER_TOKEN_PRESERVED:

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
PROD_6_SERVICES_HEALTHY_AFTER:
DB_QUICK_CHECK_AFTER:
FOREIGN_KEY_CHECK:
MTLS_REQUIRED:
INTERNAL_PORTS_PRIVATE:
ROOT_OK:
AVITO_EXTENSION_PAGE_OK:
AVITO_EXTENSION_DOWNLOAD_OK:
SALES_OK:
REPAIRS_OK:
HELP_OK:

## Owner Acceptance
OWNER_BROWSER_ACCEPTANCE: PENDING

FINAL_STATUS:
TECHNOREBOOT_STAGE12B_PRODUCTION_READY_FOR_OWNER_ACCEPTANCE
```

# 19. STOP

STOP after production deploy + non-destructive verification.

Do not touch legacy VDS.
Do not modify production business data.
Wait for Owner browser acceptance.
