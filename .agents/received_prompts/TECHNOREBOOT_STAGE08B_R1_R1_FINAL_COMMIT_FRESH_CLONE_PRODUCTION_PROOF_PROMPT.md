# TECHNOREBOOT — Stage 08B-R1-R1
## Final committed production baseline fresh-clone proof

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 08B-R1-R1 — Final Commit Fresh-Clone Production Proof`

# 0. WHY THIS REVISION EXISTS

Stage08B-R1 is NOT accepted yet.

The implementation/report is strong, but the production simulation was executed from a fresh clone at:

```text
FRESH_CLONE_HEAD: a81d087883a26f6ee604280396c73ce33df7877f
```

while the completed Stage08B-R1 changes were committed later as:

```text
HEAD_AFTER: 0a056f2352064f2326fe917249b552804cadb0d1
```

Therefore the previous fresh-clone proof did NOT prove that the final committed production configuration and shared-code security changes can be cloned from `origin/main` and deployed successfully.

This revision closes only that gap.

Do NOT redesign production configuration.
Do NOT deploy the real VDS.
Do NOT change DNS.
Do NOT modify live business data.
Do NOT introduce unrelated features.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08B_R1_R1_FINAL_COMMIT_FRESH_CLONE_PRODUCTION_PROOF_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08B_R1_R1_FINAL_COMMIT_FRESH_CLONE_PRODUCTION_PROOF_PROMPT.md`

# 1. PREFLIGHT

Record:

```text
CURRENT_LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
GIT_STATUS:
LIVE_GATEWAY:
LIVE_PRODUCTS:
LIVE_SALES:
LIVE_REPAIRS:
LIVE_PHOTOS:
LIVE_EXTERNAL_LISTINGS:
```

Required:

```text
CURRENT_LOCAL_HEAD == ORIGIN_MAIN_HEAD
```

Capture exact live ID sets before testing:
- products;
- sales;
- repairs;
- product photos;
- external listings.

# 2. VERIFY PRODUCTION FILES ARE COMMITTED

From the current repository, prove that the following are Git-tracked at `origin/main`:

```text
deploy/production/docker-compose.prod.yml
deploy/production/nginx/nginx.conf.template
deploy/production/env.production.example
deploy/production/README.md
docs/production_debian_deployment.md
docs/stage08b_r1_production_debian_security_baseline.md
scripts/simulate_production_stack.py
tests/test_stage08b_r1_production_baseline.py
tests/test_stage08b_r1_production_simulation.py
```

Also verify that the shared source changes introduced by Stage08B-R1 are committed.

Report:

```text
PRODUCTION_FILES_TRACKED:
UNTRACKED_REQUIRED_FILES:
```

Acceptance requires zero untracked required files.

# 3. CREATE A BRAND-NEW CLONE OF FINAL ORIGIN/MAIN

Delete any previous test clone.

Create a brand-new clone directly from `origin/main` into a temporary directory outside the live workspace.

Required:

```text
FRESH_CLONE_PATH:
FRESH_CLONE_HEAD:
ORIGIN_MAIN_HEAD:
HEAD_MATCH:
```

Acceptance:

```text
FRESH_CLONE_HEAD == ORIGIN_MAIN_HEAD
```

Do NOT:
- copy files from `C:\tbootit` into the fresh clone;
- mount the live source tree;
- mount live mutable data;
- reuse generated config from the current working directory.

Everything used by the production proof must come from the fresh clone plus generated test-only secrets/certs/data.

# 4. PRODUCTION COMPOSE VALIDATION FROM FRESH CLONE

Inside the fresh clone:

1. create test-only production env values;
2. use a temporary data root;
3. generate test-only TLS/client CA material;
4. run:

```text
docker compose -f deploy/production/docker-compose.prod.yml config
```

Prove:

- Compose parses;
- only Gateway publishes host ports;
- internal services publish zero host ports;
- production hostname comes from variable;
- data root is temporary sandbox;
- no live `C:\tbootit\data` path appears;
- no `localhost` / `127.0.0.1` dependency exists in production service routing;
- no development secret fallback is accepted.

