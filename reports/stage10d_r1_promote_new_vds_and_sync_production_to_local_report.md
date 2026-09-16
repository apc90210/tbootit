# TechnoReboot — Stage 10D-R1 Report
## Promote New VDS as Canonical Production + Sync Production Data to LOCAL

**Execution Date:** 2026-09-16  
**LOCAL Workspace:** `C:\tbootit`  
**Primary Production VDS:** `144.31.15.88` (Debian 13, `atanov822.serv.host`)  
**Legacy Server:** `144.31.50.134` (`OLD_VDS_STATUS=legacy-retained`, `OLD_VDS_ROUTINE_SUPPORT=false`)  

---

## 1. Executive Summary

Following Owner confirmation that the NEW VDS `144.31.15.88` operates correctly and reliably (both with and without Amnezia VPN), Stage 10D-R1 has successfully:
1. Promoted `144.31.15.88` to the **sole canonical primary production server** and authoritative source of truth for business data.
2. Retired the old VDS `144.31.50.134` as `legacy-retained` with routine support disabled.
3. Created a verified fresh backup snapshot of live business data directly on `144.31.15.88`.
4. Created a pre-sync safety backup of the LOCAL mutable data in `.local-recovery/`.
5. Synchronized live business data (database, media/storage, and Avito records) from `144.31.15.88` to LOCAL without mutating or exposing any production secrets or overwriting local PKI.
6. Verified 100% data parity between `144.31.15.88` and LOCAL across all counts, SQLite schemas, and media files.
7. Validated that all 6 LOCAL Docker services are healthy and that all 8 core UI/API routes return HTTP 200 without error.
8. Updated active repository configuration, tooling defaults, and documentation to target `144.31.15.88` for all future operations.

---

## 2. Canonical Production VDS Verification (`144.31.15.88`)

Before sync, the new production VDS was inspected and verified healthy:

| Metric | Target Server Value (`144.31.15.88`) | Status |
| :--- | :--- | :--- |
| **SSH Connectivity** | Key authentication via `C:\Users\Apc\.ssh\id_ed25519` | PASS |
| **Operating System** | Debian GNU/Linux 13 (trixie) | MATCH |
| **Git HEAD** | `37768cb20dc7eca4a9539ce83ab9ba5b379c1232` | MATCH |
| **6 Docker Services** | All 6 services Up and healthy (`technoreboot-prod-*`) | PASS |
| **SQLite Quick Check** | `ok` | PASS |
| **DB Schema SHA256** | `3fdb6cbedf5cb46bb70ab7ed2e75bc4239e3467bbf7e5e21dfd989d21605973a` | PASS |
| **Products Count** | 225 | MATCH |
| **Sales Count** | 6 | MATCH |
| **Repairs Count** | 1 | MATCH |
| **Product Photos** | 221 | MATCH |
| **External Listings** | 221 | MATCH |
| **Avito Post-Sale Tasks** | 4 | MATCH |
| **Storage File Count** | 221 | MATCH |
| **Extension Version** | `0.2.62` | MATCH |
| **User Manual PDF SHA256** | `50ddeedeb4f93d2ea164ce57218a49cf6318ad2557a90c9266995dc8d0589b9e` | MATCH |

---

## 3. Fresh Production Snapshot & Local Pre-Sync Safety

1. **Production Snapshot on `144.31.15.88`:**
   - **Tool Used:** `admin-shell/app/backup_service.py` (`vds_backup.py`)
   - **Path:** `/tmp/TECHNOREBOOT_BACKUP_2026-09-16_215207.zip`
   - **SHA256:** `64ab2ad149398a26ac1c2eb4dc4ed99cb207502996d2b136f93ec6ce55414cd7`
   - **Manifest Integrity:** `True` (351 members, valid manifest metadata)
   - **Database Quick Check inside ZIP:** `ok`

2. **Local Safety Pre-Sync Backup:**
   - **Path:** `C:\tbootit\.local-recovery\pre_sync_20260916_220128.zip`
   - **SHA256:** `a6f341a886620aea5e52f4ec87e04b6cb3c9a008715b7db88e30d2aeb13fa4f1`
   - Preserves all pre-sync local data safely in `.gitignore`-tracked recovery space.

