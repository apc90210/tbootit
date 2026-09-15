# Technoreboot Production Status

**Status Date:** 2026-09-15  
**Operating Architecture:** Local (Permanent DEV Sandbox) + VDS (Canonical Production)  
**Production Activation State:** **ACTIVE (IP-Only Canonical Test-Production)**  
**Canonical Production URL:** `https://144.31.50.134`  
**Domain Status:** Deferred / Not Required  

---

## 1. Network & Host Identity

| Parameter | Current Value | Required / Target Value | Status |
| :--- | :--- | :--- | :--- |
| **VDS Public IPv4** | `144.31.50.134` | `144.31.50.134` | MATCH |
| **VDS Hostname** | `atanov821.serv.host` | Deferred | DEFERRED |
| **Canonical URL** | `https://144.31.50.134` | `https://144.31.50.134` | **ACTIVE** |
| **Russia Domestic Reachability** | ICMP, PLPMTUD & TCP MSS clamped | Reachable w/o VPN | **ACTIVE (FIXED)** |
| **Public Server TLS** | Let's Encrypt IP SAN Certificate | Let's Encrypt IP SAN | **ACTIVE (TRUSTED)** |
| **TLS Issuer** | Let's Encrypt (`C=US, O=Let's Encrypt, CN=YE2`) | Let's Encrypt | MATCH |
| **TLS SAN** | `IP Address:144.31.50.134` | `144.31.50.134` | MATCH |
| **TLS Profile** | Short-lived profile | Short-lived | MATCH |
| **ACME Renewal Service** | Systemd `certbot.timer` + reload hook | Active & enabled | **ACTIVE** |
| **mTLS Client CA** | `a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d` | Persistent | PRESERVED |

---

## 2. Environments Status

### Local Workstation (`C:\tbootit`)
- **Role:** Permanent DEV / TEST Sandbox (`https://localhost:8443`).
- **Stack Status:** **RUNNING** (all 6 services Up and healthy).
- **Restart Count:** 0 across all containers.
- **Database Status:** Local replica.
- **Data Sync:** Synchronized via `scripts/sync_vds_business_to_local.py` (VDS -> LOCAL).
- **Safety Invariant:** Local data NEVER flows to VDS.

### Debian VDS (`144.31.50.134`)
- **Role:** Canonical Real-User Test-Production (`https://144.31.50.134`).
- **Stack Status:** **RUNNING** (all 6 services Up and healthy).
- **Current Git Commit:** `37768cb20dc7eca4a9539ce83ab9ba5b379c1232`.
- **Restart Count:** 0 across all containers.
- **Business Data Status:** **CANONICAL PRODUCTION (162 products, 3 sales, 1 repair order, 158 photos, 158 listings)**.
- **Production Data Guard:** Installed and active at `/srv/technoreboot/data/.technoreboot_production_data`.
- **Pre-Update Safety Backup:** Verified.
- **Code-Only Update Script:** Installed, tested, and active at `deploy/production/update_code_only.sh`.
- **RBAC & Security Status:** USER restricted from dev-reset, seed, backups, certificates, avito profiles; dev-reset blocked even for OWNER on production.
- **Avito Extension Version:** `0.2.62` (fixed SW init, immediate pairing input, syntax error resolved).
- **avito_post_sale_tasks Table:** **PRESENT** (Stage 09C migration applied).

---

## 3. Deployment & Update Model

```text
CURRENT_PRODUCTION_URL = https://144.31.50.134
DOMAIN_NAME = deferred / not required
LOCAL = DEV / TEST SANDBOX (REPLICA)
VDS = CANONICAL SOURCE OF TRUTH (REAL USER DATA)
CODE FLOW = LOCAL -> Git -> VDS (Code-Only Deployment)
DATA FLOW = VDS -> LOCAL (One-Way Parity Sync)
REVERSE SYNC = STRICTLY FORBIDDEN (LOCAL DATA NEVER FLOWS TO VDS)
```

- Deployment updates are triggered via `deploy/production/update_code_only.sh`.
- Ordinary deployments will never invoke `bootstrap_restore.py`, local data sync, or auth wipe.
- In-place SQLite backups occur automatically before every code change.
- Invariant verification checks ensure pre-update and post-update business record counts match identically.

---

