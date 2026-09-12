# TECHNOREBOOT — Stage 08D-R1R2
## IP-only clean test-production activation

**Project:** ТехноРебут
**Local workspace:** `C:\tbootit`
**VDS:** `144.31.50.134`
**Canonical production URL for now:** `https://144.31.50.134`
**Stage:** `Stage 08D-R1R2 — IP-Only Clean Test-Production Activation`

# 0. OWNER DECISION

DNS / hostname activation is DEFERRED.

Do NOT block production activation on `atanov821.serv.host`.

For now the canonical real-user address is:

```text
https://144.31.50.134
```

Long-term environment model remains:

```text
LOCALHOST = DEV / TEST SANDBOX
VDS       = CANONICAL REAL-USER ENVIRONMENT
```

Both environments may run simultaneously.

Business data must NEVER sync from local to VDS.
Future deployments are CODE-ONLY.

This stage continues from Stage08D-R1R1, which already completed:
- pre-reset VDS backup;
- production data guard;
- code-only deployment script;
- deployment guard tests;
- local safety verification.

This stage must now:
1. obtain trusted HTTPS directly for the IP if technically available;
2. clean all VDS business data;
3. preserve auth/security/backups;
4. start VDS as an empty real-user environment;
5. prove empty state + mTLS;
6. prove code-only deployment preserves VDS data;
7. leave both local DEV and VDS running.

---

# 1. PROMPT PRESERVATION

Copy unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08D_R1R2_IP_ONLY_CLEAN_TEST_PRODUCTION_ACTIVATION_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08D_R1R2_IP_ONLY_CLEAN_TEST_PRODUCTION_ACTIVATION_PROMPT.md`

---

# 2. PREFLIGHT

Record:

```text
LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
LOCAL_GIT_STATUS:
LOCAL_STACK_RUNNING:
VDS_STACK_RUNNING:
VDS_REPO_HEAD:
```

Required:
- local HEAD == origin/main;
- local worktree clean;
- local stack running;
- VDS state known;
- SSH key access works.

Capture local non-mutation baseline:
- product IDs;
- sale IDs;
- repair IDs;
- photo IDs;
- external listing IDs;
- local DB SHA256;
- local CA SHA256;
- local container restart counts.

Do NOT stop or clean local.

---

# 3. REUSE EXISTING SAFETY ARTIFACTS

Verify the Stage08D-R1R1 pre-reset backup still exists:

```text
/srv/technoreboot/deploy/pre_clean_reset/TECHNOREBOOT_PRE_RESET_BACKUP_2026-09-12_081617.zip
```

Expected SHA256:

```text
4362991cc8216b66d36451b1ea36be9ede3ff77173a9bb4a871be280c122b9cc
```

Verify:
- file exists;
- SHA256 exact;
- safety manifest exists;
- production data guard exists:

```text
/srv/technoreboot/data/.technoreboot_production_data
```

If any is missing, recreate equivalent safety protection BEFORE destructive reset.

---

# 4. IP-ONLY TLS — NO DNS DEPENDENCY

Canonical production address:

```text
https://144.31.50.134
```

Do NOT require any DNS record.

Let's Encrypt IP address certificates are generally available and use the short-lived profile.

Preferred method:
- Certbot >= 5.4;
- `--preferred-profile shortlived`;
- `--ip-address 144.31.50.134`;
- challenge via standalone or webroot;
- automated renewal.

First inspect:

```text
certbot --version
```

If installed Certbot is too old for `--ip-address`:
- upgrade/install a supported Certbot version safely;
- prefer isolated supported installation method;
- do not break system Python;
- do not remove working Docker/system packages.

Request a publicly trusted IP certificate.

Example concept only; use syntax supported by installed Certbot:

```text
certbot certonly \
  --standalone \
  --preferred-profile shortlived \
  --ip-address 144.31.50.134
