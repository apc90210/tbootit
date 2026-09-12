# Technoreboot Production Deployment Model

**Canonical Architecture Contract — Stage 08D-R1R1**

```text
LOCAL = DEV / TEST SANDBOX
VDS = CANONICAL REAL-USER DATA
CODE SYNCS LOCAL/GIT -> VDS
BUSINESS DATA NEVER SYNCS LOCAL -> VDS
VDS DATA SURVIVES CODE DEPLOYMENTS
```

---

## 1. Operating Model Overview

By explicit decision of the Project Owner, the previous "final cutover means stopping local workstation" model is permanently cancelled.

### Local Workstation (Development & Test Sandbox)
- **Role:** Permanent development, testing, UI iteration, and regression testing sandbox.
- **Data State:** Contains dirty, test, and demo business data (sample products, sales, repairs).
- **Authority:** Local business data is **NOT** authoritative production data.
- **Isolation Rule:** Local business data must **NEVER** be pushed, copied, restored, or synchronized into the VDS after Stage 08D.
- **Runtime:** Runs simultaneously and independently alongside the VDS production stack.

### Debian VDS (Canonical Real-User Production)
- **Role:** Canonical test-production and real-user operating environment.
- **Hostname / IP:** `atanov821.serv.host` / `144.31.50.134`.
- **Data State:** Canonical business data begins clean (0 products, 0 sales, 0 repairs, 0 photos) and accumulates real user transactions.
- **Authority:** VDS business data is the **single source of truth**.
- **Persistence Rule:** VDS business data and media **MUST persist** across all future code deployments, container rebuilds, and configuration updates.

---

## 2. Code-Only Deployment Workflow

Future production updates follow a strictly non-destructive code-only pipeline:

```
[Local Dev Changes]
       │
       ▼
 [git push origin main]
       │
       ▼
 [VDS: deploy/production/update_code_only.sh]
       │
       ├─► 1. Verify VDS environment & data directory (/srv/technoreboot/data)
       ├─► 2. Verify Production Data Guard (.technoreboot_production_data)
       ├─► 3. Reject any restore / wipe / sync-from-local invocation
       ├─► 4. Record pre-update business invariants (DB SHA256 & row counts)
       ├─► 5. Create automatic safety backup (admin-shell/app/backup_service.py)
       ├─► 6. Fetch target git commit (git fetch && git checkout)
       ├─► 7. Validate docker-compose.prod.yml (zero host port leaks)
       ├─► 8. Build container images from source
       ├─► 9. Recreate containers (docker compose up -d --remove-orphans)
       ├─► 10. Poll container healthchecks (all 6 services must become healthy)
       ├─► 11. Rollback code automatically if containers fail healthchecks
       └─► 12. Verify business counts preserved (PRE_COUNTS == POST_COUNTS)
```

---

## 3. Production Data Guard Sentinel

The sentinel file `/srv/technoreboot/data/.technoreboot_production_data` acts as a hard boundary on the production server:

```ini
environment=production
data_owner=vds
do_not_overwrite_from_local=true
installed_at=2026-09-12T11:16:44Z
```

### Invariants Enforced by the Data Guard:
1. **No Bootstrap Restore:** `bootstrap_restore.py` must never be called during normal deployments.
2. **No Local Data Sync:** Neither local SQLite databases nor local `data/storage` trees may ever be rsynced, scp'd, or copied over VDS data.
3. **No Auth Overwrite:** The VDS Client CA (`a9b4d288...`), Owner certificate, and issued user certificates must never be overwritten by local auth trees.
4. **Separation of Concerns:** Disaster recovery restores are emergency, manual operations requiring explicit authorization, completely decoupled from standard code deployments.

---

## 4. Database Migration Policy for Future Upgrades

Future code updates will inevitably introduce schema modifications. The following migration policy governs all future changes:

1. **Business Data Preservation:** Business data must **never** be replaced or wiped to apply a migration.
2. **Mandatory Pre-Migration Backup:** Every schema migration must automatically trigger a full SQLite backup before applying DDL statements.
3. **Forward-Compatibility:** All migrations must be additive and forward-compatible:
   - `ALTER TABLE ... ADD COLUMN ...` with sensible defaults or nullable columns.
   - New tables for new features.
   - No `DROP TABLE` or `DROP COLUMN` on business tables without explicit Owner signoff.
4. **Transaction Safety:** All DDL/DML migrations must execute within transactions (`BEGIN TRANSACTION ... COMMIT`).
5. **Rollback Safety:** If a migration fails, the database must roll back to the pre-migration backup before container restart.
6. **No Auto-Drop:** Any script or tool that attempts to drop or recreate the production database is strictly forbidden in production configurations.

---

## 5. Network, Firewall, and Security Isolation