## 4. Chrome Extension Pairing Status (Stage 08D-R1R3)

| Parameter | Current Status | Details |
| :--- | :--- | :--- |
| **Extension Version** | `0.2.62` | Fixed service worker init, immediate pairing input UI, one-click copy button |
| **Host Permissions** | `https://144.31.50.134/*`, `https://*/*` | Enables fetch communication with production VDS IP gateway |
| **Server Base URL** | Dynamic / Configurable | Extension popup permits manual entry / auto-detection of server base URL |
| **Pairing State Persistence** | Persistent Volume | Stored in `/srv/technoreboot/data/avito-module/extension_pair_codes.json` |
| **Production Target** | `https://144.31.50.134` | Extension communicates via `https://144.31.50.134/admin-api/avito-extension` |
| **Pairing Lifecycle Proof** | **PASSED (HTTP 200)** | Fresh code generation, validation, one-time-use redemption verified on VDS |

---

## 5. Owner Operations & DB Schema Guard Status (Stage 08D-R1R5)

| Parameter | Current Status | Details |
| :--- | :--- | :--- |
| **Owner Operations Page** | **ACTIVE (`/system/operations`)** | Web UI with real-time status, console logs, and confirmation modals |
| **RBAC Enforcement** | **ACTIVE (OWNER ONLY)** | USER role returns 403 Forbidden on page and all action endpoints |
| **Environment Guard** | **ACTIVE** | Local dev workstation enabled; VDS production hard-blocks all operations |
| **Schema Guard Contract** | **ACTIVE (`ae36c016...`)** | 24 tables, normalized types, 100% parity verified between code and VDS SQLite |
| **Manual Migration Flag** | `requires_manual_migration=false` | Stage 09C migration applied; `deployment_compatibility.json` cleared; code-only deploys safe |
| **Host Runner Daemon** | **RUNNING (`scripts/local_ops_runner.py`)** | Processes queued requests, enforces atomic locking, logs audit records |
| **Automated Tests** | **54 PASSED (0 FAILED)** | Full coverage for RBAC, Environment Guard, Schema Guard, Direction Guard |

---

## 6. Fast Rollback & Release Checkpoints Status (Stage 08D-R1R6)

| Parameter | Current Status | Details |
| :--- | :--- | :--- |
| **VDS Health Preflight** | **ACTIVE (`HEALTHY`)** | Probes SSH, HTTPS 443, Docker engine, 6/6 containers, SQLite quick_check, disk free space |
| **Pre-Update Release Checkpoint** | **ACTIVE** | Backs up VDS, copies to `.local-recovery/vds-releases/`, verifies SHA-256 match, tags images |
| **Checkpoint Retention Policy** | **ACTIVE (>= 3)** | Retains at least 3 recent checkpoints, preserves `last_known_good_vds_release.json` |
| **Fast Rollback (Code-Only)** | **ACTIVE** | Reverts code/containers to target checkpoint commit, preserves SQLite business DB & storage |
| **Rollback Schema Guard** | **ACTIVE** | Verifies live VDS schema contract matches target release before permitting rollback |
| **Automated Rollback** | **ACTIVE** | Reverts code and containers automatically if deployment or health check fails |
| **Operations UI Card 3 & Table** | **ACTIVE** | Rollback button, modal confirmation, and checkpoint history table on `/system/operations` |
| **Automated Tests** | **74 PASSED (0 FAILED)** | Full coverage for preflight, checkpoints, rollback RBAC, and rollback schema guard |

---

## 7. Avito Post-Sale Deactivation & Operator-Assisted Manual Flow (Stage 09A-R5 LOCAL)

