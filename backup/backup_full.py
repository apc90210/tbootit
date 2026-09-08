#!/usr/bin/env python3
"""
TECHNOREBOOT — Full System Backup Script
Stage 07B-R1: Simple Full Backup / Restore

Creates a self-contained, timestamped backup archive of:
- SQLite database (online consistent snapshot + logical SQL dump)
- Uploaded product photos and media storage (data/storage/)
- Authentication state & mTLS PKI (data/auth/: CA, OWNER, user certs, registry.json, server keys)
- Avito module persistent data (data/avito-module/)
- Runtime configuration (.env if present)
- Backup manifest (manifest.json)
"""

import sys
import os
import shutil
import sqlite3
import json
import zipfile
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def resolve_project_root() -> Path:
    """Find the root directory of Technoreboot (where docker-compose.yml lives)."""
    # 1. Start from script parent's parent
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


def get_git_info(project_root: Path) -> dict:
    """Retrieve current git commit and branch safely."""
    info = {"commit": "unknown", "branch": "unknown"}
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            info["commit"] = res.stdout.strip()
    except Exception:
        pass

    try:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout.strip():
            info["branch"] = res.stdout.strip()
    except Exception:
        pass

    return info


def inspect_ca_and_owner(auth_dir: Path) -> dict:
    """Extract fingerprints and identities from auth data for the manifest."""
    details = {
        "ca_fingerprint_sha256": None,
        "owner_fingerprint_sha256": None,
        "owner_serial_hex": None,
        "total_certificates_in_registry": 0,
        "revoked_certificates_count": 0,
    }

    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes

        ca_file = auth_dir / "ca" / "ca.crt"
        if ca_file.is_file():
            ca_cert = x509.load_pem_x509_certificate(ca_file.read_bytes())
            details["ca_fingerprint_sha256"] = ca_cert.fingerprint(hashes.SHA256()).hex().upper()

        owner_file = auth_dir / "certificates" / "owner.crt"
        if owner_file.is_file():
            owner_cert = x509.load_pem_x509_certificate(owner_file.read_bytes())
            details["owner_fingerprint_sha256"] = owner_cert.fingerprint(hashes.SHA256()).hex().upper()
            details["owner_serial_hex"] = hex(owner_cert.serial_number)[2:].upper()
    except Exception as e:
        print(f"[WARN] Failed reading certificates with cryptography: {e}")

    registry_file = auth_dir / "registry.json"
    if registry_file.is_file():
        try:
            reg_data = json.loads(registry_file.read_text(encoding="utf-8"))
            if isinstance(reg_data, list):
                details["total_certificates_in_registry"] = len(reg_data)
                details["revoked_certificates_count"] = sum(
                    1 for c in reg_data if isinstance(c, dict) and c.get("status") == "REVOKED"
                )
            elif isinstance(reg_data, dict):
                certs = reg_data.get("certificates", [])
                details["total_certificates_in_registry"] = len(certs)
                details["revoked_certificates_count"] = sum(
                    1 for c in certs if isinstance(c, dict) and c.get("status") == "REVOKED"
                )
        except Exception as e:
            print(f"[WARN] Failed reading registry.json: {e}")

    return details


def backup_database(src_db_path: Path, dst_db_path: Path, dst_dump_path: Path) -> dict:
    """
    Safely snapshot SQLite database using Python sqlite3 online backup API,
    and generate logical SQL text dump.
    """
    stats = {"tables_count": 0, "tables": {}, "total_rows": 0}
    if not src_db_path.is_file():
        raise FileNotFoundError(f"Database file not found: {src_db_path}")

    dst_db_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Consistent online binary backup
    src_conn = sqlite3.connect(f"file:{src_db_path}?mode=ro", uri=True)
    try:
        dst_conn = sqlite3.connect(str(dst_db_path))
        try:
            src_conn.backup(dst_conn, pages=100)
        finally:
            dst_conn.close()

        # 2. Logical text SQL dump
        dst_dump_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dst_dump_path, "w", encoding="utf-8") as f:
            for line in src_conn.iterdump():
                f.write(f"{line}\n")

        # 3. Collect table stats
        cursor = src_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        table_names = [row[0] for row in cursor.fetchall()]
        stats["tables_count"] = len(table_names)
        for tbl in table_names:
            try:
                cursor.execute(f'SELECT count(*) FROM "{tbl}"')
                cnt = cursor.fetchone()[0]
                stats["tables"][tbl] = cnt
                stats["total_rows"] += cnt
            except Exception:
                stats["tables"][tbl] = 0
    finally:
        src_conn.close()

    return stats


def copy_tree_files(src_dir: Path, dst_dir: Path) -> tuple[int, int]:
    """Copy directory recursively and return (files_count, total_bytes)."""
    if not src_dir.is_dir():
        return 0, 0

    count = 0
    total_bytes = 0
    for root, dirs, files in os.walk(src_dir):
        rel_root = Path(root).relative_to(src_dir)
        target_root = dst_dir / rel_root
        target_root.mkdir(parents=True, exist_ok=True)
        for file in files:
            src_file = Path(root) / file
            dst_file = target_root / file
            shutil.copy2(src_file, dst_file)
            count += 1
            try:
                total_bytes += src_file.stat().st_size
            except Exception:
                pass
    return count, total_bytes


