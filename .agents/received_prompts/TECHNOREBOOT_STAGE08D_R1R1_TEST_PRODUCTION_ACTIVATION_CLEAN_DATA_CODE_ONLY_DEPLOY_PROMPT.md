# TECHNOREBOOT — Stage 08D-R1R1
## Test-production activation with clean server data and code-only deployment model

**Project:** ТехноРебут  
**Local workspace:** `C:\tbootit`  
**VDS:** `144.31.50.134`  
**Hostname:** `atanov821.serv.host`  
**Stage:** `Stage 08D-R1R1 — Clean Test-Production Activation + Code-Only Deploy`

# 0. OWNER DECISION — NEW OPERATING MODEL

The previous "final cutover / local stack stopped" model is CANCELLED.

Owner explicitly defines a new long-term architecture:

## Local workstation
- remains permanently available;
- is DEV / TEST sandbox;
- may contain dirty/test/demo business data;
- is used for UI changes, bug fixes, development and regression testing;
- local business data is NOT authoritative production data;
- local business data must NEVER be pushed/restored/synchronized into VDS after this stage.

## VDS
- becomes the canonical test-production / real-user environment;
- real users will work there;
- VDS business data is authoritative;
- VDS business data and media must persist across code upgrades;
- future deployments must update CODE / UI / containers only;
- production data must not be overwritten by local data.

Both local and VDS stacks MAY run simultaneously because they are independent environments with independent data.

This stage must:
1. preserve local environment completely;
2. create a safety backup of current VDS state;
3. intentionally wipe all LIVE BUSINESS DATA on VDS;
4. preserve infrastructure/security state;
5. start VDS as a clean real-user environment;
6. establish and document a safe CODE-ONLY update mechanism for future upgrades.

