# Stage 07B-R1 — Simple Full Backup / Restore

**Project:** ТехноРебут  
**Workspace:** `C:\tbootit`  
**Stage:** `Stage 07B-R1 — Simple Full Backup / Restore`  
**Status:** Completed & Verified  

---

## 1. Executive Summary

Stage 07B-R1 delivers a simple, practical, fully autonomous full-system backup and restore mechanism for Technoreboot. The solution creates a single timestamped ZIP archive containing all critical persistent application state:
- SQLite database (using Python online backup API + logical SQL dump)
- Product photos and media storage (`data/storage/`)
- Authentication state & mTLS PKI (`data/auth/`: CA, OWNER, client certificates, `registry.json`, `owner_password.txt`, server certs)
- Avito module persistent state (`data/avito-module/`)
- Runtime configuration (`.env` if present)
- Metadata manifest (`manifest.json` with commit hash, table counts, sha256 fingerprints, file metrics)

The backup archive can be copied to any external hard drive, USB stick, or secondary computer. A single restore command (`backup\restore_full.cmd`) restores the full working system from scratch, validates data integrity, starts Docker services, and verifies that the existing OWNER certificate continues to authorize without reconfiguration.

---

## 2. Discovered Persistent State Inventory

Inspection of `docker-compose.yml` and runtime filesystem revealed that NO named Docker volumes are used; all persistent data is mounted from host paths:

| Component | Host Path | Container Mount | Description |
|-----------|-----------|-----------------|-------------|
| **Database** | `data/db/technoreboot.db` | `core:/data/db/technoreboot.db` | SQLite database (23 tables, 117 products, 384 photo records, 66 repairs, 50 sales, 27 customers, 39 categories, 610 audit entries) |
| **Media Storage** | `data/storage/product_photos/` | `core:/data/storage/product_photos` | 724 media files (product images, repair photos, receipts) |
| **Auth & PKI** | `data/auth/` | `admin-shell:/app/auth-data`, `gateway:/etc/nginx/certs:ro` | Root CA (`ca.crt`, `ca.key`), server keys, client certs (`owner.crt`, `owner.key`, `owner.p12`, USER bundles), `registry.json`, `owner_password.txt` |
| **Avito Module** | `data/avito-module/` | `avito-module:/app/data` | Ads, listings, profiles, extension pairing codes, tokens |
| **Configuration** | `.env` | Host root | Runtime environment variables |

**Excluded Disposable Items:**
- Docker image layers, temporary containers, bridge networks (reproducible from repository)
- Python caches (`__pycache__`, `.pytest_cache`, `.venv`, `venv`)
- Runtime log files (`pytest.log`, temp logs)
- Build artifacts (`dist/`, `scratch/`, extension zips)
- Backup destination directory (`backups/` — git-ignored)

---

## 3. Architecture & Tooling

All tooling is located under `backup/`:
```text
backup/
  backup_full.py       - Core backup logic (SQLite backup API, iterdump, recursive copy, manifest, zip)
  backup_full.cmd      - Windows CMD wrapper
  restore_full.py      - Core restore logic (pre-validation, confirmation, service management, healthcheck)
  restore_full.cmd     - Windows CMD wrapper
  README.md            - User instructions for owner
```

### 3.1 Backup Workflow (`backup\backup_full.cmd`)
1. Resolves project root (`C:\tbootit`).
2. Generates timestamp: `YYYY-MM-DD_HHMMSS`.
3. Creates temporary staging directory in `backups/.tmp_staging_<timestamp>`.
4. Connects to `data/db/technoreboot.db` in read-only mode and performs an online consistent snapshot via `sqlite3.Connection.backup()`. Concurrently streams logical SQL text dump via `iterdump()`.
5. Recursively copies `data/storage/`, `data/auth/`, `data/avito-module/`, and `.env`.
6. Inspects certificates: extracts CA SHA-256 fingerprint, OWNER SHA-256 fingerprint, OWNER serial, registry total and revoked cert counts.
7. Assembles `manifest.json` (format version "1.0", UTC timestamp, git commit, table counts, fingerprints).
8. Compresses staging folder into `backups/TECHNOREBOOT_BACKUP_YYYY-MM-DD_HHMMSS.zip` (Deflate compression level 6).
9. Verifies archive with `testzip()` and cleans up staging directory.
10. Prints summary report with archive size and path.

### 3.2 Restore Workflow (`backup\restore_full.cmd`)
1. **Pre-Validation (Fail-Fast):**
   - Validates archive existence and checks zip integrity via `testzip()`.
   - Parses `manifest.json`, validates format version 1.0.
   - Verifies required files: database (`technoreboot.db` or `technoreboot_dump.sql`), `auth/ca/ca.crt`, `auth/certificates/owner.crt`, `auth/registry.json`.
   - If validation fails: exits with code 1 immediately. No containers are stopped and no disk data is modified.
2. **Confirmation:**
   - Warns user that live data will be overwritten and prompts for `yes` confirmation (or `--yes` flag).
3. **Service Management:**
   - Safely stops containers (`core`, `admin-shell`, `gateway`, `avito-module`, `inventory-sales-module`, `repairs-module`).
4. **Data Restoration:**
   - Restores SQLite database, media files, auth keys/certs, avito data, and `.env`.
5. **Stack Restart & Healthcheck:**
   - Launches containers (`docker compose up -d`).
   - Polls `http://localhost:8000/health` until 200 OK.
   - Polls `http://localhost:8011/` until 200 OK.
6. **Post-Restore Integrity Verification:**
   - Verifies database table queries.
   - Verifies CA fingerprint matches manifest.
   - Verifies OWNER fingerprint and serial match manifest.
   - Verifies revoked certificate count and states.

---

## 4. Disaster Recovery Instructions

In the event of total server loss:

1. On a fresh Windows machine with Docker Desktop, Git, and Python 3 installed:
   ```cmd
   git clone https://github.com/apc90210/tbootit.git C:\tbootit
   cd /d C:\tbootit
   ```
2. Copy your backup archive (e.g. `TECHNOREBOOT_BACKUP_2026-09-08_142812.zip`) into `C:\tbootit\backups\`.
3. Run restore:
   ```cmd
   backup\restore_full.cmd "C:\tbootit\backups\TECHNOREBOOT_BACKUP_2026-09-08_142812.zip"
   ```
4. Access the system securely via mTLS:
   ```text
   https://localhost:8443/admin-shell/
   ```
   The existing OWNER certificate installed in the browser connects immediately without reissuing or reconfiguring certificates.
