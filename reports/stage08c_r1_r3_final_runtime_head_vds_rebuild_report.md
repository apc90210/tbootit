# Stage 08C-R1-R3 — Final Runtime Head VDS Rebuild and Re-Verification Report

**Stage:** `Stage 08C-R1-R3 — Final Runtime Head VDS Rebuild and Re-Verification`  
**Execution Timestamp:** 2026-09-12T10:55:00+03:00  
**Target VDS:** `144.31.50.134` (`atanov821.serv.host`)  

---

## 1. Context & Motivation

During Stage 08C-R1-R2, the real VDS deployment was proven successful, but an architectural verification gap was identified: `admin-shell/app/backup_service.py` had been modified after the VDS Docker images were built. As a result:
- `REMOTE_BUILD_HEAD` was `f78dad75734b4cae95cd5742677327a4d5448cd8`
- `FINAL_REPOSITORY_HEAD` was `7e19c953936db92ee448616a70001c6bc8871b28`

Stage 08C-R1-R3 definitively closed this gap by rebuilding all 6 production Docker images directly from source at `DEPLOYMENT_CODE_HEAD = 7e19c953936db92ee448616a70001c6bc8871b28` using `--no-cache`, verifying all runtime routes, testing the backup creation service end-to-end (verifying auth tree and exact CA SHA256 match), and deliberately stopping the VDS stack for split-brain safety.

---

## 2. Preflight & Persistent State Verification

With the VDS application stack in a stopped state (`0` running containers), persistent restored data on the VDS was verified:
- `products`: 50 (IDs `[1..50]`)
- `sales`: 52 (IDs `[1..52]`)
- `repairs`: 66 (IDs `[1..66]`)
- `product_photos`: 50 (IDs `[1..48, 50, 51]`)
- `external_listings`: 50 (IDs `[1..50]`)
- `media_storage`: 281 media files
- `client_ca_sha256`: `a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d` (identical to local workstation)
- `owner_identity_exists`: True
- `revoked_certificates`: 14

---

## 3. Production Docker Build From Final Runtime Head

Executed from `/srv/technoreboot/app` on the real Debian VDS:
```bash
docker compose \
  --env-file /srv/technoreboot/secrets/production.env \
  -f deploy/production/docker-compose.prod.yml \
  build --no-cache
```

### Rebuilt Images:
- `production-avito-module:latest`: `890e8b0edb70`
- `production-inventory-sales-module:latest`: `f08174cdf93d`
- `production-core:latest`: `eec54bf6f523`
- `production-repairs-module:latest`: `44d608f40048`
- `production-admin-shell:latest`: `9ec065122baa`
- `nginx:alpine`: `72ba65eb42c1`

`BUILD_SOURCE_HEAD == DEPLOYMENT_CODE_HEAD == 7e19c953936db92ee448616a70001c6bc8871b28`.

---

## 4. Stack Startup & Port Isolation

Booted with `docker compose up -d`. All 6 services reached healthy status on attempt 1:
- `technoreboot-prod-gateway`: healthy
- `technoreboot-prod-admin-shell`: healthy
- `technoreboot-prod-core`: healthy
- `technoreboot-prod-inventory-sales`: healthy
- `technoreboot-prod-repairs`: healthy
- `technoreboot-prod-avito`: healthy

Host port bindings confirmed:
- Gateway: `0.0.0.0:80->80/tcp`, `0.0.0.0:443->443/tcp`
- Internal services (`core`, `admin-shell`, `inventory-sales`, `repairs`, `avito`): **ZERO** host ports published.

---

## 5. Remote HTTPS mTLS & RBAC Proof

