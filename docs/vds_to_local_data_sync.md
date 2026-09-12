# Technoreboot — VDS to Local Business Data Sync Guide
**Stage 08D-R1R4-SYNC: Permanent Operational Procedure**

---

## 1. Architectural Principles

Technoreboot operates under a strict two-directional boundary:

```text
CODE DIRECTION:          LOCAL DEV -> Git -> Production VDS
BUSINESS DATA DIRECTION: Production VDS -> LOCAL DEV Replica
FORBIDDEN DIRECTION:     LOCAL DEV -> Production VDS (STRICTLY PROHIBITED)
```

1. **VDS is Canonical Source of Truth:**
   All real products, catalog items, media/photos, repair orders, and sales live on VDS (`https://144.31.50.134`).
2. **Local Workstation is a Dev/Test Replica:**
   Local stack operates for development, testing, UI prototyping, and regression audits. Local data is a consumer/replica of production data.
3. **Data Parity on Demand:**
   Developers can pull fresh production state at any time using the one-way sync tool to test against actual production volume (149 products, 149 photos, 149 listings).
4. **Zero Reverse Contamination:**
   The sync tool and production deployment guards reject any attempt to push local test databases, dirty mock states, or local credentials to VDS.

---

## 2. Sync Tool Overview (`scripts/sync_vds_business_to_local.py`)

The sync tool automates safe, consistent, and verifiable synchronization from VDS to Local.

### Command-line Usage

```bash
# Standard one-way sync (creates fresh snapshot on VDS and syncs to local)
python scripts/sync_vds_business_to_local.py

# Sync from a specific existing VDS snapshot
python scripts/sync_vds_business_to_local.py --snapshot-path /tmp/TECHNOREBOOT_BACKUP_2026-09-12_103935.zip

# Dry run mode (validates connection, remote snapshot, and integrity without touching local files)
python scripts/sync_vds_business_to_local.py --dry-run

# Run without managing Docker containers (for standalone dev testing)
python scripts/sync_vds_business_to_local.py --no-docker
```

### Safety & Guard Rails

1. **Forbidden Reverse-Sync Arguments:**
   Arguments containing `--push`, `--upload`, `--to-vds`, `--reverse`, `--sync-to-vds`, or `--vds-dest` immediately trigger a fatal security violation exit:
   ```text
   SECURITY VIOLATION: REVERSE SYNC (LOCAL -> VDS) IS STRICTLY FORBIDDEN!
   Technoreboot policy dictates: Code flows LOCAL -> VDS; Data flows VDS -> LOCAL.
   ```

2. **Mandatory Local Safety Backup:**
   Before modifying any local business file, the script compresses the existing local database, storage, and avito state into:
   `.local-recovery/pre_sync_YYYYMMDD_HHMMSS.zip`
   and computes its SHA256 checksum.

3. **Integrity Validation:**
   The SHA256 of the remote ZIP on VDS is verified via SSH and compared against the downloaded archive before extraction begins.

4. **Strict Business Scope Isolation:**
   Only the following components are restored:
   - `database/technoreboot.db` -> `data/db/technoreboot.db` and `core/technoreboot.db`
   - `storage/` -> `data/storage/`
   - `avito-module/` -> `data/avito-module/`
   
   **Explicitly Excluded and Preserved:**
   - Local TLS server certificates (`data/auth/server/*`)
   - Local CA keys (`data/auth/ca/*.key`)
   - Local client private keys and certificates (`data/auth/certificates/*`, `data/auth/registry.json`)
   - Local secrets (`.env`, secrets files, pairing tokens)

5. **Post-Sync Parity Assertions:**
   The tool automatically verifies:
   - Local database matches the snapshot database checksum (`post_local_db_hash == snapshot_db_hash`)
   - Business table counts match VDS counts (`PRODUCTS`, `SALES`, `REPAIRS`, `PHOTOS`, `LISTINGS`)
   - Media file count matches VDS storage count

---

## 3. Standard Feature & Development Lifecycle

To develop new features or fixes safely:

```text
Step 1: Sync VDS business snapshot -> LOCAL
        python scripts/sync_vds_business_to_local.py

Step 2: Develop and test code locally
        pytest core/tests admin-shell/tests avito-module/tests tests

Step 3: Commit and push code to Git
        git add <code_files>
        git commit -m "Feature description"
        git push origin main

Step 4: Automatic VDS safety backup
        Triggered automatically by update_code_only.sh on VDS

Step 5: Code-only deploy to VDS
        ssh root@144.31.50.134 "bash /srv/technoreboot/app/deploy/production/update_code_only.sh origin/main"

Step 6: Verify VDS health and business preservation
        Verify 6 containers healthy, counts match pre-deploy state

Step 7: Refresh local business snapshot when needed
        python scripts/sync_vds_business_to_local.py
```

---

## 4. Local Recovery Procedure

If a local sync or test corrupts the local developer state, restore from `.local-recovery/`:

```python
import zipfile, shutil
from pathlib import Path

backup_zip = Path(".local-recovery/pre_sync_20260912_134134.zip")
with zipfile.ZipFile(backup_zip, "r") as zf:
    zf.extractall("data_restored_temp")
# Move database back
shutil.copy2("data_restored_temp/database/technoreboot.db", "data/db/technoreboot.db")
```
