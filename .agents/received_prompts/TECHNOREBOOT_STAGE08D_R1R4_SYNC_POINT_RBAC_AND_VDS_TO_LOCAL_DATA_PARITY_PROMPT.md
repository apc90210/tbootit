# TECHNOREBOOT — Stage 08D-R1R4-SYNC
## Complete security fixes + production deploy + VDS→LOCAL business-data parity

**Project:** ТехноРебут  
**Local workspace:** `C:\tbootit`  
**Production VDS:** `https://144.31.50.134`  
**Stage:** `Stage 08D-R1R4-SYNC — Security Hardening + Full Business Data Parity`

# 0. OWNER DECISION — THIS PROMPT SUPERSEDES THE PREVIOUS CORRECTION

Do NOT execute the previous prompt:

```text
TECHNOREBOOT_STAGE08D_R1R4_R1_RESTORE_DEV_ISOLATION_AND_COMPLETE_RBAC_HARDENING_PROMPT.md
```

The Owner has explicitly changed the synchronization model.

## New permanent model

### SOURCE CODE
Direction:

```text
LOCAL DEV -> Git -> VDS
```

Local is where code/UI/new features are developed and tested.

Production deployment to VDS is CODE-ONLY.

### BUSINESS DATA
Direction:

```text
VDS -> LOCAL
```

VDS is the canonical source of truth for:
- products;
- sales;
- repairs;
- inventory;
- product photos/media;
- external listings;
- operational business data.

Local DEV should periodically receive a fresh snapshot of VDS business data so local testing happens against the current real catalog/data.

### ABSOLUTE RULE

Never sync business data:

```text
LOCAL -> VDS
```

The production VDS database and media must never be overwritten by local DEV data during ordinary deployment.

---

# 1. GOAL OF THIS STAGE

At the end of this stage:

1. all previously identified RBAC/draft/security issues are fixed;
2. local source code and VDS runtime are on the same approved runtime commit;
3. VDS real business data is preserved exactly;
4. VDS business data is then copied in the SAFE direction to LOCAL;
5. local DB/media/business state matches the VDS snapshot;
6. VDS remains the source of truth;
7. future workflow is documented and automated:
   - code LOCAL -> VDS;
   - data VDS -> LOCAL;
   - never the reverse.

---

# 2. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08D_R1R4_SYNC_POINT_RBAC_AND_VDS_TO_LOCAL_DATA_PARITY_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08D_R1R4_SYNC_POINT_RBAC_AND_VDS_TO_LOCAL_DATA_PARITY_PROMPT.md`

---

# 3. PREFLIGHT — CAPTURE BOTH ENVIRONMENTS

Record Git:

```text
LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
LOCAL_GIT_STATUS:
VDS_HEAD:
```

Record LOCAL business state:

```text
LOCAL_PRODUCTS:
LOCAL_SALES:
LOCAL_REPAIRS:
LOCAL_PHOTOS:
LOCAL_EXTERNAL_LISTINGS:
LOCAL_DB_SHA256:
LOCAL_STORAGE_FILE_COUNT:
LOCAL_STORAGE_TREE_SHA256:
LOCAL_CA_SHA256:
```

Record VDS business state:

```text
VDS_PRODUCTS:
VDS_SALES:
VDS_REPAIRS:
VDS_PHOTOS:
VDS_EXTERNAL_LISTINGS:
VDS_DB_SHA256:
VDS_STORAGE_FILE_COUNT:
VDS_STORAGE_TREE_SHA256:
VDS_CA_SHA256:
```

Important:
- do not assume historical counts such as 149 remain current;
- users may already have changed VDS data;
- capture the CURRENT VDS state and preserve it.

---

# 4. SAFETY BACKUPS BEFORE ANY CHANGE

## VDS

Create a fresh full production backup using the accepted production backup mechanism.

Record:

```text
VDS_PRE_STAGE_BACKUP_FILE:
VDS_PRE_STAGE_BACKUP_SHA256:
```

Do not restore it.

## LOCAL

Create a full local safety backup of the current local mutable data before any VDS→LOCAL synchronization.

Store under ignored local recovery storage, for example:

```text
C:\tbootit\.local-recovery\pre_sync_YYYYMMDD_HHMMSS.zip
```

Record:

```text
LOCAL_PRE_SYNC_BACKUP_FILE:
LOCAL_PRE_SYNC_BACKUP_SHA256:
```

Never commit either archive.

---

# 5. IMPLEMENT ALL OUTSTANDING DRAFT-LIFECYCLE FIXES

Audit `core/app/routers/products.py` and all product-status UI/API paths.

Required safe lifecycle:

```text
in_stock -> draft    ALLOWED
draft -> in_stock    ALLOWED

reserved -> draft    FORBIDDEN
written_off -> draft FORBIDDEN
sold -> draft        FORBIDDEN
archive -> draft     FORBIDDEN
```

For `imported`:
- allow `imported -> draft` only if current real business semantics explicitly require it;
- otherwise forbid it;
- document the decision.

Preferred business definition:

```text
draft = temporary hidden state for an available product
```

`draft` must never be a resurrection/bypass state.

---

# 6. DRAFT UI RULES

Seller and Owner UI should show:

```text
in_stock -> "Убрать в черновик"
draft    -> "Вернуть в наличие"
```

Do NOT show draft actions for:
- reserved;
- written_off;
- sold;
- archive.

Backend remains authoritative even if UI is bypassed.

Do not create an OWNER-only hidden shortcut through `draft`.

---

# 7. COMPLETE SELLER RBAC HARDENING

Required USER restrictions:

```text
/admin-api/dev-reset        -> forbidden
/admin-api/seed             -> forbidden
/dev-reset                  -> forbidden
/seed                       -> forbidden
/backups                    -> forbidden
/certificates               -> forbidden
Avito profile hard-delete   -> forbidden
```

Requirements:
- UI controls hidden;
- gateway/auth layer rejects USER;
- backend rejects USER;
- production `dev-reset` is forbidden even to OWNER;
- no destructive production action is invoked merely for proof.

For OWNER:
- OWNER-only routes remain available where appropriate;
- production DB reset remains hard-blocked.

---

# 8. COMPLETE HARD-DELETE AUDIT

Inventory every `DELETE` endpoint and every code path that physically deletes persistent business rows across:

- core;
- admin-shell;
- inventory-sales-module;
- repairs-module;
- avito-module.

For every path record:

```text
ROUTE
ENTITY
SOFT_OR_HARD
OWNER_ONLY
USER_ALLOWED
AUDITED
```

Explicitly cover:
- products;
- sales;
- repairs;
- customers;
- categories;
- product photos;
- external listings;
- Avito profiles;
- inventory/stock;
- payments/business transactions.

Acceptance rule:

```text
USER_ACCESSIBLE_HARD_DELETE_ROUTES = 0
```

If any seller-accessible hard delete exists:
- close it;
- use a safe soft transition or OWNER-only operation where appropriate;
- add regression tests.

---

# 9. EXTENSION HOST-PERMISSION AUDIT

Audit current Avito Extension manifest.

If it still contains:

```text
https://*/*
```

remove this broad permanent permission unless absolutely necessary.

Preferred permissions:
- `https://144.31.50.134/*`;
- local DEV origins;
- exact Avito origins required by the extension.

If arbitrary CRM server targets are required:
- prefer `optional_host_permissions`;
- request explicit permission when configuring that server.

If manifest/runtime changes:
- bump extension version from current version to the next version;
- synchronize version across extension/backend/UI;
- rebuild downloadable ZIP;
- run full extension regression suite.

The VDS extension pairing flow must continue to work.

---

# 10. LOCAL TESTS BEFORE COMMIT

Run at minimum:

```text
core/tests/test_product_safety_and_draft.py
core/tests/test_products.py
admin-shell/tests/test_seller_rbac_and_data_safety.py
admin-shell/tests/test_certificate_auth.py
tests/test_production_data_guard.py
tests/test_stage08b_r1_production_baseline.py
```

Add/run:
- draft transition rejection tests;
- hard-delete route inventory tests;
- extension tests if extension changed;
- code-only deploy guard tests.

Required:

```text
FAILED = 0
```

---

# 11. COMMIT AND PUSH THE SOURCE FIXES