```

The resulting IP certificate is short-lived, so fully automated renewal is mandatory.

Install/copy:
- full chain to production Gateway server certificate path;
- private key to production Gateway server key path.

Set private key mode 0600.

Do NOT touch Technoreboot CLIENT CA.

Required:

```text
TLS_IDENTIFIER = 144.31.50.134
TLS_PUBLIC_TRUST = true
TLS_IP_SAN_MATCH = true
TLS_SHORTLIVED_PROFILE = true
TLS_RENEWAL_AUTOMATED = true
TLS_RENEW_DRY_RUN = PASS
```

If Let's Encrypt IP issuance is temporarily unavailable because of ACME client compatibility:
- do NOT fall back to DNS;
- return `BLOCKED_IP_TLS_CLIENT_SUPPORT` with exact Certbot/client version and exact error.
- do NOT perform destructive reset unless a trusted IP certificate is installed.

---

# 5. PRODUCTION ENVIRONMENT HOST

Update VDS production environment/config to use:

```text
TECHNOREBOOT_HOSTNAME=144.31.50.134
```

Production links/redirects must resolve to:

```text
https://144.31.50.134
```

No required production route may depend on `atanov821.serv.host`.

Do not remove the hostname from documentation permanently; simply mark DNS/domain as deferred.

---

# 6. PRESERVE INFRASTRUCTURE

Before business reset verify these remain outside reset scope:

```text
/srv/technoreboot/data/auth
/srv/technoreboot/data/backups
/srv/technoreboot/secrets
/srv/technoreboot/deploy/pre_clean_reset
```

Preserve:
- client CA;
- OWNER certificate/identity;
- USER certificates;
- revocation registry;
- production secrets;
- IP server TLS;
- backup history;
- SSH keys;
- firewall;
- repository.

Never regenerate Client CA.

---

# 7. DISCOVER BUSINESS TABLES BEFORE RESET

Inspect SQLite schema.

Classify every table as:

```text
BUSINESS
TECHNICAL
REFERENCE
```

Business scope includes at minimum:
- products;
- product photos;
- inventory/stock;
- inventory movements;
- sales;
- sale items;
- payment/business transaction rows;
- repair orders;
- repair events/history/comments;
- external listings;
- Avito business/listing data;
- operational report/materialized business rows;
- related business history.

Do not leave stale business rows in dependent tables.

Create table-classification evidence in the report.

---

# 8. RESET VDS BUSINESS DATABASE TO EMPTY STATE

VDS stack must be stopped during reset.

Preferred:
- create a clean DB with current schema;
- seed only required technical/reference data;
- atomically replace live DB.

Alternative:
- transactional FK-safe DELETE of all business tables;
- reset relevant SQLite sequences;
- VACUUM.

Required final business counts:

```text
PRODUCTS = 0
SALES = 0
REPAIRS = 0
PRODUCT_PHOTOS = 0
EXTERNAL_LISTINGS = 0
INVENTORY_MOVEMENTS = 0
OTHER_BUSINESS_ROWS = 0
```

Sequences should restart from clean baseline where safe.

Do not delete schema/migrations/reference data required to start the app.

---

# 9. RESET VDS BUSINESS MEDIA

Clear live business media under:

```text
/srv/technoreboot/data/storage/
```

including:
- current product photos;
- archived old product photos;
- stale business media.

Historical media remains recoverable from the pre-reset backup.

Required:

```text
LIVE_STORAGE_BUSINESS_FILES = 0
```

Keep only explicit application/system placeholders if any; list them.

---

# 10. RESET AVITO BUSINESS STATE

Clear old Avito business/listing/import/cache/draft/history state.

Do not publish anything.

Preserve only infrastructure state that is not old business data.

Report:

```text
AVITO_BUSINESS_STATE_CLEARED:
PAIRING_PRESERVED_OR_RESET:
```

If extension pairing is reset, that is acceptable; document that re-pairing is required.

---

# 11. START CLEAN VDS

Start production/test-production stack.

Required:

```text
LOCAL_STACK_RUNNING = true
VDS_STACK_RUNNING = true
```

Both running is intentional:
- Local = DEV/TEST;
- VDS = real-user canonical data.

All 6 VDS services must be healthy.

Only Gateway exposes application ports.

---

# 12. IP-BASED HTTPS / MTLS VERIFICATION

From Owner PC verify using exactly:

```text
https://144.31.50.134
```

without disabling normal server certificate verification.

Required:

```text
PUBLIC_TLS_TRUSTED = true
IP_CERTIFICATE_VALID = true
HTTP_TO_HTTPS = PASS
NO_CLIENT_CERT = REJECTED
OWNER_CERT = ACCEPTED
USER_RBAC = PASS
REVOKED_CERT = REJECTED
```

OWNER routes:

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

USER:
- operational routes allowed;
- `/backups` 403;
- `/certificates` 403.

---

# 13. EMPTY BUSINESS STATE VERIFICATION

Verify VDS through DB and UI/API:

```text
PRODUCTS = 0
SALES = 0
REPAIRS = 0
PHOTOS = 0
EXTERNAL_LISTINGS = 0
INVENTORY_MOVEMENTS = 0
OTHER_BUSINESS_ROWS = 0
```

UI:
- no product cards;
- no sales;
- no repairs;
- empty cart;
- reports Today/Week/Year = 0;
- no stale active media/product links;
- Avito old business listings absent.

No permanent fake records.

If a write smoke test is strictly necessary:
- create one temporary record;
- verify;
- fully delete it;
- final state must return to zero.

---

# 14. CLIENT AUTH PRESERVATION

Verify exact Client CA fingerprint remains unchanged from local/master:

```text
a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d
```

Required:

```text
CLIENT_CA_SHA256_UNCHANGED = true
OWNER_CERT_PRESERVED = true
USER_CERTS_PRESERVED = true
REVOCATION_REGISTRY_PRESERVED = true
```

The same OWNER certificate must work:
- local `https://localhost:8443`;
- VDS `https://144.31.50.134`.