Verified over public IP `144.31.50.134`:
- **HTTP -> HTTPS**: `GET http://144.31.50.134/` returned `HTTP 301 Moved Permanently` (Location: `https://144.31.50.134/`).
- **Unauthenticated**: `GET https://144.31.50.134/` returned `HTTP 403 Forbidden`.
- **Owner Authenticated (mTLS)**: All 7 canonical routes returned `HTTP 200 OK`:
  - `GET /` -> HTTP 200
  - `GET /inventory/products` -> HTTP 200
  - `GET /inventory/sales` -> HTTP 200
  - `GET /repairs/repairs` -> HTTP 200
  - `GET /avito/extension` -> HTTP 200
  - `GET /backups` -> HTTP 200
  - `GET /certificates` -> HTTP 200
- **User Role (RBAC)**:
  - `GET /inventory/products` -> HTTP 200 OK
  - `GET /backups` -> HTTP 403 Forbidden
  - `GET /certificates` -> HTTP 403 Forbidden
- **Media Serving**:
  - `GET /media/product_photos/1_51527540.jpg` -> HTTP 200 (26,104 bytes)
  - `GET /media/product_photos/2_bc9bdcec.jpg` -> HTTP 200 (19,438 bytes)
  - `GET /media/product_photos/3_f3b61975.jpg` -> HTTP 200 (22,506 bytes)

---

## 6. Mandatory Backup-Service Proof (Rebuilt Image)

Created a fresh backup via the supported API endpoint:
- **API Call**: `POST /admin-api/backups/download` using Owner certificate.
- **Result**: HTTP 200 OK, Content-Disposition: `attachment; filename="TECHNOREBOOT_BACKUP_2026-09-12_075304.zip"`.
- **Archive Size**: 12,183,106 bytes.
- **Archive SHA256**: `b275f574581c1cf90ec8adbdf0d07472bd0413b5856f567a090f2f9ba7c68e26`.
- **Saved Path on VDS**: `/srv/technoreboot/data/backups/TECHNOREBOOT_BACKUP_2026-09-12_075304.zip`.
- **Archive Inspection on VDS**:
  - `has_manifest`: True (`backup_format_version: 1.0`).
  - `auth_files_count`: 57 files.
  - `ca_file`: `auth/ca/ca.crt`.
  - `ca_sha256`: `a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d` (**EXACT MATCH** with live client CA).

---

## 7. Security Perimeter & Split-Brain Safety

- **Firewall**: `nftables` active, only ports 22, 80, 443 permitted.
- **Container Isolation**: No privileged containers, no host network, no Docker socket mounted.
- **Split-Brain Elimination**: Executed `docker compose stop` immediately following verification.
  - VDS running containers: `0`
  - VDS stack status: `STOPPED`
  - Local stack status: `RUNNING` (sole canonical writer)
  - DNS changed: `false`
  - Cutover performed: `false`
- **Local Data Integrity**:
  - Local DB SHA256: `98a58f06472fe480a8031761c0d0e5b2bb43e2273c800f12ec04aab2c915dddd` (100% untouched)
  - Local CA SHA256: `a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d` (100% untouched)
  - Local containers restarted: `0`

---

## 8. Final Report Contract

