# Technoreboot Production Status

**Status Date:** 2026-09-12  
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
- **Database Status:** 149 products, 0 sales, 0 repairs, 149 photos, 149 listings (100% parity with VDS).
- **Data Sync:** Synchronized via `scripts/sync_vds_business_to_local.py` (VDS -> LOCAL).
- **Safety Invariant:** Local data NEVER flows to VDS.

### Debian VDS (`144.31.50.134`)
- **Role:** Canonical Real-User Test-Production (`https://144.31.50.134`).
- **Stack Status:** **RUNNING** (all 6 services Up and healthy).
- **Current Git Commit:** `1c7792db7267bb3fd5e7b75b04a90edb73d37960`.
- **Restart Count:** 0 across all containers.
- **Business Data Status:** **CANONICAL PRODUCTION (149 products, 0 sales, 0 repairs, 149 photos, 149 listings)**.
- **Production Data Guard:** Installed and active at `/srv/technoreboot/data/.technoreboot_production_data`.
- **Pre-Update Safety Backup:** `TECHNOREBOOT_BACKUP_2026-09-12_103639.zip` / `TECHNOREBOOT_BACKUP_2026-09-12_103935.zip`.
- **Code-Only Update Script:** Installed, tested, and active at `deploy/production/update_code_only.sh`.
- **RBAC & Security Status:** USER restricted from dev-reset, seed, backups, certificates, avito profiles; dev-reset blocked even for OWNER on production.
- **Avito Extension Version:** `0.2.56` (tightened host permissions, broad wildcard removed).

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
| **Extension Version** | `0.2.54` | Aligned across manifest, popup, service worker, content script, and backend schemas |
| **Host Permissions** | `https://144.31.50.134/*`, `https://*/*` | Enables fetch communication with production VDS IP gateway |
| **Server Base URL** | Dynamic / Configurable | Extension popup permits manual entry / auto-detection of server base URL |
| **Pairing State Persistence** | Persistent Volume | Stored in `/srv/technoreboot/data/avito-module/extension_pair_codes.json` |
| **Production Target** | `https://144.31.50.134` | Extension communicates via `https://144.31.50.134/admin-api/avito-extension` |
| **Pairing Lifecycle Proof** | **PASSED (HTTP 200)** | Fresh code generation, validation, one-time-use redemption verified on VDS |