---

## 4. Production to LOCAL Data Sync Parity

The production snapshot was downloaded and extracted to LOCAL via `scripts/sync_vds_business_to_local.py`:

| Metric | Production VDS (`144.31.15.88`) | LOCAL Replica (`C:\tbootit`) | Parity Status |
| :--- | :--- | :--- | :--- |
| **Products** | 225 | 225 | **IDENTICAL** |
| **Sales** | 6 | 6 | **IDENTICAL** |
| **Repair Orders** | 1 | 1 | **IDENTICAL** |
| **Product Photos** | 221 | 221 | **IDENTICAL** |
| **External Listings** | 221 | 221 | **IDENTICAL** |
| **Avito Post-Sale Tasks**| 4 | 4 | **IDENTICAL** |
| **Storage Files** | 221 | 221 | **IDENTICAL** |
| **DB Schema SHA256** | `3fdb6cbedf5cb46bb70ab7ed2e75bc4239e3467bbf7e5e21dfd989d21605973a` | `3fdb6cbedf5cb46bb70ab7ed2e75bc4239e3467bbf7e5e21dfd989d21605973a` | **IDENTICAL** |
| **PRAGMA quick_check** | `ok` | `ok` | **PASS** |

### Local PKI & Infrastructure Preservation:
- Local server TLS certificates: **UNTOUCHED**
- Local Client Auth private keys: **UNTOUCHED**
- Local `.env` and dev credentials: **UNTOUCHED**
- Local networking and port bindings: **UNTOUCHED**

---

## 5. LOCAL Stack & Smoke Verification

All 6 LOCAL containers were started via `docker compose up -d` and verified:

```text
technoreboot-core                     Up (healthy)  0.0.0.0:8000->8000/tcp
technoreboot-inventory-sales-module   Up            0.0.0.0:8030->8030/tcp
technoreboot-repairs-module           Up            0.0.0.0:8040->8040/tcp
technoreboot-avito-module             Up            0.0.0.0:8020->8020/tcp, 127.0.0.1:8061->6080/tcp
technoreboot-admin-shell              Up            0.0.0.0:8011->8010/tcp
technoreboot-gateway                  Up            0.0.0.0:8443->8443/tcp
```

### End-to-End Route Smoke Test (`scripts/smoke_test_local_stage10d_r1.py`):
- `GET /` -> HTTP 200 (754,631 bytes)
- `GET /inventory/products` -> HTTP 200 (236,888 bytes)
- `GET /sales` -> HTTP 200 (16,841 bytes)
- `GET /repairs` -> HTTP 200 (12,990 bytes)
- `GET /avito/extension` -> HTTP 200 (19,529 bytes)
- `GET /avito/post-sale` -> HTTP 200 (20,227 bytes)
- `GET /help` -> HTTP 200 (11,092 bytes)
- `GET /help/user-manual.pdf` -> HTTP 200 (2,470,296 bytes)
- **Zero 500 / 502 Errors.**

### Automated Test Suite (`scripts/run_targeted_tests.py`):
- `core/tests`: 27 passed, 0 failed
- `admin-shell/tests`: 28 passed, 0 failed
- Root integration suite: 109 passed, 0 failed
- **Overall: 164 passed, 0 failed.**

---

## 6. Active Project References Update

| File | Changes Made |
| :--- | :--- |
| `scripts/sync_vds_business_to_local.py` | Default host changed to `root@144.31.15.88`; added `avito_post_sale_tasks` to parity verification. |
| `scripts/db_schema_contract.py` | Default VDS host updated to `root@144.31.15.88`. |
| `scripts/deploy_vds_precutover.py` | `VDS_HOST` set to `144.31.15.88`. |
| `scripts/verify_ip_https_mtls.py` | `BASE_URL` and `HTTP_URL` updated to `144.31.15.88`. Verified with public TLS and mTLS (PASS). |
| `chrome-extension/technoreboot-avito/manifest.json` | Added `"https://144.31.15.88/*"` to `host_permissions`. |
| `chrome-extension/technoreboot-avito/popup.js` | Added `144.31.15.88` to URL auto-detection. |
| `docs/production_status.md` | Promoted `144.31.15.88` to canonical production; marked `144.31.50.134` as `legacy-retained`. |
| `docs/production_deployment_model.md` | Recorded new canonical host `144.31.15.88` and new standard workflow. |

