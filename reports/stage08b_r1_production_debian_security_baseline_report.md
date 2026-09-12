# Stage 08B-R1 — Production Debian Docker Configuration and Security Baseline Report

## Preflight
- **HEAD:** `a81d087883a26f6ee604280396c73ce33df7877f`
- **GIT_STATUS:** Modified application hardening files (`admin-shell`, `core`, `inventory-sales-module`, `repairs-module`), untracked prompt and production deploy configuration.
- **LIVE_COUNTS:**
  - `PRODUCT_IDS` (50): `[1..50]`
  - `SALE_IDS` (52): `[1..52]`
  - `REPAIR_IDS` (66): `[1..66]`
  - `PHOTO_IDS` (50): `[1..48, 50, 51]`
  - `EXTERNAL_LISTING_IDS` (50): `[1..50]`

---

## Production Compose
- **FILE:** `deploy/production/docker-compose.prod.yml`
- **SERVICES:** `core`, `admin-shell`, `inventory-sales-module`, `repairs-module`, `avito-module`, `gateway`
- **PUBLIC_SERVICES:** `gateway` only
- **PUBLIC_PORTS:** `80/tcp` (HTTP redirect), `443/tcp` (HTTPS with mTLS)
- **INTERNAL_PUBLISHED_PORTS:** 0 (all internal services communicate exclusively via `technoreboot-network`)
- **DATA_ROOT:** `${TECHNOREBOOT_DATA_ROOT:-/srv/technoreboot/data}`
- **HOSTNAME_VARIABLE:** `TECHNOREBOOT_HOSTNAME` (required, evaluated via Nginx `envsubst` filter)

---

## TLS / mTLS
- **SERVER_TLS_CONFIG:** Configurable via `SERVER_TLS_CERT_PATH` and `SERVER_TLS_KEY_PATH` (decoupled from client CA)
- **CLIENT_CA_CONFIG:** Configurable via `CLIENT_CA_CERT_PATH` (points to restored/active Technoreboot Root CA)
- **MTLS_REQUIRED:** `true` (enforced at Gateway via `ssl_client_certificate` and subrequest to `/internal-auth/verify`)
- **OWNER_POLICY:** Unrestricted access to all operational routes, plus exclusive access to `/backups` and `/certificates`
- **USER_POLICY:** Access to operational routes (Inventory, Sales, Repairs, Avito); strictly rejected on `/backups` and `/certificates` with HTTP 403 Forbidden
- **REVOCATION_POLICY:** Revoked certificates listed in `registry.json` are rejected by `auth_manager` with HTTP 403 Forbidden

---

## Secrets
- **CRITICAL_ENV_VARS:** `TECHNOREBOOT_HOSTNAME`, `TECHNOREBOOT_DATA_ROOT`, `SERVER_TLS_CERT_PATH`, `SERVER_TLS_KEY_PATH`, `CLIENT_CA_CERT_PATH`, `APP_ENV`, `CORE_API_TOKEN`, `CART_SESSION_SECRET`
- **INSECURE_DEFAULTS_FOUND:** Development fallback defaults existed in local development modules (`dev-token`, `technoreboot_secret_cart_key_mvp`)
- **INSECURE_DEFAULTS_ALLOWED_IN_PROD:** 0 (Pydantic model validators fail fast on container startup if insecure defaults or missing tokens are detected when `APP_ENV=production`)
- **REAL_SECRETS_COMMITTED:** 0 (template `deploy/production/env.production.example` contains variable descriptions only; `.env` is gitignored)

---

## Persistence
- **DB:** `${TECHNOREBOOT_DATA_ROOT}/db:/data/db` (persistent SQLite database `technoreboot.db`)
- **STORAGE:** `${TECHNOREBOOT_DATA_ROOT}/storage:/data/storage` (product photos and media files)
- **AUTH:** `${TECHNOREBOOT_DATA_ROOT}/auth:/app/auth-data` (PKI CA, certificates, client registry)
- **AVITO_STATE:** `${TECHNOREBOOT_DATA_ROOT}/avito-module:/app/data` (session pairing and cookies)
- **BACKUPS:** `${TECHNOREBOOT_DATA_ROOT}/backups:/data/backups` (backup archives)

---