---

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08D_R1R1_TEST_PRODUCTION_ACTIVATION_CLEAN_DATA_CODE_ONLY_DEPLOY_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08D_R1R1_TEST_PRODUCTION_ACTIVATION_CLEAN_DATA_CODE_ONLY_DEPLOY_PROMPT.md`

---

# 2. PRE-FLIGHT — LOCAL MUST REMAIN UNTOUCHED

Record:

```text
LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
LOCAL_GIT_STATUS:
LOCAL_STACK_RUNNING:
LOCAL_PRODUCTS:
LOCAL_SALES:
LOCAL_REPAIRS:
LOCAL_PHOTOS:
LOCAL_EXTERNAL_LISTINGS:
LOCAL_DB_SHA256:
LOCAL_CA_SHA256:
LOCAL_CONTAINER_RESTART_COUNTS:
```

Required:
- local worktree clean;
- local HEAD == origin/main before changes;
- local stack stays running;
- do NOT stop local containers;
- do NOT reset or clean local DB;
- do NOT delete local media;
- do NOT import VDS data into local.

Capture exact local IDs and hashes only for non-mutation proof.

---

# 3. PRE-FLIGHT — VDS

Connect using existing key-based SSH.

Verify:

```text
VDS_HOST = 144.31.50.134
VDS_HOSTNAME = atanov821.serv.host
SSH_KEY_AUTH = PASS
VDS_OS = Debian
DOCKER = available
COMPOSE = available
VDS_DATA_ROOT = /srv/technoreboot/data
```

Record current:
- VDS Git HEAD;
- VDS stack state;
- DB counts;
- DB SHA256;
- storage recursive file count/tree hash;
- auth CA SHA256;
- backups;
- Avito mutable state;
- server TLS status.

---

# 4. FINAL DOMAIN / TLS FOR REAL USERS

This VDS will be used by real users.

Verify:

```text
atanov821.serv.host -> 144.31.50.134
```

Check A and AAAA records.

If AAAA exists and is wrong, BLOCK until corrected.

Replace temporary self-signed pre-cutover server certificate with a publicly trusted certificate for:

`atanov821.serv.host`

Preferred:
- Let's Encrypt / ACME.

Requirements:
- public trust;
- SAN contains `atanov821.serv.host`;
- automatic renewal configured;
- private key 0600;
- do NOT replace Technoreboot CLIENT CA;
- OWNER/USER client certificates remain valid.

Verify:

```text
TLS_PUBLIC_TRUST = true
TLS_HOSTNAME_MATCH = true
TLS_RENEWAL_CONFIGURED = true
TLS_RENEW_DRY_RUN = PASS
```

If trusted TLS cannot be obtained, return BLOCKED and DO NOT perform the destructive clean-data step.

---

# 5. SAFETY BACKUP BEFORE VDS DATA RESET

Before deleting anything on VDS:

Create a FULL server backup of the current VDS mutable state using the accepted backup mechanism.

Also create a filesystem-level safety manifest.

Store under:

`/srv/technoreboot/deploy/pre_clean_reset/`

Record:

```text
PRE_RESET_BACKUP_FILENAME:
PRE_RESET_BACKUP_SHA256:
PRE_RESET_DB_SHA256:
PRE_RESET_STORAGE_TREE_SHA256:
PRE_RESET_AUTH_TREE_SHA256:
PRE_RESET_AVITO_TREE_SHA256:
```

Do not delete this backup during the stage.

The purpose is rollback if the reset scope is wrong.

---

# 6. DEFINE WHAT MUST BE PRESERVED

The following VDS infrastructure/security state MUST be preserved:

- `/srv/technoreboot/data/auth`
  - client CA;
  - OWNER certificate registry;
  - USER certificates;
  - revoked certificate registry;
- `/srv/technoreboot/data/backups`;
- `/srv/technoreboot/secrets`;
- production server TLS certificate/private key;
- production env/secrets;
- SSH configuration/authorized_keys;
- Docker installation;
- repository checkout;
- firewall;
- system packages.

Do NOT regenerate:
- client CA;
- OWNER certificate;
- USER certificates.

Do NOT wipe backup history.

---

# 7. DEFINE WHAT MUST BE RESET

Owner explicitly authorizes destructive reset of ALL VDS BUSINESS DATA.

The reset must remove all live domain/business records, including all dependent/history rows associated with:

- products;
- product photos;
- inventory/stock;
- sales;
- sale items;
- receipts/check-related data;
- canceled/reissued/superseded sale history where stored as business records;
- payment records/channels linked to sales;
- repairs / repair orders;
- repair history/events/comments if business data;
- product external listings;
- Avito listing/import/cache/draft/business state;
- inventory movements;
- business reports materialized data if any;
- any other domain rows discovered in schema that belong to actual shop operations.

Do NOT merely clear the five headline tables if dependent business tables remain populated.

Preserve only:
- schema/migrations;
- mandatory technical/reference rows strictly required for application startup;
- infrastructure auth/security state.

---

# 8. RESET METHOD — SAFE EMPTY DATABASE

Do NOT delete random tables ad hoc.

Inspect the current schema first and classify tables:

```text
BUSINESS_TABLES
TECHNICAL_TABLES
REFERENCE_TABLES
```

Then use one of these safe methods:

Preferred:
1. create a new empty SQLite DB using current application schema/migrations;
2. seed ONLY mandatory technical/reference data;
3. atomically replace the live VDS DB while stack is stopped.

Acceptable alternative:
- transactional DELETE in correct FK order for all business tables;
- reset relevant `sqlite_sequence`;
- VACUUM after validation.

Required post-reset business counts:

```text
PRODUCTS = 0
SALES = 0
REPAIRS = 0
PRODUCT_PHOTOS = 0
EXTERNAL_LISTINGS = 0
INVENTORY_MOVEMENTS = 0
BUSINESS_HISTORY_ROWS = 0
```

New first records should start from clean sequence where practical:
- first new Product ID should normally begin from 1;
- same principle for new sale/repair IDs unless schema prevents it.

Do not break migrations or required reference data.

---

# 9. RESET LIVE MEDIA STORAGE

Because VDS business data starts from zero, live business media must also start clean.

Clean business media under:

`/srv/technoreboot/data/storage/`

including:
- product photos;
- archived old product photos;
- obsolete business media.

Preserve no old product media in LIVE storage.

Historical copies remain recoverable through the pre-reset backup.

Required after reset:

```text
LIVE_STORAGE_BUSINESS_FILES = 0
```

If application requires placeholder/system assets, keep only those and report them explicitly.

---

# 10. RESET AVITO BUSINESS STATE

Clear Avito mutable/business content that represents old imported products/listings/cache/drafts/history.

Preserve only infrastructure/access state strictly required for module operation.

If extension pairing/session state is not security-sensitive and can safely persist, preserve it.
If it is mixed with old business listing state, reset it and require re-pairing.

Report:

```text
AVITO_BUSINESS_STATE_CLEARED:
EXTENSION_REPAIR_REQUIRED:
PAIRING_PRESERVED_OR_RESET:
```

Do not publish or pay for any listing.

---

# 11. START CLEAN VDS ENVIRONMENT

After reset, start the VDS production/test-production stack.

Required:

```text
VDS_STACK_RUNNING = true
LOCAL_STACK_RUNNING = true
```

This is intentional.

Local is DEV.
VDS is canonical real-user environment.

Verify all six services healthy.

---

# 12. EMPTY-STATE UI / API VERIFICATION

Through:

`https://atanov821.serv.host`

