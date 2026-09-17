# Technoreboot Production Status

**Status Date:** 2026-09-17  
**Operating Architecture:** Local (Permanent DEV Sandbox) + VDS (Canonical Production)  
**Production Activation State:** **ACTIVE (Canonical Production: 144.31.15.88)**  
**Canonical Production URL:** `https://144.31.15.88`  
**Domain Status:** Deferred / Not Required  
**PRIMARY_PRODUCTION_VDS:** `144.31.15.88`  
**LEGACY_VDS:** `144.31.50.134` (OLD_VDS_STATUS=legacy-retained, OLD_VDS_ROUTINE_SUPPORT=false)  

---

## 1. Network & Host Identity

| Parameter | Current Value | Required / Target Value | Status |
| :--- | :--- | :--- | :--- |
| **VDS Public IPv4** | `144.31.15.88` | `144.31.15.88` | **MATCH (PRIMARY)** |
| **VDS Hostname** | `atanov822.serv.host` | `atanov822.serv.host` | MATCH |
| **Canonical URL** | `https://144.31.15.88` | `https://144.31.15.88` | **ACTIVE** |
| **Legacy VDS IPv4** | `144.31.50.134` | `legacy-retained` | **RETIRED (NO ROUTINE SUPPORT)** |
| **Public Server TLS** | Let's Encrypt IP SAN Certificate | Let's Encrypt IP SAN | **ACTIVE (TRUSTED)** |
| **TLS Issuer** | Let's Encrypt (`C=US, O=Let's Encrypt, CN=YE2`) | Let's Encrypt | MATCH |
| **TLS SAN** | `IP Address:144.31.15.88` | `144.31.15.88` | MATCH |
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
- **Data Sync:** Synchronized from `144.31.15.88` via `scripts/sync_vds_business_to_local.py` (VDS -> LOCAL).
- **Safety Invariant:** Local data NEVER flows to VDS.

### Debian VDS (`144.31.15.88`) — PRIMARY PRODUCTION
- **Role:** Canonical Primary Production (`https://144.31.15.88`).
- **Provider Hostname:** `atanov822.serv.host`.
- **Stack Status:** **RUNNING** (all 6 services Up and healthy).
- **Current Git Commit:** Stage 11D-R2 (`024c453592680addaa5f064380cbecc886700a6b`).
- **Restart Count:** 0 across all containers.
- **Business Data Status:** **CANONICAL PRODUCTION (241 products, 4 sales, 1 repair order, 237 photos, 237 listings, 4 avito post-sale tasks)**.
- **Stage 11A/11B/11D-R1/11D-R2 Features Deployed & Audited:**
  - Sales corrections with immutable revision history.
  - Canonical repair issue payment finalization, warranty receipt (`/sales/{id}` canonical link).
  - Ready status accessible from all active repair stages with price field.
  - OWNER-only permanent bulk delete for Sales & Repairs with full relational invariants.
  - Anti-spoofing gateway & reverse-proxy header sanitization for `X-Auth-Is-Owner`.
  - Forensic integrity audit (Stage 11D-R2): repair #1 and status history restored from pre-incident backup after test mutation; compensating audit event #1746 recorded; data integrity 100% verified.
- **Production Data Guard:** Installed and active at `/srv/technoreboot/data/.technoreboot_production_data`.
- **Incident Forensic Status:**
  - `REAL_BUSINESS_RECORDS_MUTATED_DURING_STAGE11D_R1`: true
  - `INCIDENT_RESTORED_AND_VERIFIED`: true
  - `PRE_INCIDENT_BACKUP`: `TECHNOREBOOT_BACKUP_2026-09-17_110805.zip` (`061b139bed42b56c228500a58cdc3352aa41a6b0dcc46551e778e9640de9e713`)
  - `POST_INCIDENT_BACKUP`: `TECHNOREBOOT_BACKUP_2026-09-17_113124.zip` (`832c9a108d8666a8a926c5e004c5efa586f22c40c1406a50bc9a6dddc7844768`)
  - `COMPENSATING_AUDIT_LOG_ID`: 1746 (`production_test_restore`)