## Container Security
- **PRIVILEGED_CONTAINERS:** 0 (`privileged: true` is not set on any service)
- **HOST_NETWORK:** 0 (`network_mode: host` is not set on any service)
- **DOCKER_SOCKET_MOUNTS:** 0 (`/var/run/docker.sock` is nowhere mounted)
- **HOST_ROOT_MOUNTS:** 0 (only persistent data root is mounted)
- **SOURCE_BIND_MOUNTS:** 0 in production compose (code is built into image layers)
- **LOG_ROTATION:** Bounded JSON file logging on all services (`max-size: "10m"`, `max-file: "5"`)
- **RESTART_POLICIES:** `restart: unless-stopped` on all 6 services
- **HEALTHCHECKS:** Explicit health checks defined for all 6 services

---

## Fresh Build Proof
- **FRESH_CLONE:** Verified in isolated sandbox checkout directly from `origin/main` (outside workspace, 0 files copied)
- **FRESH_CLONE_HEAD:** `0a056f2352064f2326fe917249b552804cadb0d1` (matches `origin/main` exactly)
- **PREBUILT_IMAGES_REQUIRED:** `false` (built directly from fresh clone Dockerfiles)
- **BUILD_RESULT:** PASS (all images built deterministically from fresh clone source)

---

## Isolated Production Simulation
- **PROJECT:** `technoreboot-prod-sim-sim_1789195097_808b63`
- **GATEWAY_URL:** `https://127.0.0.1:18443` (HTTP redirect on `18080`)
- **GATEWAY_HTTPS:** PASS (HTTP 200 with valid client certificate)
- **NO_CERT_REJECTED:** PASS (HTTP 403 Forbidden returned without client cert)
- **OWNER_CERT_ACCEPTED:** PASS (HTTP 200 on all canonical routes)
- **PRODUCTS:** PASS (`/inventory/products` returned HTTP 200)
- **SALES:** PASS (`/inventory/sales` returned HTTP 200)
- **REPAIRS:** PASS (`/repairs/repairs` returned HTTP 200)
- **AVITO_EXTENSION:** PASS (`/avito/extension` returned HTTP 200)
- **BACKUPS:** PASS (`/backups` returned HTTP 200 for OWNER, HTTP 403 for USER)
- **INTERNAL_SERVICES_PUBLICLY_EXPOSED:** `false` (zero host port bindings on internal services)
- **TEARDOWN:** PASS (containers stopped, volumes and sandbox cleanly removed)

---

## Live Data Safety
- **PRODUCT_IDS_UNCHANGED:** `true` (50 products: [1..50])
- **SALE_IDS_UNCHANGED:** `true` (52 sales: [1..52])
- **REPAIR_IDS_UNCHANGED:** `true` (66 repairs: [1..66])
- **PHOTO_IDS_UNCHANGED:** `true` (50 photos: [1..48, 50, 51])
- **EXTERNAL_LISTING_IDS_UNCHANGED:** `true` (50 external listings: [1..50])
- **REAL_PRODUCTS_DELETED:** 0

---

## Deployment Runbook
- **PATH:** `docs/production_debian_deployment.md`
- **SECURITY_BASELINE_DOC:** `docs/stage08b_r1_production_debian_security_baseline.md`
- **REAL_VDS_TOUCHED:** `false`
- **DNS_CHANGED:** `false`

---

## Exact Test Results
- **TESTS_A_THROUGH_X:** 24 passed (`tests/test_stage08b_r1_production_baseline.py`)
- **TESTS_Y_AND_Z:** 2 passed (`tests/test_stage08b_r1_production_simulation.py`)
- **TOTAL_STAGE08B_TESTS:** 26 passed, 0 failed
- **REGRESSION_SUITES:**
  - `admin-shell/tests`: 92 passed, 1 skipped
  - `inventory-sales-module/tests`: 154 passed
  - `repairs-module/tests`: 34 passed
  - `core/tests`: 255 passed
  - `avito-module/tests`: 154 passed
  - `chrome-extension/technoreboot-avito/tests`: 126 passed
  - **TOTAL_REGRESSION:** 815 passed, 1 skipped

---

## Status
- **FINAL_STATUS:** `TECHNOREBOOT_STAGE08B_R1_PRODUCTION_BASELINE_READY_FOR_OWNER_CHECK`
- **PRODUCTION_DEPLOYMENT_NOT_STARTED:** `true`
- **DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE:** `true`