# 5. BUILD ALL PRODUCTION IMAGES FROM FINAL FRESH CLONE

From the fresh clone only:

```text
docker compose -f deploy/production/docker-compose.prod.yml build --no-cache
```

or equivalent deterministic fresh build.

Use a unique Compose project/image namespace.

Report:

```text
BUILT_FROM_PATH:
BUILT_FROM_HEAD:
IMAGES:
IMAGE_IDS:
PREBUILT_LIVE_IMAGES_USED:
```

Acceptance:

```text
BUILT_FROM_HEAD == ORIGIN_MAIN_HEAD
PREBUILT_LIVE_IMAGES_USED = false
```

# 6. FINAL-COMMIT ISOLATED PRODUCTION SIMULATION

Run the complete production simulation using only the fresh clone.

Use:
- separate Compose project;
- alternate ports (not 8443);
- temporary data root;
- test-only TLS and client certs.

Verify:

```text
GATEWAY_HTTPS = PASS
HTTP_TO_HTTPS = PASS
NO_CERT_REJECTED = PASS
OWNER_CERT_ACCEPTED = PASS
USER_OWNER_ONLY_ROUTES_REJECTED = PASS
PRODUCTS = PASS
SALES = PASS
REPAIRS = PASS
AVITO_EXTENSION = PASS
BACKUPS_OWNER = PASS
CERTIFICATES_OWNER = PASS
INTERNAL_HOST_PORTS = 0
```

The production simulation must execute the final committed:
- production Compose;
- Nginx template;
- secret validation;
- shared app code.

# 7. FAIL-FAST SECRET PROOF FROM FRESH CLONE

From the fresh clone prove production startup/config refuses known insecure values.

At minimum:

```text
APP_ENV=production
CORE_API_TOKEN=dev-token
```

must fail.

Also verify the production cart/session secret rejects the known dev default.

Report:

```text
CORE_DEV_TOKEN_REJECTED:
CART_DEV_SECRET_REJECTED:
EMPTY_CRITICAL_SECRET_REJECTED:
```

Do not print real secrets.

# 8. SECURITY CONFIG PROOF

From resolved fresh-clone production Compose report:

```text
PUBLIC_SERVICES:
PUBLIC_PORTS:
INTERNAL_PUBLISHED_PORTS:
PRIVILEGED_CONTAINERS:
HOST_NETWORK_SERVICES:
DOCKER_SOCKET_MOUNTS:
HOST_ROOT_MOUNTS:
SOURCE_BIND_MOUNTS:
NO_NEW_PRIVILEGES:
LOG_ROTATION:
RESTART_POLICIES:
HEALTHCHECKS:
```

Required:
- only gateway public;
- no privileged;
- no host networking;
- no Docker socket;
- no host root;
- no source-code bind mounts.

# 9. LIVE WORKSPACE ISOLATION

Before and after test compare exact live state:

```text
PRODUCT_IDS
SALE_IDS
REPAIR_IDS
PHOTO_IDS
EXTERNAL_LISTING_IDS
```

Also verify live containers were not restarted by the proof.

Required:

```text
PRODUCT_IDS_UNCHANGED: true
SALE_IDS_UNCHANGED: true
REPAIR_IDS_UNCHANGED: true
PHOTO_IDS_UNCHANGED: true
EXTERNAL_LISTING_IDS_UNCHANGED: true
LIVE_CONTAINERS_RESTARTED: 0
LIVE_GATEWAY_HEALTH_AFTER: true
```

# 10. TEARDOWN

After verification:
- remove only fresh-clone simulation containers/networks/volumes;
- remove temporary clone;
- remove test-only TLS/data;
- do NOT remove live images/data/backups;
- verify the normal local stack remains healthy.

# 11. REQUIRED TESTS

Run from the final fresh clone:

```text
pytest tests/test_stage08b_r1_production_baseline.py
pytest tests/test_stage08b_r1_production_simulation.py
```