def main():
    project_root = resolve_project_root()
    print("=" * 70)
    print("  TECHNOREBOOT — FULL SYSTEM BACKUP")
    print(f"  Project Root: {project_root}")
    print("=" * 70)

    # Output path handling
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    default_backup_dir = project_root / "backups"
    default_backup_dir.mkdir(parents=True, exist_ok=True)

    output_arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
    if output_arg:
        custom_path = Path(output_arg)
        if custom_path.is_dir() or custom_path.suffix == "":
            output_archive = custom_path / f"TECHNOREBOOT_BACKUP_{timestamp_str}.zip"
            custom_path.mkdir(parents=True, exist_ok=True)
        else:
            output_archive = custom_path
            output_archive.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_archive = default_backup_dir / f"TECHNOREBOOT_BACKUP_{timestamp_str}.zip"

    # Temporary staging directory
    staging_dir = default_backup_dir / f".tmp_staging_{timestamp_str}"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    try:
        print("[1/5] Backing up SQLite database...")
        db_src = project_root / "data" / "db" / "technoreboot.db"
        dst_db = staging_dir / "database" / "technoreboot.db"
        dst_sql = staging_dir / "database" / "technoreboot_dump.sql"
        db_stats = backup_database(db_src, dst_db, dst_sql)
        print(f"      OK: {db_stats['tables_count']} tables, {db_stats['total_rows']} total rows captured.")
        print(f"      Snapshot: {dst_db.name} ({dst_db.stat().st_size / 1024:.1f} KB)")
        print(f"      Logical dump: {dst_sql.name} ({dst_sql.stat().st_size / 1024:.1f} KB)")

        print("[2/5] Backing up product photos and media storage...")
        storage_src = project_root / "data" / "storage"
        storage_dst = staging_dir / "storage"
        storage_files, storage_bytes = copy_tree_files(storage_src, storage_dst)
        print(f"      OK: {storage_files} media files ({storage_bytes / (1024*1024):.2f} MB).")

        print("[3/5] Backing up authentication & mTLS state (data/auth)...")
        auth_src = project_root / "data" / "auth"
        auth_dst = staging_dir / "auth"
        auth_files, auth_bytes = copy_tree_files(auth_src, auth_dst)
        auth_metrics = inspect_ca_and_owner(auth_dst)
        print(f"      OK: {auth_files} auth files ({auth_bytes / 1024:.1f} KB).")
        print(f"      CA Fingerprint SHA256: {auth_metrics['ca_fingerprint_sha256']}")
        print(f"      OWNER Fingerprint SHA256: {auth_metrics['owner_fingerprint_sha256']}")
        print(f"      Registry: {auth_metrics['total_certificates_in_registry']} certs ({auth_metrics['revoked_certificates_count']} revoked).")

        print("[4/5] Backing up Avito module state and runtime configuration...")
        avito_src = project_root / "data" / "avito-module"
        avito_dst = staging_dir / "avito-module"
        avito_files, avito_bytes = copy_tree_files(avito_src, avito_dst)
        print(f"      OK: {avito_files} avito persistent files ({avito_bytes / 1024:.1f} KB).")

        env_src = project_root / ".env"
        if env_src.is_file():
            shutil.copy2(env_src, staging_dir / "config" / ".env")
            print("      OK: .env configuration file copied.")
        else:
            print("      INFO: .env file not present in root (using compose defaults).")

        # Build Manifest
        git_info = get_git_info(project_root)
        manifest = {
            "backup_format_version": "1.0",
            "backup_type": "full",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_project_path": str(project_root),
            "git_commit": git_info["commit"],
            "git_branch": git_info["branch"],
            "components": ["database", "storage", "auth", "avito-module", "config"],
            "database": {
                "sqlite_file": "database/technoreboot.db",
                "sql_dump_file": "database/technoreboot_dump.sql",
                "tables_count": db_stats["tables_count"],
                "total_rows": db_stats["total_rows"],
                "tables": db_stats["tables"],
            },
            "storage": {
                "files_count": storage_files,
                "total_bytes": storage_bytes,
            },
            "auth": {
                "ca_fingerprint_sha256": auth_metrics["ca_fingerprint_sha256"],
                "owner_fingerprint_sha256": auth_metrics["owner_fingerprint_sha256"],
                "owner_serial_hex": auth_metrics["owner_serial_hex"],
                "total_certificates": auth_metrics["total_certificates_in_registry"],
                "revoked_certificates": auth_metrics["revoked_certificates_count"],
            },
            "avito": {
                "files_count": avito_files,
                "total_bytes": avito_bytes,
            },
        }

        manifest_path = staging_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"[5/5] Compressing full backup archive into {output_archive.name}...")
        total_uncompressed = 0
        total_files = 0
        with zipfile.ZipFile(output_archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zip_out:
            for root, dirs, files in os.walk(staging_dir):
                for f in files:
                    file_path = Path(root) / f
                    arcname = file_path.relative_to(staging_dir).as_posix()
                    zip_out.write(file_path, arcname=arcname)
                    total_uncompressed += file_path.stat().st_size
                    total_files += 1

        archive_size = output_archive.stat().st_size
        print("=" * 70)
        print("  BACKUP COMPLETED SUCCESSFULLY!")
        print(f"  Output Archive: {output_archive}")
        print(f"  Archive Size:   {archive_size / (1024*1024):.2f} MB ({archive_size} bytes)")
        print(f"  Uncompressed:   {total_uncompressed / (1024*1024):.2f} MB across {total_files} files")
        print(f"  Database:       {db_stats['tables_count']} tables, {db_stats['total_rows']} records")
        print(f"  Storage Photos: {storage_files} files")
        print(f"  Auth PKI:       CA={auth_metrics['ca_fingerprint_sha256'][:16]}..., Owner={auth_metrics['owner_fingerprint_sha256'][:16]}...")
        print("=" * 70)
        return 0

    except Exception as e:
        print(f"\n[ERROR] Backup failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        if output_archive.exists():
            try:
                output_archive.unlink()
            except Exception:
                pass
        return 1

    finally:
        # Clean up staging directory
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