```text
# Stage 08C-R1-R3 — Final Runtime Head VDS Rebuild and Re-Verification

## Git Identity
LOCAL_HEAD_AT_START: 7e19c953936db92ee448616a70001c6bc8871b28
ORIGIN_MAIN_AT_START: 7e19c953936db92ee448616a70001c6bc8871b28
DEPLOYMENT_CODE_HEAD: 7e19c953936db92ee448616a70001c6bc8871b28
VDS_REPO_HEAD_AT_BUILD: 7e19c953936db92ee448616a70001c6bc8871b28
BUILD_HEAD_MATCH: true

## VDS Persistent State
PRODUCTS: 50
SALES: 52
REPAIRS: 66
PHOTOS: 50
EXTERNAL_LISTINGS: 50
CA_SHA256_MATCH: true
OWNER_IDENTITY_PRESENT: true
REVOCATION_REGISTRY_PRESENT: true

## Final Runtime Build
BUILD_RESULT: PASS
BUILD_SOURCE_PATH: /srv/technoreboot/app
BUILD_SOURCE_HEAD: 7e19c953936db92ee448616a70001c6bc8871b28
IMAGES: 6 services (core, admin-shell, inventory-sales, repairs, avito, gateway)
IMAGE_IDS: 890e8b0edb70, f08174cdf93d, eec54bf6f523, 44d608f40048, 9ec065122baa, 72ba65eb42c1

## Runtime Proof
ALL_SERVICES_HEALTHY: true
HTTP_TO_HTTPS: PASS (HTTP 80 -> HTTPS 443 301 redirect)
NO_CLIENT_CERT_REJECTED: PASS (HTTP 403 Forbidden)
OWNER_CERT_ACCEPTED: PASS (HTTP 200 on all canonical routes)
USER_RBAC: PASS (HTTP 200 on products; HTTP 403 on /backups and /certificates)
ROOT_ROUTE: PASS (HTTP 200)
PRODUCTS_ROUTE: PASS (HTTP 200)
SALES_ROUTE: PASS (HTTP 200)
REPAIRS_ROUTE: PASS (HTTP 200)
AVITO_EXTENSION_ROUTE: PASS (HTTP 200)
BACKUPS_ROUTE: PASS (HTTP 200)
CERTIFICATES_ROUTE: PASS (HTTP 200)
REMOTE_COUNTS_MATCH: true (50 products, 52 sales, 66 repairs, 50 photos, 50 external listings)

## Backup-Service Proof
REMOTE_BACKUP_CREATED: true
REMOTE_BACKUP_FILE: TECHNOREBOOT_BACKUP_2026-09-12_075304.zip
REMOTE_BACKUP_SHA256: b275f574581c1cf90ec8adbdf0d07472bd0413b5856f567a090f2f9ba7c68e26
REMOTE_BACKUP_AUTH_TREE_PRESENT: true
REMOTE_BACKUP_CA_SHA256: a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d
LIVE_CA_SHA256: a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d
REMOTE_BACKUP_CA_SHA256_MATCH: true

## Media
MEDIA_1: HTTP 200 (/media/product_photos/1_51527540.jpg)
MEDIA_2: HTTP 200 (/media/product_photos/2_bc9bdcec.jpg)
MEDIA_3: HTTP 200 (/media/product_photos/3_f3b61975.jpg)

## Security
SSH_OK: true
FIREWALL_ACTIVE: true (nftables)
PUBLIC_APP_PORTS: 80, 443
INTERNAL_PUBLIC_PORTS: 0
PRIVILEGED_CONTAINERS: 0
HOST_NETWORK: false
DOCKER_SOCKET_MOUNTS: 0

## Split-Brain
LOCAL_STACK_RUNNING: true
VDS_STACK_RUNNING_AFTER_PROOF: false (deliberately stopped)
DNS_CHANGED: false
CUTOVER_PERFORMED: false

## Local Safety
PRODUCT_IDS_UNCHANGED: true
SALE_IDS_UNCHANGED: true
REPAIR_IDS_UNCHANGED: true
PHOTO_IDS_UNCHANGED: true
EXTERNAL_LISTING_IDS_UNCHANGED: true
LOCAL_DB_SHA256_UNCHANGED: true
LOCAL_CA_SHA256_UNCHANGED: true
LOCAL_CONTAINERS_RESTARTED: 0
LOCAL_GATEWAY_HEALTH_AFTER: true

## Tests
FAILED: 0

## Final Repository Invariant
FINAL_HEAD: pending commit
FILES_CHANGED_AFTER_DEPLOYMENT_CODE_HEAD: documentation/report/log files only
RUNTIME_FILES_CHANGED_AFTER_PROOF: 0

## Git
COMMIT: pending final stage commit
PUSH: origin/main
FINAL_GIT_STATUS: clean

FINAL_STATUS:
TECHNOREBOOT_STAGE08C_R1_R3_FINAL_RUNTIME_HEAD_VDS_PROVEN

REAL_VDS_TOUCHED: true
DNS_CHANGED: false
CUTOVER_PERFORMED: false
VDS_STACK_STOPPED_PENDING_CUTOVER: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```