| Parameter | Current Status | Details |
| :--- | :--- | :--- |
| **Stage Scope** | **LOCAL + VDS PRODUCTION** | Deployed to production VDS in Stage 09C |
| **Workflow Decision** | **MANUAL OPERATOR FLOW** | Automatic browser DOM clicking is disabled as unreliable; replaced by clear operator flow |
| **Post-Sale Prompt** | **ACTIVE** | Large card after sale: `[ ↗ Снять с Avito вручную ]` and `[ Не снимать ]` |
| **Manual Open Invariant** | **ENFORCED** | Opening listing sets task to `manual_required` (NEVER `success`). Original tab intact. |
| **"Не снимать" Invariant** | **ENFORCED** | Dismisses prompt, transitions task to `canceled`, preserves active listing, sale completed. |
| **Sale Detail Action Bar** | **ACTIVE** | Permanent button near `[ Товарный чек ]` with 3 honest states (no listing, already inactive, manual open) |
| **Manual Confirmation** | **ACTIVE** | `[ ✓ Я снял объявление ]` button sets task to `success`, listing to `archived`, writes audit log |
| **Post-Sale Queue UI** | **ACTIVE (`/avito/post-sale`)** | Operator-oriented table: Дата, Продажа, Товар, Avito ID, Статус, Действие |
| **Chrome Extension Version** | `0.2.62` | Fixed SW syntax error, immediate pairing code input UI, copy pair code button |
| **Stock & Sale Invariant** | **ENFORCED** | Completed sale and physical stock are NEVER mutated by Avito actions or cancellations |
| **Automated Tests** | **158 PASSED (0 FAILED)** | Core (27), Admin-shell (28), Root (103) all passing cleanly |
| **Live Proof** | **12/12 PASSED** | `scripts/verify_stage09a_r5_manual_flow.py` verified all flows end-to-end |
| **Schema Guard Status** | `requires_manual_migration = false` | Migration applied in Stage 09C. Code-only deploys are safe. |

---

## 8. VDS Isolated Shell Sync Test (Stage 09B — Zero Production DB Touch)

| Parameter | Current Status | Details |
| :--- | :--- | :--- |
| **Stage Scope** | **VDS ISOLATED TEST ONLY** | Release tested in isolated namespace (`technoreboot-sync-test-e022180`) on loopback port `127.0.0.1:18443` |
| **VDS Host Compatibility** | **VERIFIED (PASS)** | All 6 candidate images built and ran healthy on VDS host; UI, extension v0.2.62, copy button, and endpoints verified |
| **Live Production Runtime** | **100% UNTOUCHED** | All 6 live production containers retained original IDs and images (`Up 39h/40h/2d`), public `https://144.31.50.134` returned 200 |
| **Live Production DB** | **100% UNTOUCHED** | SHA256 before (`da6e2808...`) == SHA256 after (`da6e2808...`), schema hash unchanged, zero writes |
| **Live Media & Auth** | **100% UNTOUCHED** | Storage count (149) and auth files completely intact and unmodified |
| **Isolated Test Cleanup** | **COMPLETED** | Test containers, network, worktree, and disposable DB copy removed cleanly |
| **Final Status** | `TECHNOREBOOT_STAGE09B_VDS_ISOLATED_SYNC_TEST_PASSED_NO_PROD_DB_TOUCH` | Ready for separate production deployment stage upon Owner approval |

---

## 9. Production Schema Migration + Code Deploy (Stage 09C)

| Parameter | Current Status | Details |
| :--- | :--- | :--- |
| **Migration Applied** | **YES** | `avito_post_sale_tasks` table created on live VDS production DB |
| **Migration Method** | `CREATE TABLE IF NOT EXISTS` + indexes | Idempotent, additive, zero existing row mutation |
| **Schema Guard Post-Migration** | **PASS** | `db_schema_contract.py check-vds`: "VDS live database matches tracked contract: SAFE" |
| **Code Deployed** | **YES** | `update_code_only.sh origin/main` → `e21dba6404` (from `aa593781b7`) |
| **Extension Version** | `0.2.62` | ZIP SHA256 match confirmed: `c27a95bb...` |
| **All 6 Services Healthy** | **YES** | core, admin-shell, inventory-sales, repairs, avito, gateway — all healthy |
| **Business Data Preserved** | **YES** | 149 products, 0 sales, 149 photos, 149 listings — all counts identical pre/post |
| **Release Checkpoint Retained** | **YES** | `checkpoint_20260914_085202_aa593781` with business backup, image IDs, DB SHA256 |
| **deployment_compatibility.json** | `requires_manual_migration=false` | Future code-only deploys via admin shell UPDATE button are now safe |
| **Smoke Tests** | **ALL PASSED** | Root, products, sales, extension, post-sale, repairs, manual flow buttons verified |
| **Auto Code Rollback** | **NOT REQUIRED** | Deployment succeeded on first attempt |
| **Final Status** | `TECHNOREBOOT_STAGE09C_PRODUCTION_DEPLOYMENT_SUCCESS` | **READY FOR OWNER BROWSER ACCEPTANCE** |