---

# 15. CODE-ONLY DEPLOYMENT SCRIPT

Use/finish:

```text
deploy/production/update_code_only.sh
```

This is the ONLY normal deployment mechanism for future application updates.

It MUST:
1. require production data guard;
2. create fresh VDS backup before update;
3. record pre-update counts;
4. pull/reset code to requested Git commit;
5. never copy local DB;
6. never copy local storage;
7. never copy local auth;
8. never copy local Avito mutable state;
9. never invoke bootstrap restore;
10. build/recreate containers;
11. wait for health;
12. verify counts unchanged;
13. rollback CODE if runtime fails.

Add/retain tests proving these rules.

---

# 16. RUN REAL CODE-ONLY SELF-TEST

Run the code-only deployment mechanism against VDS using the current approved commit.

Before:

```text
PRODUCTS = 0
SALES = 0
REPAIRS = 0
```

Run deployment.

After:

```text
PRODUCTS = 0
SALES = 0
REPAIRS = 0
AUTH_PRESERVED = true
PRODUCTION_DATA_GUARD_PRESENT = true
STACK_HEALTHY = true
```

Verify no local business file was copied to VDS.

---

# 17. CLEAN BASELINE PRODUCTION BACKUP

With VDS clean and running, create one new backup:

```text
CLEAN_IP_TEST_PRODUCTION_BASELINE
```

Verify archive:
- manifest valid;
- business data empty;
- auth present;
- Client CA exact;
- Avito state reflects clean state;
- persisted under VDS backups.

Record filename + SHA256.

---

# 18. LOCAL DEV NON-MUTATION

After all work verify local:

```text
LOCAL_PRODUCTS unchanged
LOCAL_SALES unchanged
LOCAL_REPAIRS unchanged
LOCAL_PHOTOS unchanged
LOCAL_EXTERNAL_LISTINGS unchanged
LOCAL_DB_SHA256 unchanged
LOCAL_CA_SHA256 unchanged
```

Local stack remains running.

Do not make local data match VDS.

---

# 19. FIREWALL / NETWORK

Verify:

```text
PUBLIC_PORTS = SSH,80,443
INTERNAL_PUBLIC_PORTS = 0
FIREWALL_ACTIVE = true
SSH_KEY_ACCESS = true
```

Canonical user URL is IP only for now.

---

# 20. DOCUMENTATION

Create:

`docs/stage08d_r1r2_ip_only_clean_test_production_activation.md`

Update:

`docs/production_status.md`

`docs/production_deployment_model.md`

Create:

`reports/stage08d_r1r2_ip_only_clean_activation_report.md`

Update:

`logs/2026-09-12.md`

Preserve prompt under `.agents/received_prompts`.

Documentation must state:

```text
CURRENT_PRODUCTION_URL = https://144.31.50.134
DOMAIN_NAME = deferred / not required
LOCAL = DEV / TEST
VDS = canonical real-user data
FUTURE_DEPLOYS = code only
LOCAL BUSINESS DATA MUST NEVER BE RESTORED TO VDS
```