with valid OWNER client certificate, verify:

```text
/ = 200
/inventory/products = 200
/products/json = 200
/inventory/sales = 200
/inventory/cart = 200
/inventory/reports/sales = 200
/repairs/repairs = 200
/avito/extension = 200
/backups = 200
/certificates = 200
```

Verify UI/API shows empty business state:

```text
PRODUCTS = 0
SALES = 0
REPAIRS = 0
PHOTOS = 0
EXTERNAL_LISTINGS = 0
```

Reports:
- today = 0;
- week = 0;
- year = 0;
- payment totals = 0.

Cart empty.

No stale products visible anywhere.

No old photos load through active product routes.

---

# 13. AUTH / MTLS AFTER RESET

Security/auth must remain unchanged.

Verify:
- no client cert -> rejected;
- OWNER -> allowed;
- USER operational routes -> allowed;
- USER `/backups` -> 403;
- USER `/certificates` -> 403;
- revoked cert -> rejected.

Required:

```text
CLIENT_CA_SHA256_UNCHANGED = true
OWNER_IDENTITY_PRESERVED = true
USER_ACCESS_PRESERVED = true
REVOCATION_REGISTRY_PRESERVED = true
```

---

# 14. CLEAN-STATE FUNCTIONAL SMOKE WITHOUT POLLUTING PRODUCTION

Do NOT create permanent fake shop data.

Prefer non-mutating smoke tests.

If application absolutely requires a write test:
1. create one clearly marked temporary test product;
2. verify create/edit/delete;
3. delete it completely;
4. remove its media;
5. reset sequence if safe;
6. final production counts must again be zero.

Do NOT create a real sale or repair just for testing unless strictly required.

Final business state after test:

```text
PRODUCTS = 0
SALES = 0
REPAIRS = 0
PHOTOS = 0
EXTERNAL_LISTINGS = 0
```

---

# 15. NEW LONG-TERM DEPLOYMENT MODEL — CODE ONLY

Implement a safe, repeatable CODE-ONLY production update workflow.

Goal:

> local dev changes -> Git commit/push -> VDS pulls code -> backup production data -> rebuild/recreate containers -> production data remains intact.

Create a dedicated deployment script, preferably:

`deploy/production/update_code_only.sh`

and optionally a Windows launcher/orchestrator if useful.

The code-only deployment workflow MUST:

1. verify production VDS;
2. verify `/srv/technoreboot/data` exists;
3. verify production data guard file exists;
4. create fresh VDS backup BEFORE update;
5. record pre-update business counts and DB hash;
6. fetch/pull/reset source to requested Git commit;
7. run `docker compose config`;
8. build affected/all containers from source;
9. recreate containers;
10. wait for healthchecks;
11. verify primary routes;
12. verify business counts preserved;
13. NEVER run bootstrap restore;
14. NEVER copy local DB/media/auth/Avito state;
15. NEVER delete `/srv/technoreboot/data`;
16. NEVER mount local Windows data into production;
17. rollback CODE if containers fail.

---

# 16. PRODUCTION DATA GUARD

Create a sentinel file on VDS:

`/srv/technoreboot/data/.technoreboot_production_data`

Safe example content:

```text
environment=production
data_owner=vds
do_not_overwrite_from_local=true
```

No secret values.

The code-only deploy script must refuse destructive/restore behavior when this guard is present.

Add safeguards so ordinary deployment does NOT invoke:
- `bootstrap_restore.py`;
- restore ZIP;
- DB copy from local;
- storage sync from local;
- auth copy from local.

Data restore must remain a separate explicit disaster-recovery operation only.

---

# 17. DATABASE MIGRATION POLICY FOR FUTURE UPGRADES

Future code deployments may require schema changes.

Policy:

- business DATA must not be replaced;
- schema migrations are allowed only when explicitly required by a stage;
- every migration requires fresh VDS backup first;
- migration must be forward-compatible and preserve existing rows;
- destructive migration requires separate Owner approval;
- no automatic "drop and recreate production DB".