- **Exposed Public Ports:** Only SSH (port 22), HTTP (port 80 -> HTTPS redirect), and HTTPS (port 443).
- **Internal Service Ports:** Ports 8000 (Core), 8010 (Admin Shell), 8020 (Avito), 8030 (Inventory), 8040 (Repairs), and 6080 (noVNC) are bound exclusively to the private Docker bridge network (`technoreboot-network`) and never published to the host interfaces.
- **Firewall:** Linux `nftables` active, restricting traffic and preserving Docker forward chains.
- **Authentication:** mTLS enforced at Nginx gateway with client certificate verification against the persistent Technoreboot Client CA.

---

## 6. Extension Pairing Architecture & State Persistence Rules

In accordance with Stage 08D-R1R3 requirements:
1. **Canonical Persistent State:** Pairing code generation and redemption use canonical persistent state files stored at `${TECHNOREBOOT_DATA_ROOT}/avito-module/extension_pair_codes.json` and `extension_tokens.json`.
2. **Persistence Across Rebuilds & Deploys:** The directory `/srv/technoreboot/data/avito-module` is mounted as a persistent host volume into the `avito-module` container (`/app/data`). Pairing codes and issued tokens survive container recreations, rebuilds, and code-only deployments.
3. **Environment Independence:** Local development pairing state (`data/avito-module/...`) is completely isolated and independent from VDS production state (`/srv/technoreboot/data/avito-module/...`). Neither environment can overwrite or redeem codes from the other.
4. **Code Normalization & Security:** 6-digit pairing codes are formatted with leading zeros (`%06d`), validated as exact strings, have a 10-minute TTL, and are strictly one-time-use. Issued tokens are SHA-256 hashed and authenticated on every extension request.
5. **Dynamic Server Origin:** The Chrome Extension (v0.2.54+) supports dynamic server base URL configuration via popup UI and `chrome.storage.local`, allowing it to communicate directly with production VDS (`https://144.31.50.134/admin-api/avito-extension`) or local dev sandbox.

---

## 7. Business Data Direction & Local Parity Sync Architecture (Stage 08D-R1R4-SYNC)

Stage 08D-R1R4-SYNC codifies the permanent architectural relationship between Local Dev and VDS:

```text
CODE ARROW: LOCAL DEV -> Git -> VDS (Code-Only Deployment via update_code_only.sh)
DATA ARROW: VDS -> LOCAL DEV Replica (One-Way Sync via sync_vds_business_to_local.py)
FORBIDDEN:  LOCAL DEV -> VDS (NEVER reverse the data arrow during normal operations)
```

### Operating Procedure: Feature / Update Cycle
1. **Sync VDS Business Snapshot -> LOCAL:**
   Run `python scripts/sync_vds_business_to_local.py` to pull fresh canonical data into the local test replica.
2. **Develop & Test Code Locally:**
   Build new features, adjust templates, add endpoints, and execute unit/integration test suites against the replicated dataset.
3. **Commit & Push to Git:**
   Commit code, tests, docs, and tooling to git and push to `origin/main`.
4. **Automatic VDS Backup:**
   Production deploy script automatically creates a pre-update safety backup of VDS state.
5. **Code-Only Deploy to VDS:**
   Execute `deploy/production/update_code_only.sh origin/main` on VDS. Business data, certificates, and secrets are completely untouched.
6. **Verify VDS Invariants:**
   Confirm all 6 containers are healthy and business counts match pre-deploy values.
7. **Later Refresh Local Replica:**
   Refresh local business data on demand using `scripts/sync_vds_business_to_local.py`.

---

## 8. Owner Operations & Database Schema Guard (Stage 08D-R1R5)

Stage 08D-R1R5 introduces the Owner Operations Control Panel (`/system/operations`) with automated Database Schema Guard:

### 1. Operations Panel (`/system/operations`)
- **Role:** Strict OWNER-only access enforced at both UI and API levels (HTTP 403 for USER role).
- **Environment Isolation:** Sync and Update actions are permitted exclusively from the local development workstation (`LOCAL DEV`). On VDS production, actions are blocked by code and buttons are disabled.
- **Two Canonical Buttons:**
  - `[ Синхронизировать данные с VDS ]`: One-way snapshot sync from live VDS to local replica with pre-sync local safety backup in `.local-recovery/`.
  - `[ UPDATE VDS ]`: Automated code-only deploy (`origin/main` -> VDS) executed after preflight Git clean check, DB schema compatibility check, and remote safety backup.

### 2. Database Schema Guard
- **Canonical Contract:** Tracked at `deploy/production/schema_contract.json` (SHA256: `ce11b10dc33ecd3ab6804bf65e12fc55a840ce3f308b5cd2da4a6869b8e904d7`).
- **Compatibility Flag:** Tracked at `deploy/production/deployment_compatibility.json`. If `requires_manual_migration == true` or structural changes exist between SQLAlchemy code models and canonical VDS schema, code deployment is hard-blocked.
- **Host Runner Daemon:** `scripts/local_ops_runner.py` runs in the background on the host, processing atomic requests from `data/dev-ops/requests/`, enforcing single-job concurrency locking (`lock.json`), and recording audit history in `data/dev-ops/audit_log.json`.