- **Running Image IDs:**
  - `core`: `sha256:237ff077b400f85bb8e9ed20f9e4b0c71a828d49c2111d96f0503379e710a5da`
  - `admin-shell`: `sha256:0bcc827b6307d599bf296291974632cc68736e5c6394bdbad723d4e1d863ac2d`
  - `inventory-sales`: `sha256:e7a8fdcea8e39f2cb26df3b47ad742630c29630a7f35b98fb97cdc25fceacbaa`
  - `repairs`: `sha256:f91c41abe2820a5b70f166340d31e65a8a7889be731a37416233a41c394e3c3a`
- **Schema Guard:** Contract `3b8d35d76ae6343f105925aa7c725c7ebc4b8613ed5f015bec61a27f491484dc` (SAFE).
- **RBAC & Security Status:** USER restricted from dev-reset, seed, backups, certificates, avito profiles, and bulk-delete; dev-reset blocked even for OWNER on production; spoofed `X-Auth-Is-Owner: 1` returns 403.
- **Avito Extension Version:** `0.2.62`.
- **avito_post_sale_tasks Table:** **PRESENT**.

### Legacy Debian VDS (`144.31.50.134`) — RETIRED
- **Role:** Legacy-retained (`OLD_VDS_STATUS=legacy-retained`).
- **Routine Support:** None (`OLD_VDS_ROUTINE_SUPPORT=false`).
- **Policy:** Preserved untouched for history/rollback; not deployed to, not verified routinely.

---

## 3. Deployment & Update Model

```text
PRIMARY_PRODUCTION_VDS = 144.31.15.88
CURRENT_PRODUCTION_URL = https://144.31.15.88
LEGACY_VDS = 144.31.50.134
OLD_VDS_STATUS = legacy-retained
OLD_VDS_ROUTINE_SUPPORT = false

WORKFLOW:
1. Production source of truth for business data: 144.31.15.88
2. Development: LOCAL C:\tbootit
3. Business-data refresh: VDS 144.31.15.88 -> LOCAL only
4. New work: LOCAL implementation -> automated tests -> Owner browser acceptance
5. Deployment: separate production deployment stage -> 144.31.15.88
6. Never: LOCAL business DB/media -> VDS
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

---

## 12. Parallel Clone to New Debian 13 VDS (Stage 10D PRODUCTION)

| Parameter | Current Status | Details |
| :--- | :--- | :--- |
| **Stage Scope** | **PARALLEL FULL CLONE TO NEW VDS (`144.31.15.88`)** | Testing non-VPN connectivity on alternative IP prefix without touching source |
| **Source Server** | `144.31.50.134` (Authoritative Production) | Remained 100% online, unmutated, 6 services healthy, authoritative status retained |
| **Target Server** | `144.31.15.88` (Parallel Test Clone) | Debian 13 trixie, Xeon E5-2667 v2, 1.9 GB RAM, 18 GB disk free, MTU 1500 |
| **Public Server TLS** | **Let's Encrypt IP SAN (`144.31.15.88`)** | Successfully issued via Certbot 5.8.0 standalone shortlived profile; auto-renewal enabled |
| **Client mTLS Verification** | **ACTIVE & ENFORCED** | Uses identical TechnoReboot Client CA (`a9b4d288...`); requests without cert return 403 |
| **HTTP 80 Redirect** | **ACTIVE (301 -> HTTPS)** | Verified redirection to `https://144.31.15.88/` |
| **Business Data Invariants** | **100% PARITY MATCH** | 220 products, 6 sales, 1 repair, 216 photos, 216 listings, 4 tasks, 216 storage files |
| **DB Schema Parity** | **MATCH (`3fdb6cbed...`)** | SQLite `PRAGMA quick_check: ok`, identical schema SHA |
| **All 6 Services Healthy** | **YES** | core, inventory-sales, repairs, avito, admin-shell, gateway — all Up & healthy |
| **Internal Ports Secured** | **YES** | Zero internal ports exposed on host; only 80 and 443 open on gateway |
| **Avito Safety** | **ENFORCED** | Auto-deactivation disabled (manual only); no duplicate external worker |
| **Packet Capture Armed** | **YES (`target-capture.service`)** | Logging all port 80/443 traffic to `/tmp/stage10d_target_test.pcap` for non-VPN testing |
| **Final Status** | `TECHNOREBOOT_STAGE10D_NEW_VDS_CLONE_READY_ARMED_FOR_OWNER_TEST` | **READY FOR OWNER NON-VPN BROWSER TEST** |

---

## 13. Promote New VDS as Canonical Production & Sync to LOCAL (Stage 10D-R1)