Commit all safe runtime code/tests.

Push `origin/main`.

Define:

```text
DEPLOY_HEAD = exact pushed runtime commit
```

Do not include:
- DB;
- media;
- production/private secrets;
- pairing runtime tokens;
- backup archives.

---

# 12. DEPLOY CODE TO VDS — CODE ONLY

Before deploy, capture CURRENT VDS counts and hashes again.

Deploy only through the accepted mechanism:

```text
deploy/production/update_code_only.sh origin/main
```

Forbidden:
- copying local DB to VDS;
- copying local media to VDS;
- copying local auth to VDS;
- copying local Avito runtime state to VDS;
- bootstrap restore.

After deploy require:
- all 6 services healthy;
- VDS business counts unchanged;
- VDS Client CA unchanged;
- production data guard present.

Record:

```text
VDS_HEAD_AFTER_DEPLOY:
VDS_PRODUCTS_AFTER_DEPLOY:
VDS_SALES_AFTER_DEPLOY:
VDS_REPAIRS_AFTER_DEPLOY:
VDS_PHOTOS_AFTER_DEPLOY:
VDS_EXTERNAL_LISTINGS_AFTER_DEPLOY:
VDS_CA_SHA256_AFTER_DEPLOY:
```

---

# 13. NON-DESTRUCTIVE PRODUCTION SECURITY PROOF

Do not modify a real product merely for testing.

Safely prove:
- USER auth layer rejects owner-only destructive routes;
- production OWNER dev-reset returns 403;
- primary routes healthy;
- VDS counts unchanged;
- no real product status changed;
- no seed/reset/profile delete was actually executed.

---

# 14. CREATE A CONSISTENT VDS BUSINESS SNAPSHOT FOR LOCAL

After production code deployment is proven healthy:

Create a fresh VDS snapshot using the accepted production backup mechanism.

This snapshot is the source for VDS→LOCAL synchronization.

Record:

```text
SYNC_SNAPSHOT_FILE:
SYNC_SNAPSHOT_SHA256:
SYNC_SNAPSHOT_CREATED_AT:
```

The snapshot must contain at minimum:
- SQLite database;
- storage/media;
- business Avito state required to represent the catalog/listings consistently.

---

# 15. VDS→LOCAL SYNC SCOPE

## MUST synchronize to LOCAL

From the consistent VDS snapshot:

```text
database/technoreboot.db
storage/**
```

Also synchronize business-only Avito mutable state necessary for development parity, such as:
- listing/import metadata;
- business cache/data needed to reproduce current catalog behavior.

## DO NOT automatically synchronize environment secrets

Do NOT overwrite local environment-specific infrastructure with production secrets merely for parity.

Exclude by default:
- production server TLS private key;
- SSH keys;
- production env/secrets;
- production backup history;
- production Certbot state;
- live production pairing tokens;
- live production pairing codes;
- browser session secrets/cookies;
- private credentials that are not business data.

The same Owner client certificate may continue to work in both environments through the existing trusted Client CA model.

If the current local auth tree is already intentionally shared and required for local mTLS, preserve it rather than replacing it from the VDS snapshot.

---

# 16. SAFE LOCAL REPLACEMENT

Before applying snapshot:
- local backup from Section 4 must exist and validate;
- stop LOCAL containers;
- VDS stays running.

Apply VDS business snapshot to LOCAL:
- replace local canonical DB with VDS snapshot DB;
- replace local storage/media with VDS snapshot storage;
- synchronize approved business Avito state;
- remove stale local business files that do not exist in VDS snapshot.

Do not merge stale local business rows into the production snapshot.

Restart LOCAL containers.

---

# 17. EXACT DATA PARITY PROOF

After local restart compare VDS snapshot vs LOCAL.

Required exact parity:

```text
LOCAL_PRODUCTS == VDS_PRODUCTS
LOCAL_SALES == VDS_SALES
LOCAL_REPAIRS == VDS_REPAIRS
LOCAL_PHOTOS == VDS_PHOTOS
LOCAL_EXTERNAL_LISTINGS == VDS_EXTERNAL_LISTINGS

LOCAL_DB_SHA256 == SYNC_SNAPSHOT_DB_SHA256
LOCAL_STORAGE_TREE_SHA256 == SYNC_SNAPSHOT_STORAGE_TREE_SHA256
```