---

## 7. New Standard Workflow

```text
1. Production source of truth for business data:
   144.31.15.88

2. Development:
   LOCAL C:\tbootit

3. Business-data refresh:
   VDS 144.31.15.88 → LOCAL only (scripts/sync_vds_business_to_local.py)

4. New work:
   LOCAL implementation → automated tests → Owner browser acceptance

5. Deployment:
   separate production deployment stage → 144.31.15.88

6. Never:
   LOCAL business DB/media → VDS
```

---

## 8. Final Contract Block

```text
# Stage 10D-R1 — Promote New VDS + Sync Production to LOCAL

## Canonical Production
PRIMARY_PRODUCTION_VDS: 144.31.15.88
PRIMARY_PRODUCTION_HEALTHY: true
PRIMARY_PRODUCTION_GIT_HEAD: 37768cb20dc7eca4a9539ce83ab9ba5b379c1232
PRIMARY_PRODUCTION_DB_QUICK_CHECK: ok

## Legacy
LEGACY_VDS: 144.31.50.134
LEGACY_VDS_ROUTINE_SUPPORT: false
LEGACY_VDS_MODIFIED: false

## Fresh Production Snapshot
BACKUP_CREATED: /tmp/TECHNOREBOOT_BACKUP_2026-09-16_215207.zip
BACKUP_SHA256: 64ab2ad149398a26ac1c2eb4dc4ed99cb207502996d2b136f93ec6ce55414cd7
BACKUP_MANIFEST_OK: true

## LOCAL Safety
LOCAL_PRE_SYNC_BACKUP_CREATED: true
LOCAL_PRE_SYNC_BACKUP_PATH: C:\tbootit\.local-recovery\pre_sync_20260916_220128.zip
LOCAL_CODE_UNCOMMITTED_WORK_PRESERVED: true

## Production -> LOCAL Sync
PROD_PRODUCTS: 225
LOCAL_PRODUCTS: 225
PROD_SALES: 6
LOCAL_SALES: 6
PROD_REPAIRS: 1
LOCAL_REPAIRS: 1
PROD_PRODUCT_PHOTOS: 221
LOCAL_PRODUCT_PHOTOS: 221
PROD_EXTERNAL_LISTINGS: 221
LOCAL_EXTERNAL_LISTINGS: 221
PROD_AVITO_POST_SALE_TASKS: 4
LOCAL_AVITO_POST_SALE_TASKS: 4
PROD_STORAGE_FILE_COUNT: 221
LOCAL_STORAGE_FILE_COUNT: 221
SCHEMA_MATCH: true
LOCAL_DB_QUICK_CHECK: ok
DATA_SYNC_MATCH: true

## LOCAL Runtime
LOCAL_6_SERVICES_HEALTHY: true
LOCAL_ROOT_OK: true
LOCAL_PRODUCTS_OK: true
LOCAL_SALES_OK: true
LOCAL_REPAIRS_OK: true
LOCAL_AVITO_EXTENSION_OK: true
LOCAL_AVITO_POST_SALE_OK: true
LOCAL_HELP_OK: true
LOCAL_USER_MANUAL_OK: true

## Project Target Update
ACTIVE_DEPLOYMENT_TARGET: 144.31.15.88
OLD_IP_REMOVED_FROM_ACTIVE_TARGETS: true
HISTORICAL_RECORDS_PRESERVED: true

## Workflow
PRODUCTION_SOURCE_OF_TRUTH: 144.31.15.88
BUSINESS_SYNC_DIRECTION: VDS_TO_LOCAL_ONLY
FUTURE_DEPLOY_TARGET: 144.31.15.88

FINAL_STATUS:
TECHNOREBOOT_STAGE10D_R1_NEW_VDS_CANONICAL_LOCAL_SYNC_COMPLETE
```
