# Stage 08D-R1R2: IP-Only Clean Test-Production Activation Report

**Date:** 2026-09-12  
**Host IP:** `144.31.50.134`  
**Canonical Production URL:** `https://144.31.50.134`  
**Local DEV URL:** `https://localhost:8443`  
**Stage:** `Stage 08D-R1R2 — IP-Only Clean Test-Production Activation`  
**Status:** **SUCCESS / ACTIVE**  

---

## 1. Executive Summary

By Owner direction under Stage 08D-R1R2, hostname/DNS activation (`atanov821.serv.host`) is permanently deferred for now, and the canonical production environment is activated directly on the VDS public IP address:
```text
CURRENT_PRODUCTION_URL = https://144.31.50.134
DOMAIN_NAME = deferred / not required
LOCAL = DEV / TEST
VDS = canonical real-user data
FUTURE_DEPLOYS = code only
LOCAL BUSINESS DATA MUST NEVER BE RESTORED TO VDS
```

### Key Milestones Achieved:
1. **IP-Only Public TLS via Let's Encrypt:** Installed Certbot 5.8.0 in an isolated environment (`/opt/certbot-venv`). Successfully requested and installed a publicly trusted Let's Encrypt IP SAN certificate (`IP Address:144.31.50.134`) using the short-lived profile. Automated background renewal via systemd timer `certbot.timer` and automatic Nginx reload hook configured and proven with dry-run (`certbot renew --dry-run`).
2. **Clean VDS Business Data Reset:** Transactionally cleared all business domain rows from `/srv/technoreboot/data/db/technoreboot.db`:
   - `products`: **0**
   - `sales`: **0**
   - `repair_orders`: **0**
   - `product_photos`: **0**
   - `product_external_listings`: **0**
   - `stock_movements`: **0**
   - `product_events`: **0**
   - `customers`: **0**
   - `sale_items`: **0**
   - `repair_status_history`: **0**
   - `product_avito_attribute_values`: **0**
   - `audit_log`: **2** (only system seed events preserved)
3. **Live Media Storage Reset:** Cleared all active photos and legacy archive directories under `/srv/technoreboot/data/storage/`. Total business media files = **0** (`LIVE_STORAGE_BUSINESS_FILES = 0`).
4. **Avito Business State Reset:** Removed all old imported runs, ads, and listing caches under `/srv/technoreboot/data/avito-module/`, preserving pairing credentials and browser profiles.
5. **Infrastructure & Client CA Preserved:** Client CA (`a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d`), Owner certificate, user certificates, revocation registry, backups, secrets, and firewall were 100% preserved.
6. **Simultaneous Dual Runtime & mTLS Proof:** Both the Local DEV stack (`https://localhost:8443`) and the VDS production stack (`https://144.31.50.134`) are running simultaneously and accepting the same client certificates. Verified all 10 canonical Owner routes return HTTP 200, unauthenticated requests return 403, revoked certificates return 403, and user RBAC enforces restricted access.
7. **Real Code-Only Self-Test:** Executed `deploy/production/update_code_only.sh origin/main` on the live VDS. Containers were rebuilt and recreated while proving zero-mutation of clean data (`PRE_COUNTS == POST_COUNTS == 0`).
8. **Clean Baseline Production Backup:** Generated post-activation baseline backup `TECHNOREBOOT_CLEAN_IP_TEST_PRODUCTION_BASELINE_2026-09-12.zip` (SHA256: `e6892f9921de3b62f7de25c8780f554c39002cb681b7d7edf8aa6fd36062a6b0`).

---

## 2. Section 23 Final Report Contract