For every DB table classified as business:
- compare row counts;
- ideally compare deterministic table hashes.

Required:

```text
BUSINESS_TABLE_MISMATCHES = 0
STORAGE_FILE_MISMATCHES = 0
```

Do not require environment-specific secret/runtime files to be byte-identical.

---

# 18. LOCAL RUNTIME PROOF AFTER DATA SYNC

Verify local DEV after synchronization:

```text
https://localhost:8443
```

OWNER access works.

Verify:
- Products;
- one real product card;
- product images;
- Sales;
- Reports;
- Repairs;
- Avito pages;
- JSON editor.

All local services healthy.

Local is now suitable for development/testing against the current production business snapshot.

---

# 19. CREATE PERMANENT ONE-WAY VDS→LOCAL SYNC TOOL

Create a safe reusable tool, preferably:

```text
scripts/sync_vds_business_to_local.py
```

or an equivalent Windows-friendly orchestrator.

It MUST enforce direction:

```text
VDS -> LOCAL
```

Required workflow:

1. verify target is configured production VDS;
2. verify SSH key access;
3. create fresh VDS backup/snapshot;
4. verify snapshot hash;
5. create local pre-sync backup;
6. stop LOCAL stack only;
7. extract/copy only approved business-data scope;
8. replace local DB/storage atomically;
9. restart LOCAL;
10. compare business counts/hashes;
11. leave VDS untouched and running.

It MUST refuse:
- any `LOCAL -> VDS` data mode;
- upload of local DB;
- upload of local storage;
- bootstrap restore on VDS.

No credentials/private keys hardcoded in Git.

---

# 20. FUTURE OPERATING PROCEDURE

Document exactly:

## Feature/update cycle

```text
1. Sync VDS business snapshot -> LOCAL
2. Develop/test code locally
3. Commit/push Git
4. VDS backup
5. Code-only deploy LOCAL/Git -> VDS
6. Verify VDS
7. Later refresh LOCAL business snapshot from VDS as needed
```

Absolute rule:

```text
CODE: LOCAL -> VDS
DATA: VDS -> LOCAL
```

Never reverse the data arrow during normal operation.

---

# 21. TEST THE ONE-WAY SYNC TOOL

Perform one real sync test using the CURRENT VDS snapshot.

Prove:
- local pre-sync backup created;
- VDS data unchanged;
- local business data matches VDS snapshot;
- no environment-specific production secrets copied;
- VDS stack remained running;
- local stack recovered healthy.

Required:

```text
SYNC_DIRECTION = VDS_TO_LOCAL
VDS_MUTATED_BY_SYNC = false
LOCAL_PARITY = true
```

---

# 22. FINAL PRODUCTION BACKUP / SAFETY

Do not delete:
- any existing VDS backups;
- current production DB/media;
- local pre-sync backup.

Keep production data guard active.

---

# 23. DOCUMENTATION

Create:

```text
docs/stage08d_r1r4_sync_point.md
docs/vds_to_local_data_sync.md
reports/stage08d_r1r4_sync_point_report.md
```

Update:

```text
docs/production_deployment_model.md
docs/production_status.md
logs/2026-09-12.md
```

Preserve received prompt.

---

# 24. FINAL GIT SAFETY

Commit only:
- code;
- tests;
- sync tooling;
- docs;
- reports;
- logs.

Never commit:
- SQLite DB;
- media;
- VDS backup ZIP;
- local recovery ZIP;
- auth private keys;
- passwords;
- production pairing tokens;
- production env/secrets.

Push `origin/main`.

Final worktree clean.

---

# 25. FINAL REPORT CONTRACT

Return:

```text
# Stage 08D-R1R4-SYNC — Security Hardening + VDS→LOCAL Business Parity

## Source / Runtime
DEPLOY_HEAD:
LOCAL_HEAD:
VDS_HEAD:
CODE_PARITY:

## Draft Lifecycle
IN_STOCK_TO_DRAFT:
DRAFT_TO_IN_STOCK:
RESERVED_TO_DRAFT:
WRITTEN_OFF_TO_DRAFT:
SOLD_TO_DRAFT:
ARCHIVE_TO_DRAFT:
IMPORTED_TO_DRAFT:
DRAFT_BYPASS_CLOSED:

## RBAC
USER_DEV_RESET_AUTH:
USER_SEED_AUTH:
USER_AVITO_PROFILE_DELETE_AUTH:
USER_BACKUPS_AUTH:
USER_CERTIFICATES_AUTH:
OWNER_PRODUCTION_DEV_RESET:
DESTRUCTIVE_HANDLER_INVOKED_DURING_PROOF: false

## Hard Delete Audit
DELETE_ROUTES_FOUND:
USER_ACCESSIBLE_HARD_DELETE_ROUTES:
SELLER_NO_HARD_DELETE_PROVEN:

## Extension
EXTENSION_VERSION:
BROAD_HTTPS_HOST_PERMISSION_PRESENT:
HOST_PERMISSION_RESULT:
PAIRING_VDS_WORKS:
ZIP_REBUILT:

## Tests
FAILED:

## VDS Safety
VDS_PRE_STAGE_BACKUP:
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
VDS_CA_SHA256_UNCHANGED:
LOCAL_DATA_UPLOADED_TO_VDS: false
ALL_VDS_SERVICES_HEALTHY:

## VDS→LOCAL Snapshot
SYNC_SNAPSHOT_FILE:
SYNC_SNAPSHOT_SHA256:
LOCAL_PRE_SYNC_BACKUP:
SYNC_DIRECTION: VDS_TO_LOCAL
VDS_MUTATED_BY_SYNC: false

## Business Parity
VDS_PRODUCTS:
LOCAL_PRODUCTS:
VDS_SALES:
LOCAL_SALES:
VDS_REPAIRS:
LOCAL_REPAIRS:
VDS_PHOTOS:
LOCAL_PHOTOS:
VDS_EXTERNAL_LISTINGS:
LOCAL_EXTERNAL_LISTINGS:
DB_SHA256_MATCH:
STORAGE_TREE_SHA256_MATCH:
BUSINESS_TABLE_MISMATCHES:
STORAGE_FILE_MISMATCHES:
LOCAL_PARITY:

## Secret Isolation
PRODUCTION_TLS_KEY_COPIED_TO_LOCAL: false
PRODUCTION_ENV_COPIED_TO_LOCAL: false
PRODUCTION_PAIRING_TOKENS_COPIED_TO_LOCAL: false
PRODUCTION_PAIRING_CODES_COPIED_TO_LOCAL: false

## Future Workflow
CODE_DIRECTION: LOCAL_TO_VDS
DATA_DIRECTION: VDS_TO_LOCAL
CODE_ONLY_DEPLOY_ENFORCED:
VDS_TO_LOCAL_SYNC_TOOL:
LOCAL_TO_VDS_DATA_SYNC_FORBIDDEN:

## Runtime
LOCAL_STACK_HEALTHY:
VDS_STACK_HEALTHY:
LOCAL_URL: https://localhost:8443
VDS_URL: https://144.31.50.134

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08D_R1R4_SYNC_POINT_ESTABLISHED

VDS_IS_CANONICAL_DATA_SOURCE: true
LOCAL_BUSINESS_SNAPSHOT_MATCHES_VDS: true
FUTURE_CODE_DEPLOYS_LOCAL_TO_VDS: true
FUTURE_DATA_SYNCS_VDS_TO_LOCAL: true
LOCAL_BUSINESS_DATA_MUST_NEVER_OVERWRITE_VDS: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- VDS business data changes unexpectedly during code deployment;
- local DB/media are uploaded to VDS;
- draft bypass remains;
- USER can hard-delete persistent business data;
- local business snapshot does not match VDS;
- sync tool permits LOCAL→VDS data flow;
- tests fail.

---

# 26. STOP

After:
- fixes implemented;
- code deployed to VDS;
- VDS verified;
- VDS snapshot synchronized to LOCAL;
- parity proven;
- one-way sync tool documented/tested;

STOP.

Wait for Owner acceptance.