Document this clearly.

---

# 18. VERIFY CODE-ONLY DEPLOYMENT NOW

Perform one safe self-test of the code-only deployment mechanism using the CURRENT commit (or docs-only no-op commit if appropriate).

Required proof:

```text
PRE_DEPLOY_PRODUCTS = 0
PRE_DEPLOY_SALES = 0
PRE_DEPLOY_REPAIRS = 0
PRE_DEPLOY_DB_SHA256
```

Run code-only deploy.

After:

```text
POST_DEPLOY_PRODUCTS = 0
POST_DEPLOY_SALES = 0
POST_DEPLOY_REPAIRS = 0
POST_DEPLOY_DATA_PRESERVED = true
AUTH_PRESERVED = true
STACK_HEALTHY = true
```

DB file hash may legitimately change due to SQLite metadata/startup activity, so row/content preservation is the primary invariant; if hash changes, explain why.

---

# 19. LOCAL DEV REMAINS ACTIVE

Verify local after all work:

```text
LOCAL_STACK_RUNNING = true
LOCAL_PRODUCTS unchanged
LOCAL_SALES unchanged
LOCAL_REPAIRS unchanged
LOCAL_PHOTOS unchanged
LOCAL_EXTERNAL_LISTINGS unchanged
LOCAL_DB_SHA256 unchanged
LOCAL_CA_SHA256 unchanged
LOCAL_CONTAINERS_RESTARTED = 0
```

Do NOT clean local.

Do NOT make local match VDS.

The local dirty/test dataset is intentionally independent.

---

# 20. PRODUCTION BACKUP AFTER CLEAN ACTIVATION

With clean VDS running, create a new baseline production backup.

This backup represents:

```text
CLEAN TEST-PRODUCTION BASELINE
```

Verify:
- manifest valid;
- zero business data;
- auth preserved;
- production client CA included;
- persistent backup path.

Record filename and SHA256.

---

# 21. FIREWALL / TLS / EXPOSURE

Verify final real-user environment:

```text
PUBLIC_PORTS = SSH,80,443
INTERNAL_PUBLIC_PORTS = 0
FIREWALL_ACTIVE = true
PUBLIC_TLS_TRUSTED = true
HOSTNAME_VALID = true
TLS_RENEWAL_CONFIGURED = true
```

---

# 22. DOCUMENTATION

Create:

`docs/stage08d_r1r1_test_production_activation.md`

`docs/production_deployment_model.md`

`docs/production_status.md`

`reports/stage08d_r1r1_clean_test_production_activation_report.md`

Update:

`logs/2026-09-12.md`

Preserve:

`.agents/received_prompts/TECHNOREBOOT_STAGE08D_R1R1_TEST_PRODUCTION_ACTIVATION_CLEAN_DATA_CODE_ONLY_DEPLOY_PROMPT.md`

`docs/production_deployment_model.md` must clearly say:

```text
LOCAL = DEV / TEST SANDBOX
VDS = CANONICAL REAL-USER DATA
CODE SYNCS LOCAL/GIT -> VDS
BUSINESS DATA NEVER SYNCS LOCAL -> VDS
VDS DATA SURVIVES CODE DEPLOYMENTS
```

---

# 23. TESTS

Run:
- production baseline tests;
- affected module tests if code changes;
- code-only deploy guard tests;
- backup tests;
- mTLS tests;
- empty-state route smoke.

Required:

```text
FAILED = 0
```

---

# 24. GIT / SECRET SAFETY

Never commit:
- SSH keys;
- passwords;
- `.secrets/`;
- production.env;
- TLS private keys;
- backup ZIP;
- runtime DB;
- production media.

Commit:
- deployment script;
- safety guard logic;
- tests;
- docs;
- reports;
- logs.

Push `origin/main`.

Final worktree clean.

---

# 25. FINAL REPORT CONTRACT

Return:

```text
# Stage 08D-R1R1 — Clean Test-Production Activation + Code-Only Deploy

## Environment Model
LOCAL_ROLE: DEV_TEST_SANDBOX
VDS_ROLE: CANONICAL_REAL_USER_ENVIRONMENT
LOCAL_STACK_RUNNING:
VDS_STACK_RUNNING:
BUSINESS_DATA_SYNC_LOCAL_TO_VDS: false
CODE_DEPLOY_LOCAL_GIT_TO_VDS: true

## DNS / TLS
HOSTNAME:
IP:
DNS_READY:
TLS_PUBLIC_TRUST:
TLS_HOSTNAME_MATCH:
TLS_RENEWAL_CONFIGURED:
TLS_RENEW_DRY_RUN:

## Pre-Reset Safety
PRE_RESET_BACKUP_FILE:
PRE_RESET_BACKUP_SHA256:
PRE_RESET_DB_SHA256:
PRE_RESET_STORAGE_TREE_SHA256:
PRE_RESET_AUTH_TREE_SHA256:
PRE_RESET_AVITO_TREE_SHA256:

## Preserved Infrastructure
CLIENT_CA_PRESERVED:
OWNER_CERT_PRESERVED:
USER_CERTS_PRESERVED:
REVOCATION_REGISTRY_PRESERVED:
BACKUP_HISTORY_PRESERVED:
PRODUCTION_SECRETS_PRESERVED:
SERVER_TLS_PRESERVED:

## VDS Business Reset
PRODUCTS:
SALES:
REPAIRS:
PRODUCT_PHOTOS:
EXTERNAL_LISTINGS:
INVENTORY_MOVEMENTS:
OTHER_BUSINESS_ROWS:
LIVE_STORAGE_BUSINESS_FILES:
AVITO_BUSINESS_STATE_CLEARED:
SQLITE_SEQUENCES_RESET:

## Empty-State Runtime
ALL_SERVICES_HEALTHY:
ROOT:
PRODUCTS_ROUTE:
JSON_ROUTE:
SALES_ROUTE:
CART_ROUTE:
REPORTS_ROUTE:
REPAIRS_ROUTE:
AVITO_ROUTE:
BACKUPS_ROUTE:
CERTIFICATES_ROUTE:
REPORT_TOTALS_ZERO:
NO_STALE_BUSINESS_DATA_VISIBLE:

## mTLS
NO_CERT_REJECTED:
OWNER_ACCEPTED:
USER_RBAC:
REVOKED_CERT_REJECTED:
CLIENT_CA_SHA256_UNCHANGED:

## Code-Only Deployment Model
UPDATE_SCRIPT:
PRODUCTION_DATA_GUARD:
PRE_UPDATE_BACKUP_REQUIRED:
LOCAL_DB_COPY_FORBIDDEN:
LOCAL_MEDIA_COPY_FORBIDDEN:
LOCAL_AUTH_COPY_FORBIDDEN:
BOOTSTRAP_RESTORE_FORBIDDEN_IN_CODE_DEPLOY:
CODE_ONLY_SELF_TEST:
POST_DEPLOY_DATA_PRESERVED:

## Local Safety
LOCAL_PRODUCTS_UNCHANGED:
LOCAL_SALES_UNCHANGED:
LOCAL_REPAIRS_UNCHANGED:
LOCAL_PHOTOS_UNCHANGED:
LOCAL_EXTERNAL_LISTINGS_UNCHANGED:
LOCAL_DB_SHA256_UNCHANGED:
LOCAL_CA_SHA256_UNCHANGED:
LOCAL_CONTAINERS_RESTARTED:

## Clean Production Baseline Backup
BASELINE_BACKUP_FILE:
BASELINE_BACKUP_SHA256:
BASELINE_BUSINESS_DATA_EMPTY:
BASELINE_AUTH_PRESERVED:

## Network
PUBLIC_PORTS:
INTERNAL_PUBLIC_PORTS:
FIREWALL_ACTIVE:

## Tests
FAILED:

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08D_R1R1_CLEAN_TEST_PRODUCTION_ACTIVE

PRODUCTION_URL: https://atanov821.serv.host
LOCAL_DEV_URL: https://localhost:8443
LOCAL_AND_VDS_MAY_RUN_SIMULTANEOUSLY: true
VDS_DATA_IS_CANONICAL: true
DO_NOT_SYNC_LOCAL_BUSINESS_DATA_TO_VDS: true
FUTURE_DEPLOYS_CODE_ONLY: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- trusted TLS is not ready;
- pre-reset VDS backup fails;
- auth/CA would be lost;
- local environment changes;
- old business data remains visible;
- code-only deploy can overwrite VDS persistent data;
- internal ports are exposed;
- tests fail.

---

# 26. STOP

After clean VDS activation, code-only deploy model proof, documentation, commit/push:

STOP.

Leave BOTH:
- local DEV stack running;
- VDS real-user stack running.

Do not sync business data between them.

Wait for Owner browser acceptance.