```text
# Stage 08D-R1R2 — IP-Only Clean Test-Production Activation

## Environment
LOCAL_ROLE: DEV_TEST
VDS_ROLE: CANONICAL_REAL_USER
LOCAL_STACK_RUNNING: true
VDS_STACK_RUNNING: true
CANONICAL_URL: https://144.31.50.134
DNS_REQUIRED: false

## IP TLS
CERTBOT_VERSION: 5.8.0
IP_CERT_ISSUED: true
TLS_IDENTIFIER: 144.31.50.134
TLS_ISSUER: C=US, O=Let's Encrypt, CN=YE2
TLS_PUBLIC_TRUST: true
TLS_IP_SAN_MATCH: true (IP Address:144.31.50.134)
TLS_SHORTLIVED_PROFILE: true (6 days validity)
TLS_RENEWAL_AUTOMATED: true (systemd certbot.timer + reload deploy hook)
TLS_RENEW_DRY_RUN: PASS

## Safety
PRE_RESET_BACKUP_FILE: TECHNOREBOOT_PRE_RESET_BACKUP_2026-09-12_081617.zip
PRE_RESET_BACKUP_SHA256: 4362991cc8216b66d36451b1ea36be9ede3ff77173a9bb4a871be280c122b9cc
PRODUCTION_DATA_GUARD: /srv/technoreboot/data/.technoreboot_production_data (installed)

## Preserved Infrastructure
CLIENT_CA_PRESERVED: true (SHA256: a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d)
OWNER_CERT_PRESERVED: true
USER_CERTS_PRESERVED: true
REVOCATION_REGISTRY_PRESERVED: true
BACKUP_HISTORY_PRESERVED: true
PRODUCTION_SECRETS_PRESERVED: true

## Clean VDS
PRODUCTS: 0
SALES: 0
REPAIRS: 0
PRODUCT_PHOTOS: 0
EXTERNAL_LISTINGS: 0
INVENTORY_MOVEMENTS: 0
OTHER_BUSINESS_ROWS: 0
LIVE_STORAGE_BUSINESS_FILES: 0
AVITO_BUSINESS_STATE_CLEARED: true
SQLITE_SEQUENCES_RESET: true

## Runtime
ALL_SERVICES_HEALTHY: true (core, inventory-sales, repairs, avito, admin-shell, gateway)
ROOT: 200
PRODUCTS_ROUTE: 200 (0 product links)
JSON_ROUTE: 200
SALES_ROUTE: 200
CART_ROUTE: 200 (empty cart)
REPORTS_ROUTE: 200 (totals = 0)
REPAIRS_ROUTE: 200 (0 repairs)
AVITO_ROUTE: 200 (0 business listings)
BACKUPS_ROUTE: 200
CERTIFICATES_ROUTE: 200
REPORT_TOTALS_ZERO: true
NO_STALE_BUSINESS_DATA_VISIBLE: true

## mTLS
NO_CERT_REJECTED: true (HTTP 403)
OWNER_ACCEPTED: true (HTTP 200 on all canonical routes)
USER_RBAC: true (HTTP 200 on operational, HTTP 403 on /backups & /certificates)
REVOKED_CERT_REJECTED: true (0bcc72bc7c81 -> HTTP 403)
CLIENT_CA_SHA256_UNCHANGED: true
SAME_OWNER_CERT_WORKS_LOCAL_AND_VDS: true

## Code-Only Deployment
UPDATE_SCRIPT: deploy/production/update_code_only.sh
PRE_UPDATE_BACKUP_REQUIRED: true
LOCAL_DB_COPY_FORBIDDEN: true
LOCAL_MEDIA_COPY_FORBIDDEN: true
LOCAL_AUTH_COPY_FORBIDDEN: true
BOOTSTRAP_RESTORE_FORBIDDEN: true
CODE_ONLY_SELF_TEST: PASSED (origin/main rebuild & recreation verified)
POST_DEPLOY_DATA_PRESERVED: true (PRE_COUNTS == POST_COUNTS == 0)

## Clean Baseline Backup
BASELINE_BACKUP_FILE: TECHNOREBOOT_CLEAN_IP_TEST_PRODUCTION_BASELINE_2026-09-12.zip
BASELINE_BACKUP_SHA256: e6892f9921de3b62f7de25c8780f554c39002cb681b7d7edf8aa6fd36062a6b0
BASELINE_BUSINESS_DATA_EMPTY: true (0 products, 0 sales, 0 repairs, 0 photos, 0 storage files)
BASELINE_AUTH_CA_MATCH: true (Client CA exact)

## Local Safety
LOCAL_PRODUCTS_UNCHANGED: true (50)
LOCAL_SALES_UNCHANGED: true (52)
LOCAL_REPAIRS_UNCHANGED: true (66)
LOCAL_PHOTOS_UNCHANGED: true (50)
LOCAL_EXTERNAL_LISTINGS_UNCHANGED: true (50)
LOCAL_DB_SHA256_UNCHANGED: true (a84b08e77ac37d522ba90b952bc88b2d5dd6d90efd5de6987bdd662798cd0435)
LOCAL_CA_SHA256_UNCHANGED: true (a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d)

## Network
PUBLIC_PORTS: 22,80,443
INTERNAL_PUBLIC_PORTS: 0
FIREWALL_ACTIVE: true

## Tests
FAILED: 0

## Git
COMMIT: PENDING_COMMIT
PUSH: PENDING_PUSH
HEAD_AFTER: PENDING
FINAL_GIT_STATUS: PENDING

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
