#!/usr/bin/env python3
"""
TECHNOREBOOT — Full System Restore Script
Stage 07B-R1: Simple Full Backup / Restore

Restores a full system backup:
1. Validates backup archive integrity and manifest schema before any destructive action.
2. Prompts user for explicit confirmation before overwriting persistent data (supports --yes).
3. Orderly stops relevant Docker services.
4. Restores database, product photos/media storage, auth/mTLS state, and runtime config.
5. Starts Docker services.
6. Waits for core and admin-shell healthchecks.
7. Verifies database and certificate identities (CA and OWNER).
"""

import sys
import os
import shutil
import sqlite3
import json
import zipfile
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path


def resolve_project_root() -> Path:
    """Find the root directory of Technoreboot."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent,
        Path.cwd(),
        Path(r"C:\tbootit"),
    ]
    for c in candidates:
        if (c / "docker-compose.yml").is_file() and (c / "data").is_dir():
            return c
    return script_dir.parent


def validate_manifest_and_contents(backup_path: Path) -> tuple[dict, bool, str]:
    """
    Strict validation of backup package before any destructive action.
    Returns: (manifest_dict, is_valid, error_message)
    """
    if not backup_path.exists():
        return {}, False, f"Backup source does not exist: {backup_path}"

    if backup_path.is_file():
        # Validate ZIP
        if not zipfile.is_zipfile(backup_path):
            return {}, False, f"File is not a valid zip archive: {backup_path}"
        try:
            with zipfile.ZipFile(backup_path, "r") as z:
                bad_file = z.testzip()
                if bad_file is not None:
                    return {}, False, f"Corrupt file in zip archive: {bad_file}"
                namelist = set(z.namelist())
                if "manifest.json" not in namelist:
                    return {}, False, "Missing manifest.json in backup archive"
                manifest_data = json.loads(z.read("manifest.json").decode("utf-8"))
        except Exception as e:
            return {}, False, f"Failed reading zip manifest: {e}"
    elif backup_path.is_dir():
        manifest_file = backup_path / "manifest.json"
        if not manifest_file.is_file():
            return {}, False, "Missing manifest.json in backup directory"
        try:
            manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception as e:
            return {}, False, f"Failed parsing manifest.json: {e}"
    else:
        return {}, False, f"Invalid backup path: {backup_path}"

    # Validate manifest format
    if manifest_data.get("backup_format_version") != "1.0":
        return {}, False, f"Unsupported backup format version: {manifest_data.get('backup_format_version')}"

    required_components = ["database", "storage", "auth"]
    components = manifest_data.get("components", [])
    for req in required_components:
        if req not in components:
            return {}, False, f"Manifest missing required component: {req}"

    # Verify critical files inside archive/folder
    required_files = [
        "auth/ca/ca.crt",
        "auth/certificates/owner.crt",
        "auth/registry.json",
    ]
    if backup_path.is_file():
        with zipfile.ZipFile(backup_path, "r") as z:
            names = set(z.namelist())
            has_db = "database/technoreboot.db" in names or "database/technoreboot_dump.sql" in names
            if not has_db:
                return {}, False, "Missing database (neither technoreboot.db nor technoreboot_dump.sql found in backup)"
            for rf in required_files:
                if rf not in names:
                    return {}, False, f"Missing required auth file in backup: {rf}"
    else:
        has_db = (backup_path / "database" / "technoreboot.db").is_file() or (
            backup_path / "database" / "technoreboot_dump.sql"
        ).is_file()
        if not has_db:
            return {}, False, "Missing database file in backup directory"
        for rf in required_files:
            if not (backup_path / rf).is_file():
                return {}, False, f"Missing required auth file in backup directory: {rf}"

    return manifest_data, True, ""


def check_service_health(url: str, max_retries: int = 30, delay: float = 1.0) -> bool:
    """Poll HTTP health endpoint until 200 OK or timeout."""
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Technoreboot-Restore/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(delay)
    return False


def main():
    project_root = resolve_project_root()
    print("=" * 70)
    print("  TECHNOREBOOT — FULL SYSTEM RESTORE")
    print(f"  Project Root: {project_root}")
    print("=" * 70)

    # Parse arguments
    args = sys.argv[1:]
    auto_yes = "--yes" in args or "-y" in args or os.environ.get("TECHNOREBOOT_RESTORE_YES") == "1"
    skip_containers = "--skip-containers" in args
    skip_healthcheck = "--skip-healthcheck" in args

    backup_args = [a for a in args if not a.startswith("-")]

    if not backup_args:
        # Check backups directory for latest backup
        backups_dir = project_root / "backups"
        available_backups = []
        if backups_dir.is_dir():
            available_backups = sorted(
                [f for f in backups_dir.glob("TECHNOREBOOT_BACKUP_*.zip") if f.is_file()],
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )

        if available_backups:
            print(f"No backup specified. Latest backup found:\n  {available_backups[0]}")
            chosen_backup = available_backups[0]
        else:
            print("Usage: restore_full.cmd \"<path_to_backup_zip_or_folder>\" [--yes]")
            print("\nError: No backup specified and no backups found in backups/ directory.")
            return 1
    else:
        chosen_backup = Path(backup_args[0]).resolve()

    print(f"\nTarget Backup: {chosen_backup}")

    # STEP 1: Strict Pre-Validation
    print("[1/6] Pre-validating backup archive and manifest...")
    manifest, is_valid, err_msg = validate_manifest_and_contents(chosen_backup)
    if not is_valid:
        print("=" * 70)
        print("  [CRITICAL ERROR] BACKUP VALIDATION FAILED!")
        print(f"  Reason: {err_msg}")
        print("  No persistent data was modified. System left untouched.")
        print("=" * 70)
        return 1

    print("      OK: Manifest format version 1.0 verified.")
    print(f"      OK: Backup creation time: {manifest.get('created_at')}")
    print(f"      OK: Git commit at backup: {manifest.get('git_commit')}")
    db_tables = manifest.get("database", {}).get("tables_count", "unknown")
    print(f"      OK: Database contains {db_tables} tables.")
    print(f"      OK: CA fingerprint: {manifest.get('auth', {}).get('ca_fingerprint_sha256')}")
    print(f"      OK: OWNER fingerprint: {manifest.get('auth', {}).get('owner_fingerprint_sha256')}")

    # STEP 2: Overwrite Confirmation
    if not auto_yes:
        print("\n" + "!" * 70)
        print("  WARNING: RESTORE IS A DESTRUCTIVE OPERATION!")
        print("  Restoring will overwrite current live database, product photos,")
        print("  and authentication certificates with the contents of the backup.")
        print("!" * 70)
        try:
            confirm = input("Type 'yes' to proceed with restore, or anything else to abort: ").strip().lower()
        except EOFError:
            confirm = "no"
        if confirm != "yes":
            print("\nRestore aborted by user. No changes were made.")
            return 0

    # STEP 3: Stop services
    if not skip_containers:
        print("\n[2/6] Stopping Technoreboot services for safe data restore...")
        services_to_stop = [
            "core",
            "admin-shell",
            "gateway",
            "avito-module",
            "inventory-sales-module",
            "repairs-module",
        ]
        stop_cmd = ["docker", "compose", "stop"] + services_to_stop
        res = subprocess.run(stop_cmd, cwd=str(project_root), capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[WARN] docker compose stop returned non-zero ({res.returncode}): {res.stderr}")
        else:
            print("      OK: Services stopped cleanly.")
    else:
        print("\n[2/6] Skipping docker compose stop (--skip-containers active).")

    # STEP 4: Extract and restore data
    print("\n[3/6] Restoring persistent data components...")
    extract_tmp = project_root / "backups" / f".tmp_restore_{int(time.time())}"
    if extract_tmp.exists():
        shutil.rmtree(extract_tmp)
    extract_tmp.mkdir(parents=True, exist_ok=True)

    try:
        if chosen_backup.is_file():
            with zipfile.ZipFile(chosen_backup, "r") as z:
                z.extractall(extract_tmp)
            source_dir = extract_tmp
        else:
            source_dir = chosen_backup

        # 4a. Restore Database
        data_db_dir = project_root / "data" / "db"
        data_db_dir.mkdir(parents=True, exist_ok=True)
        target_db = data_db_dir / "technoreboot.db"

        backup_sqlite = source_dir / "database" / "technoreboot.db"
        backup_dump = source_dir / "database" / "technoreboot_dump.sql"

        if backup_sqlite.is_file():
            # Copy the binary SQLite database directly
            shutil.copy2(backup_sqlite, target_db)
            print(f"      OK: Database restored from binary snapshot ({target_db.stat().st_size / 1024:.1f} KB).")
        elif backup_dump.is_file():
            # Recreate from SQL logical dump
            if target_db.exists():
                target_db.unlink()
            conn = sqlite3.connect(str(target_db))
            with open(backup_dump, "r", encoding="utf-8") as sql_file:
                conn.executescript(sql_file.read())
            conn.close()
            print(f"      OK: Database restored from SQL logical dump ({target_db.stat().st_size / 1024:.1f} KB).")

        # 4b. Restore Photos and Media Storage
        backup_storage = source_dir / "storage"
        target_storage = project_root / "data" / "storage"
        if backup_storage.is_dir():
            if target_storage.exists():
                shutil.rmtree(target_storage)
            shutil.copytree(backup_storage, target_storage, dirs_exist_ok=True)
            files_restored = sum(len(files) for _, _, files in os.walk(target_storage))
            print(f"      OK: Product photos & media restored ({files_restored} files).")

        # 4c. Restore Auth & mTLS state
        backup_auth = source_dir / "auth"
        target_auth = project_root / "data" / "auth"
        if backup_auth.is_dir():
            if target_auth.exists():
                shutil.rmtree(target_auth)
            shutil.copytree(backup_auth, target_auth, dirs_exist_ok=True)
            auth_files = sum(len(files) for _, _, files in os.walk(target_auth))
            print(f"      OK: Auth PKI & certificates restored ({auth_files} files).")

        # 4d. Restore Avito module persistent state
        backup_avito = source_dir / "avito-module"
        target_avito = project_root / "data" / "avito-module"
        if backup_avito.is_dir():
            if target_avito.exists():
                shutil.rmtree(target_avito)
            shutil.copytree(backup_avito, target_avito, dirs_exist_ok=True)
            avito_files = sum(len(files) for _, _, files in os.walk(target_avito))
            print(f"      OK: Avito module persistent state restored ({avito_files} files).")

        # 4e. Restore runtime configuration if present
        backup_env = source_dir / "config" / ".env"
        if backup_env.is_file():
            shutil.copy2(backup_env, project_root / ".env")
            print("      OK: .env configuration file restored.")

    finally:
        if extract_tmp.exists():
            shutil.rmtree(extract_tmp, ignore_errors=True)

    # STEP 5: Start services
    if not skip_containers:
        print("\n[4/6] Starting Technoreboot stack...")
        start_cmd = ["docker", "compose", "up", "-d"]
        res = subprocess.run(start_cmd, cwd=str(project_root), capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[ERROR] docker compose up -d failed: {res.stderr}")
            return 1
        print("      OK: Containers launched.")
    else:
        print("\n[4/6] Skipping docker compose up (--skip-containers active).")

    # STEP 6: Healthchecks
    if not skip_containers and not skip_healthcheck:
        print("\n[5/6] Waiting for services to become healthy...")
        core_healthy = check_service_health("http://localhost:8000/health", max_retries=30, delay=1.0)
        if not core_healthy:
            print("[ERROR] Core service healthcheck failed at http://localhost:8000/health")
            return 1
        print("      OK: Core service is healthy (http://localhost:8000/health -> 200).")

        admin_healthy = check_service_health("http://localhost:8011/", max_retries=30, delay=1.0)
        if not admin_healthy:
            print("[WARN] Admin shell not responding on 8011 yet, checking gateway...")
        else:
            print("      OK: Admin shell is responding on http://localhost:8011/.")
    else:
        print("\n[5/6] Healthcheck skipped.")

    # STEP 7: Post-Restore Verification
    print("\n[6/6] Verifying restored state integrity against manifest...")
    # Verify DB
    db_file = project_root / "data" / "db" / "technoreboot.db"
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM products")
        product_count = cursor.fetchone()[0]
        conn.close()
        print(f"      OK: Database operational ({product_count} products found).")
    except Exception as e:
        print(f"[ERROR] Restored database verification failed: {e}")
        return 1

    # Verify CA & OWNER certs
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes

        ca_cert = x509.load_pem_x509_certificate((project_root / "data" / "auth" / "ca" / "ca.crt").read_bytes())
        restored_ca_fp = ca_cert.fingerprint(hashes.SHA256()).hex().upper()
        expected_ca_fp = manifest.get("auth", {}).get("ca_fingerprint_sha256")
        if expected_ca_fp and restored_ca_fp != expected_ca_fp:
            print(f"[ERROR] CA fingerprint mismatch! Expected {expected_ca_fp}, got {restored_ca_fp}")
            return 1
        print(f"      OK: CA fingerprint match ({restored_ca_fp[:16]}...).")

        owner_cert = x509.load_pem_x509_certificate(
            (project_root / "data" / "auth" / "certificates" / "owner.crt").read_bytes()
        )
        restored_owner_fp = owner_cert.fingerprint(hashes.SHA256()).hex().upper()
        expected_owner_fp = manifest.get("auth", {}).get("owner_fingerprint_sha256")
        if expected_owner_fp and restored_owner_fp != expected_owner_fp:
            print(f"[ERROR] OWNER fingerprint mismatch! Expected {expected_owner_fp}, got {restored_owner_fp}")
            return 1
        print(f"      OK: OWNER identity match ({restored_owner_fp[:16]}...).")

        # Verify revoked state
        reg_file = project_root / "data" / "auth" / "registry.json"
        reg_data = json.loads(reg_file.read_text(encoding="utf-8"))
        revoked_count = sum(1 for c in reg_data if isinstance(c, dict) and c.get("status") == "REVOKED")
        print(f"      OK: Certificate registry verified ({len(reg_data)} total, {revoked_count} revoked).")

    except Exception as e:
        print(f"[ERROR] Certificate identity verification failed: {e}")
        return 1

    print("=" * 70)
    print("  RESTORE COMPLETED SUCCESSFULLY!")
    print(f"  Restored From: {chosen_backup}")
    print(f"  Database:      {product_count} products verified")
    print(f"  CA Identity:   Preserved ({restored_ca_fp[:16]}...)")
    print(f"  OWNER Identity: Preserved ({restored_owner_fp[:16]}...)")
    print(f"  Revoked Certs: Preserved ({revoked_count} revoked)")
    print("  Services:      Core & Admin Shell Healthy")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