| Parameter | Current Status | Details |
| :--- | :--- | :--- |
| **Canonical Production VDS** | `144.31.15.88` | Promoted to sole primary production source of truth |
| **Legacy Server (`144.31.50.134`)** | `legacy-retained` | Retired from active service; routine support disabled |
| **Fresh VDS Backup** | `TECHNOREBOOT_BACKUP_2026-09-16_215207.zip` | SHA-256 `64ab2ad1...`, quick_check = ok, 351 archive members |
| **Local Safety Backup** | `pre_sync_20260916_220128.zip` | SHA-256 `a6f341a8...`, stored in `.local-recovery/` |
| **VDS -> LOCAL Data Sync** | **100% PARITY MATCH** | Products (225), Sales (6), Repairs (1), Photos (221), Listings (221), Tasks (4), Storage (221) |
| **DB Schema Parity** | **MATCH (`3fdb6cbed...`)** | SQLite `PRAGMA quick_check: ok`, schema contract verified SAFE |
| **Local PKI / Secrets** | **UNTOUCHED (100% SECURE)** | Local TLS certs, client auth keys, dev .env, and secrets completely preserved |
| **Local Stack Health** | **ALL 6 SERVICES HEALTHY** | core, admin-shell, inventory-sales, repairs, avito, gateway — all Up & functional |
| **Local Smoke Verification** | **8/8 PASSED (HTTP 200)** | `/`, `/inventory/products`, `/sales`, `/repairs`, `/avito/extension`, `/avito/post-sale`, `/help`, `/help/user-manual.pdf` |
| **Automated Test Suite** | **164 PASSED (0 FAILED)** | Core (27), Admin-shell (28), Root integration suite (109) — 100% pass |
| **Active Target Updated** | `144.31.15.88` | Active tooling (`sync_vds_business_to_local.py`, `verify_ip_https_mtls.py`, `db_schema_contract.py`, extension manifest) updated to `144.31.15.88` |
| **Historical Records** | **PRESERVED UNCHANGED** | All historical stage logs, audit reports, and forensic data retain original IPs |
| **Final Status** | `TECHNOREBOOT_STAGE10D_R1_NEW_VDS_CANONICAL_LOCAL_SYNC_COMPLETE` | **CANONICAL PRODUCTION PROMOTED & LOCAL SYNC VERIFIED** |

---

## 14. Extension Connection Switching (Stage 12A LOCAL DEV)

| Parameter | Current Status | Details |
| :--- | :--- | :--- |
| **Stage Scope** | **LOCAL DEV ONLY** | Extension connection switching between LOCAL (`https://localhost:8443`) and Production (`https://144.31.15.88`) |
| **Extension Version** | **v0.2.63** | Bumped from v0.2.62. ZIP rebuilt at `dist/technoreboot-avito-extension-0.2.63.zip` (SHA256: `bbaf780f75647c598c0725ad2de30239f865ea311ca529d405978960d1a16f9b`) |
| **Connection Card UI** | **ACTIVE** | Shows current connected origin, paired/offline status badge, explicit `[Отключиться]` button with confirmation |
| **Reconnection / Pairing UI** | **ACTIVE** | Dynamic server origin input (prefilled with active tab when unpaired) + 6-digit code + runtime permission request |
| **Atomic State Transition** | **ENFORCED** | Service worker atomically stores `server_base_url`, `extension_token`, `active_connection`. Stale tokens cleared |
| **Host Permissions Strategy** | **CLEANED MV3** | Retired `144.31.50.134` removed; `localhost:8443` and `144.31.15.88` retained; optional host permissions with runtime `chrome.permissions.request()` |
| **Server-Side Revocation** | **ACTIVE** | Added `POST /extension/api/pairing/revoke` and `/pairing/unpair` to `avito-module` |
| **Automated Tests** | **302 PASSED (0 FAILED)** | Targeted suite (164 tests) + Extension suite (138 tests, including 12 Stage 12A switching tests) |
| **Production Target** | **UNTOUCHED (0 changes)** | VDS `144.31.15.88` untouched; DB unchanged; ready for Owner LOCAL acceptance |
| **Final Status** | `TECHNOREBOOT_STAGE12A_LOCAL_READY_FOR_OWNER_ACCEPTANCE` | **READY FOR OWNER BROWSER ACCEPTANCE ON LOCAL** |