---

## 10. Local User Manual PDF & Admin Panel Download Link (Stage 10A LOCAL)

| Parameter | Current Status | Details |
| :--- | :--- | :--- |
| **Stage Scope** | **LOCAL WORKSTATION ONLY** | User Manual PDF generation and permanent navigation download link integration |
| **User Manual Source** | `docs/user_manual/TECHNOREBOOT_USER_MANUAL_RU.md` | Complete Russian manual covering 17 chapters, plain language, zero technical jargon |
| **Generated PDF** | `admin-shell/app/static/docs/TECHNOREBOOT_USER_MANUAL_RU.pdf` | A4 format, 25 pages, 2,470,296 bytes, generated via Playwright Chromium |
| **Clickable TOC** | **VERIFIED (17 JUMP LINKS)** | Page 2 contains 17 internal PDF GoTo links pointing to chapter anchors |
| **PDF Outlines / Bookmarks** | **VERIFIED (19 ENTRIES)** | PyMuPDF injected outline hierarchy pointing to exact chapter pages |
| **Screenshots Included** | **15 REAL UI SCREENSHOTS** | High-res cropped captures of Products, Extension v0.2.62, Sales, Repairs, Reports, Owner ops |
| **Permanent Download Link** | **ACTIVE (`📘 Инструкция`)** | Integrated in unified navbar across inventory-sales, repairs, and all 12 admin-shell templates |
| **Download Route** | `GET /help/user-manual.pdf` | Serves `application/pdf` with attachment header; accessible to both USER and OWNER |
| **Help Overview Route** | `GET /help` | HTML overview with version details, chapter table of contents, and download button |
| **Security Audit** | **ZERO SECRETS (PASS)** | Automated scan confirms no SSH keys, passwords, tokens, dev paths (`/srv/...`, `C:\tbootit\...`) |
| **Final Status** | `TECHNOREBOOT_STAGE10A_LOCAL_USER_MANUAL_READY_FOR_OWNER_ACCEPTANCE` | **READY FOR OWNER BROWSER ACCEPTANCE** |

---

## 11. Production Deploy Latest Fix + User Manual (Stage 10B PRODUCTION)

| Parameter | Current Status | Details |
| :--- | :--- | :--- |
| **Stage Scope** | **CANONICAL PRODUCTION VDS (`144.31.50.134`)** | Code-only deployment of manual Avito flow, extension v0.2.62, and User Manual PDF |
| **Release Checkpoint** | `checkpoint_20260914_093238_e21dba64` | Retained with pre-update backup, previous image IDs, DB SHA-256 |
| **Safety DB Backup** | `TECHNOREBOOT_BACKUP_2026-09-14_093237.zip` | SHA-256 `625ee2dd...`, quick_check = ok |
| **Code Deployed** | **YES** | `update_code_only.sh origin/main` → `46fbed130c` (from `e21dba6404`) |
| **All 6 Services Healthy** | **YES** | admin-shell, repairs, inventory-sales, avito, core, gateway — all healthy |
| **User Manual PDF Deployed** | **YES** | Size 2,470,296 bytes, SHA-256 `50ddeedeb4f93d2ea164ce57218a49cf6318ad2557a90c9266995dc8d0589b9e` (exact match) |
| **Download Endpoints Active** | **YES** | `/help/user-manual.pdf` (200 OK, attachment), `/help` (200 OK) |
| **Top Navigation Links Active** | **YES (`📘 Инструкция`)** | Verified in live HTML responses from admin-shell, inventory-sales, repairs |
| **Manual Avito Flow Active** | **YES** | Verified in live container templates (`Снять с Avito вручную`, `Не снимать`, `Я снял объявление`) |
| **Business Data Preserved** | **YES** | 149 products, 0 sales, 149 photos, 149 listings, 149 storage files — identical pre/post |
| **Schema Invariant** | **MATCH** | Live schema SHA unchanged (`eb6a9c17...`), Schema Guard verified SAFE |
| **Final Status** | `TECHNOREBOOT_STAGE10B_PRODUCTION_DEPLOYMENT_SUCCESS` | **READY FOR OWNER BROWSER ACCEPTANCE** |