---

# 21. TESTS

Run:
- production data guard tests;
- production baseline tests;
- backup tests;
- mTLS/auth tests;
- code-only deploy tests;
- empty-state smoke.

Required:

```text
FAILED = 0
```

---

# 22. GIT / SECRET SAFETY

Never commit:
- SSH keys;
- passwords;
- production.env;
- server private TLS key;
- client private keys;
- backup ZIP;
- runtime DB;
- VDS media.

Commit safe:
- deployment script changes;
- tests;
- docs;
- reports;
- logs;
- received prompt.

Push `origin/main`.

Final worktree clean.

---

# 23. FINAL REPORT CONTRACT

Return:

```text
# Stage 08D-R1R2 — IP-Only Clean Test-Production Activation

## Environment
LOCAL_ROLE: DEV_TEST
VDS_ROLE: CANONICAL_REAL_USER
LOCAL_STACK_RUNNING:
VDS_STACK_RUNNING:
CANONICAL_URL: https://144.31.50.134
DNS_REQUIRED: false

## IP TLS
CERTBOT_VERSION:
IP_CERT_ISSUED:
TLS_IDENTIFIER:
TLS_ISSUER:
TLS_PUBLIC_TRUST:
TLS_IP_SAN_MATCH:
TLS_SHORTLIVED_PROFILE:
TLS_RENEWAL_AUTOMATED:
TLS_RENEW_DRY_RUN:

## Safety
PRE_RESET_BACKUP_FILE:
PRE_RESET_BACKUP_SHA256:
PRODUCTION_DATA_GUARD:

## Preserved Infrastructure
CLIENT_CA_PRESERVED:
OWNER_CERT_PRESERVED:
USER_CERTS_PRESERVED:
REVOCATION_REGISTRY_PRESERVED:
BACKUP_HISTORY_PRESERVED:
PRODUCTION_SECRETS_PRESERVED:

## Clean VDS
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

## Runtime
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
SAME_OWNER_CERT_WORKS_LOCAL_AND_VDS:

## Code-Only Deployment
UPDATE_SCRIPT:
PRE_UPDATE_BACKUP_REQUIRED:
LOCAL_DB_COPY_FORBIDDEN:
LOCAL_MEDIA_COPY_FORBIDDEN:
LOCAL_AUTH_COPY_FORBIDDEN:
BOOTSTRAP_RESTORE_FORBIDDEN:
CODE_ONLY_SELF_TEST:
POST_DEPLOY_DATA_PRESERVED:

## Clean Baseline Backup
BASELINE_BACKUP_FILE:
BASELINE_BACKUP_SHA256:
BASELINE_BUSINESS_DATA_EMPTY:
BASELINE_AUTH_CA_MATCH:

## Local Safety
LOCAL_PRODUCTS_UNCHANGED:
LOCAL_SALES_UNCHANGED:
LOCAL_REPAIRS_UNCHANGED:
LOCAL_PHOTOS_UNCHANGED:
LOCAL_EXTERNAL_LISTINGS_UNCHANGED:
LOCAL_DB_SHA256_UNCHANGED:
LOCAL_CA_SHA256_UNCHANGED:

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
TECHNOREBOOT_STAGE08D_R1R2_IP_ONLY_CLEAN_TEST_PRODUCTION_ACTIVE

PRODUCTION_URL: https://144.31.50.134
DOMAIN_DEFERRED: true
LOCAL_AND_VDS_MAY_RUN_SIMULTANEOUSLY: true
VDS_DATA_IS_CANONICAL: true
DO_NOT_SYNC_LOCAL_BUSINESS_DATA_TO_VDS: true
FUTURE_DEPLOYS_CODE_ONLY: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- trusted IP certificate cannot be issued/renewed;
- pre-reset backup invalid;
- auth/CA would be lost;
- reset leaves business data;
- local data changes;
- code-only deployment can overwrite VDS data;
- tests fail.

---

# 24. STOP

After successful activation:

STOP.

Leave:
- local DEV running;
- VDS clean real-user environment running.

Use:

```text
https://144.31.50.134
```

Do not wait for DNS.
Do not sync business data from local to VDS.
Wait for Owner browser acceptance.