Also run production simulation directly once.

If shared source changed after Stage08B-R1, run affected module regressions.

Required:

```text
FAILED = 0
```

# 12. DOCUMENTATION

Create:

`reports/stage08b_r1_r1_final_commit_fresh_clone_proof_report.md`

Update:

`reports/stage08b_r1_production_debian_security_baseline_report.md`

`docs/stage08b_r1_production_debian_security_baseline.md`

`logs/2026-09-12.md`

Preserve:

`.agents/received_prompts/TECHNOREBOOT_STAGE08B_R1_R1_FINAL_COMMIT_FRESH_CLONE_PRODUCTION_PROOF_PROMPT.md`

# 13. GIT / SAFETY

Do not commit:
- test TLS keys;
- generated secrets;
- runtime DB;
- backup ZIP;
- temporary clone;
- temporary production data;
- real certificates/private keys.

Commit reports/tests/docs only if changes are required.

Push `origin/main`.
Verify clean worktree.

# 14. FINAL REPORT CONTRACT

Return:

```text
# Stage 08B-R1-R1 — Final Commit Fresh-Clone Production Proof

## Git Identity
LOCAL_HEAD:
ORIGIN_MAIN_HEAD:
FRESH_CLONE_HEAD:
ALL_MATCH:

## Production Files
PRODUCTION_FILES_TRACKED:
UNTRACKED_REQUIRED_FILES:

## Fresh Clone Compose
COMPOSE_FILE:
CONFIG_RESULT:
PUBLIC_SERVICES:
PUBLIC_PORTS:
INTERNAL_PUBLISHED_PORTS:
DATA_ROOT:
HOSTNAME_VARIABLE:

## Fresh Build
BUILT_FROM_PATH:
BUILT_FROM_HEAD:
IMAGES:
IMAGE_IDS:
PREBUILT_LIVE_IMAGES_USED:

## Secret Fail-Fast
CORE_DEV_TOKEN_REJECTED:
CART_DEV_SECRET_REJECTED:
EMPTY_CRITICAL_SECRET_REJECTED:

## Security
PRIVILEGED_CONTAINERS:
HOST_NETWORK:
DOCKER_SOCKET_MOUNTS:
HOST_ROOT_MOUNTS:
SOURCE_BIND_MOUNTS:
LOG_ROTATION:
RESTART_POLICIES:
HEALTHCHECKS:

## Final-Commit Production Simulation
PROJECT:
GATEWAY_URL:
HTTP_TO_HTTPS:
GATEWAY_HTTPS:
NO_CERT_REJECTED:
OWNER_CERT_ACCEPTED:
USER_OWNER_ONLY_ROUTES_REJECTED:
PRODUCTS:
SALES:
REPAIRS:
AVITO_EXTENSION:
BACKUPS:
CERTIFICATES:
INTERNAL_SERVICES_PUBLICLY_EXPOSED:
TEARDOWN:

## Live Safety
PRODUCT_IDS_UNCHANGED:
SALE_IDS_UNCHANGED:
REPAIR_IDS_UNCHANGED:
PHOTO_IDS_UNCHANGED:
EXTERNAL_LISTING_IDS_UNCHANGED:
LIVE_CONTAINERS_RESTARTED:
LIVE_GATEWAY_HEALTH_AFTER:

## Tests
PRODUCTION_BASELINE:
PRODUCTION_SIMULATION:
FAILED:

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08B_R1_R1_FINAL_COMMITTED_PRODUCTION_BASELINE_PROVEN

REAL_VDS_TOUCHED: false
DNS_CHANGED: false
PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If fresh clone HEAD differs from `origin/main`, return BLOCKED.

If the fresh-clone proof uses files copied from the live working tree, return BLOCKED.

If live business data changes, return BLOCKED.

# 15. STOP

After final-commit fresh-clone proof, cleanup, docs, commit/push and report:

STOP.

Do not deploy the real VDS.
Wait for Owner acceptance.
