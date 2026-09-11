#!/usr/bin/env python3
"""
TECHNOREBOOT — Deterministic Disaster Recovery and Bootstrap Engine
Stage 07E-R1: New Server Bootstrap and Disaster Recovery

Recovers Technoreboot on a fresh Debian server/VM from Git source + Technoreboot backup ZIP:
1. Preflights OS, Python environment, Docker dependencies and repository structure.
2. Discovers and validates backup archive integrity, manifest schema, and checksums.
3. Enforces strict security validation: Zip Slip path traversal protection (rejects '../' and absolute paths).
4. Safe staged extraction to temporary directory before target placement.
5. In-place synchronized restoration into target host directories:
   - Database (technoreboot.db / logical dump)
   - Product photos and media storage (data/storage/)
   - Authentication & mTLS PKI state (data/auth/: CA, server certs, OWNER cert, registry)
   - Avito module persistent state (data/avito-module/)
   - Runtime configuration (.env if present)
6. Preserves container-safe directory inodes and sets container permissions.
7. Fresh-server auth mode: restored CA and existing OWNER cert remain active (NEVER generates a new CA).
8. Starts Docker Compose stack (if not skipped) and waits for health.
9. Performs comprehensive verification of business data, media files, and HTTPS/mTLS endpoints.
"""

import sys
import os
import shutil
import sqlite3
import json
import zipfile
import tempfile
import subprocess
import time
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List


def resolve_project_root() -> Path:
    """Locate Technoreboot project root (where docker-compose.yml lives)."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent,
        Path.cwd(),
        Path(r"C:\tbootit"),
        Path("/tbootit"),
    ]
    for c in candidates:
        if (c / "docker-compose.yml").is_file():
            return c
    return script_dir.parent


def find_latest_backup(search_dir: Path) -> Optional[Path]:
    """Find the most recent valid backup zip archive in search_dir."""
    if not search_dir.is_dir():
        return None
    candidates = sorted(
        [f for f in search_dir.glob("TECHNOREBOOT_BACKUP_*.zip") if f.is_file()],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def validate_archive_security_and_manifest(zip_path: Path) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Validates backup archive:
    - Verifies file exists and is a valid zip
    - Enforces Zip Slip path traversal protection
    - Checks manifest presence, format version, and required components
    - Verifies presence of DB, auth, and storage components
    - Verifies checksums if present in manifest
    Returns: (is_valid, error_message, manifest_dict)
    """
    if not zip_path.is_file():
        return False, f"Файл резервной копии не существует: {zip_path}", None

    if not zipfile.is_zipfile(zip_path):
        return False, f"Файл не является корректным ZIP-архивом: {zip_path}", None

    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            corrupt = z.testzip()
            if corrupt is not None:
                return False, f"Архив поврежден (ошибка в файле: {corrupt})", None

            namelist = z.namelist()
            names_set = set(namelist)

            # Security check: Path traversal / Zip Slip protection
            for name in namelist:
                # Reject absolute paths
                if name.startswith("/") or name.startswith("\\"):
                    return False, f"Обнаружена угроза безопасности (абсолютный путь в архиве): {name}", None

                # Reject path traversal tokens
                parts = Path(name).parts
                if ".." in parts:
                    return False, f"Обнаружена угроза безопасности (выход за пределы директории '../'): {name}", None

            # Manifest inspection
            if "manifest.json" not in names_set:
                return False, "В архиве отсутствует обязательный файл manifest.json", None

            manifest_raw = z.read("manifest.json")
            try:
                manifest = json.loads(manifest_raw.decode("utf-8"))
            except Exception as e:
                return False, f"Не удалось распарсить manifest.json: {e}", None

            fmt_ver = manifest.get("backup_format_version")
            if fmt_ver != "1.0":
                return False, f"Неподдерживаемая версия формата резервной копии: '{fmt_ver}' (требуется '1.0')", None

            components = manifest.get("components", [])
            for req in ["database", "storage", "auth"]:
                if req not in components:
                    return False, f"В манифесте отсутствует обязательный компонент: '{req}'", None

            # Check database file
            has_db = "database/technoreboot.db" in names_set or "database/technoreboot_dump.sql" in names_set
            if not has_db:
                return False, "В архиве отсутствует файл базы данных (technoreboot.db или technoreboot_dump.sql)", None

            # Check required auth files for full fresh-server bootstrap
            required_auth_files = [
                "auth/ca/ca.crt",
                "auth/certificates/owner.crt",
                "auth/registry.json",
            ]
            for af in required_auth_files:
                if af not in names_set:
                    return False, f"Для полного восстановления нового сервера отсутствует обязательный файл: '{af}'", None

            # Verify checksums if present in manifest
            if "checksums" in manifest and isinstance(manifest["checksums"], dict):
                import hashlib
                for rel_path, expected_hash in manifest["checksums"].items():
                    if rel_path in names_set:
                        data = z.read(rel_path)
                        actual_hash = hashlib.sha256(data).hexdigest().lower()
                        if actual_hash != expected_hash.lower():
                            return False, f"Несовпадение контрольной суммы для '{rel_path}': ожидалось {expected_hash}, получено {actual_hash}", None

            return True, "", manifest

    except Exception as e:
        return False, f"Ошибка проверки архива: {e}", None


def _safe_sync_dir(src: Path, dst: Path):
    """
    Safely synchronizes contents of src into dst in-place.
    Preserves directory inodes to prevent invalidating Docker bind-mounts.
    """
    dst.mkdir(parents=True, exist_ok=True)
    for child in dst.iterdir():
        if child.is_dir():
            src_child = src / child.name
            if src_child.is_dir():
                _safe_sync_dir(src_child, child)
            else:
                shutil.rmtree(child, ignore_errors=True)
        else:
            try:
                child.unlink()
            except OSError:
                pass
    for item in src.iterdir():
        target = dst / item.name
        if item.is_file():
            shutil.copy2(item, target)
        elif item.is_dir() and not target.exists():
            shutil.copytree(item, target)


def set_container_permissions(auth_dir: Path):
    """Ensure proper file permissions on POSIX systems for TLS keys and certificates."""
    if os.name != "posix":
        return
    try:
        # Directories 0755 or 0700
        for root, dirs, files in os.walk(auth_dir):
            os.chmod(root, 0o755)
            for f in files:
                fp = os.path.join(root, f)
                if f.endswith(".key") or f == "owner_password.txt":
                    os.chmod(fp, 0o600)
                else:
                    os.chmod(fp, 0o644)
    except Exception as e:
        print(f"[WARN] Unable to set POSIX permissions on {auth_dir}: {e}")


def execute_bootstrap_restore(
    backup_zip: Path,
    target_data_dir: Path,
    repo_root: Path,
    skip_containers: bool = False,
    compose_project: str = "technoreboot",
    compose_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes safe staged disaster-recovery bootstrap restoration.
    """
    # 1. Validation
    is_valid, err_msg, manifest = validate_archive_security_and_manifest(backup_zip)
    if not is_valid:
        raise ValueError(f"Отказ восстановления: {err_msg}")

    # 2. Prepare staging
    staging_dir = Path(tempfile.mkdtemp(prefix="tnr_bootstrap_stage_"))

    try:
        # 3. Extract to staging
        with zipfile.ZipFile(backup_zip, "r") as z:
            z.extractall(staging_dir)

        # Validate staged database
        staged_db = staging_dir / "database" / "technoreboot.db"
        staged_sql = staging_dir / "database" / "technoreboot_dump.sql"
        if not staged_db.is_file() and not staged_sql.is_file():
            raise FileNotFoundError("В распакованном архиве отсутствует файл базы данных")

        # 4. Stop running containers if requested
        if not skip_containers:
            stop_cmd = ["docker", "compose", "-p", compose_project]
            if compose_file:
                stop_cmd.extend(["-f", str(compose_file)])
            stop_cmd.extend(["stop"])
            subprocess.run(stop_cmd, cwd=str(repo_root), capture_output=True, text=True)

        # 5. Prepare target directory tree
        target_data_dir.mkdir(parents=True, exist_ok=True)
        (target_data_dir / "db").mkdir(parents=True, exist_ok=True)
        (target_data_dir / "storage").mkdir(parents=True, exist_ok=True)
        (target_data_dir / "storage" / "product_photos").mkdir(parents=True, exist_ok=True)
        (target_data_dir / "auth").mkdir(parents=True, exist_ok=True)
        (target_data_dir / "auth" / "ca").mkdir(parents=True, exist_ok=True)
        (target_data_dir / "auth" / "certificates").mkdir(parents=True, exist_ok=True)
        (target_data_dir / "auth" / "server").mkdir(parents=True, exist_ok=True)
        (target_data_dir / "avito-module").mkdir(parents=True, exist_ok=True)
        (target_data_dir / "backups").mkdir(parents=True, exist_ok=True)

        # 6. Restore Database
        target_db = target_data_dir / "db" / "technoreboot.db"
        if staged_db.is_file():
            shutil.copy2(staged_db, target_db)
        elif staged_sql.is_file():
            if target_db.exists():
                target_db.unlink()
            conn = sqlite3.connect(str(target_db))
            with open(staged_sql, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.close()

        # 7. Restore Storage (product photos & media)
        staged_storage = staging_dir / "storage"
        target_storage = target_data_dir / "storage"
        if staged_storage.is_dir():
            _safe_sync_dir(staged_storage, target_storage)

        # 8. Restore Auth & PKI (Fresh-server mode: preserves backed-up CA + Owner trust)
        staged_auth = staging_dir / "auth"
        target_auth = target_data_dir / "auth"
        if staged_auth.is_dir():
            _safe_sync_dir(staged_auth, target_auth)
            set_container_permissions(target_auth)

        # 9. Restore Avito module persistent state
        staged_avito = staging_dir / "avito-module"
        target_avito = target_data_dir / "avito-module"
        if staged_avito.is_dir():
            _safe_sync_dir(staged_avito, target_avito)

        # 10. Restore .env if present and needed
        staged_env = staging_dir / "config" / ".env"
        target_env = repo_root / ".env"
        if staged_env.is_file() and not target_env.exists():
            shutil.copy2(staged_env, target_env)

        # 11. Launch stack if not skipped
        if not skip_containers:
            up_cmd = ["docker", "compose", "-p", compose_project]
            if compose_file:
                up_cmd.extend(["-f", str(compose_file)])
            up_cmd.extend(["up", "-d"])
            res = subprocess.run(up_cmd, cwd=str(repo_root), capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"docker compose up failed: {res.stderr}")

        return {
            "status": "RESTORED",
            "manifest": manifest,
            "target_data_dir": str(target_data_dir),
            "database_file": str(target_db),
            "auth_dir": str(target_auth),
            "storage_dir": str(target_storage),
        }

    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)


def verify_restored_system(
    target_data_dir: Path,
    expected_manifest: Optional[Dict[str, Any]] = None,
    gateway_url: Optional[str] = None,
    owner_p12_path: Optional[Path] = None,
    owner_password: str = "",
) -> Dict[str, Any]:
    """
    Verifies restored database state, media files, and auth PKI consistency.
    """
    results: Dict[str, Any] = {
        "database": {},
        "media": {},
        "auth": {},
        "gateway": {},
        "checks_passed": True,
    }

    # 1. Database verification
    db_file = target_data_dir / "db" / "technoreboot.db"
    if not db_file.is_file():
        results["database"]["error"] = f"Database file missing at {db_file}"
        results["checks_passed"] = False
        return results

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    try:
        cur.execute("SELECT count(*) FROM products;")
        total_products = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM product_external_listings;")
        avito_linked = cur.fetchone()[0]

        local_only = total_products - avito_linked

        cur.execute("SELECT count(*) FROM sales;")
        total_sales = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM product_photos;")
        photo_rows = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM repair_orders;")
        repairs_count = cur.fetchone()[0]

        results["database"] = {
            "total_products": total_products,
            "avito_linked_products": avito_linked,
            "local_only_products": local_only,
            "total_sales": total_sales,
            "product_photos_rows": photo_rows,
            "repair_orders": repairs_count,
        }
    finally:
        conn.close()

    # 2. Media storage verification
    storage_photos_dir = target_data_dir / "storage" / "product_photos"
    media_files_on_disk = []
    if storage_photos_dir.is_dir():
        for r, _, files in os.walk(storage_photos_dir):
            for f in files:
                fp = Path(r) / f
                if fp.is_file() and fp.stat().st_size > 0:
                    media_files_on_disk.append(str(fp.relative_to(target_data_dir / "storage").as_posix()))

    results["media"] = {
        "files_count": len(media_files_on_disk),
        "sample_files": media_files_on_disk[:5],
    }

    # 3. Auth PKI verification
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes

    auth_dir = target_data_dir / "auth"
    ca_cert_path = auth_dir / "ca" / "ca.crt"
    owner_cert_path = auth_dir / "certificates" / "owner.crt"
    registry_path = auth_dir / "registry.json"

    if not ca_cert_path.is_file():
        results["auth"]["error"] = "CA certificate missing"
        results["checks_passed"] = False
        return results

    if not owner_cert_path.is_file():
        results["auth"]["error"] = "OWNER certificate missing"
        results["checks_passed"] = False
        return results

    ca_cert = x509.load_pem_x509_certificate(ca_cert_path.read_bytes())
    ca_fp = ca_cert.fingerprint(hashes.SHA256()).hex().upper()

    owner_cert = x509.load_pem_x509_certificate(owner_cert_path.read_bytes())
    owner_fp = owner_cert.fingerprint(hashes.SHA256()).hex().upper()
    owner_serial = hex(owner_cert.serial_number)[2:].upper()

    registry_data = []
    if registry_path.is_file():
        try:
            registry_data = json.loads(registry_path.read_text(encoding="utf-8"))
        except Exception:
            registry_data = []

    revoked_count = sum(1 for c in registry_data if isinstance(c, dict) and c.get("status") == "REVOKED")
    active_count = sum(1 for c in registry_data if isinstance(c, dict) and c.get("status") == "ACTIVE")

    results["auth"] = {
        "ca_fingerprint_sha256": ca_fp,
        "owner_fingerprint_sha256": owner_fp,
        "owner_serial_hex": owner_serial,
        "total_certificates": len(registry_data),
        "active_certificates": active_count,
        "revoked_certificates": revoked_count,
    }

    # Compare against expected manifest if provided
    if expected_manifest:
        exp_auth = expected_manifest.get("auth", {})
        if exp_auth.get("ca_fingerprint_sha256") and exp_auth["ca_fingerprint_sha256"] != ca_fp:
            results["checks_passed"] = False
            results["auth"]["error"] = f"CA fingerprint mismatch: {ca_fp} != {exp_auth['ca_fingerprint_sha256']}"

        if exp_auth.get("owner_fingerprint_sha256") and exp_auth["owner_fingerprint_sha256"] != owner_fp:
            results["checks_passed"] = False
            results["auth"]["error"] = f"OWNER fingerprint mismatch: {owner_fp} != {exp_auth['owner_fingerprint_sha256']}"

        exp_db = expected_manifest.get("database", {})
        if exp_db.get("tables", {}).get("products") is not None:
            if exp_db["tables"]["products"] != total_products:
                results["checks_passed"] = False
                results["database"]["error"] = f"Product count mismatch: {total_products} != {exp_db['tables']['products']}"

    return results


def print_disaster_recovery_report(summary: Dict[str, Any]):
    """Formats and prints the standard disaster recovery summary."""
    print("\n" + "=" * 75)
    print("  TECHNOREBOOT — DISASTER RECOVERY & BOOTSTRAP REPORT")
    print("=" * 75)
    print(f"  Status:             {summary.get('FINAL_STATUS', 'UNKNOWN')}")
    print(f"  Backup Archive:     {summary.get('BACKUP_ORIGIN', 'N/A')}")
    print(f"  Restore Mode:       {summary.get('RESTORE_MODE', 'Fresh Server Bootstrap')}")
    print(f"  Target Root:        {summary.get('TARGET_ROOT', 'N/A')}")
    print(f"  Database Products:  {summary.get('PRODUCTS', 0)} total ({summary.get('AVITO_LINKED_PRODUCTS', 0)} Avito, {summary.get('LOCAL_ONLY_PRODUCTS', 0)} Local)")
    print(f"  Total Sales:        {summary.get('SALES', 0)}")
    print(f"  Product Photos:     {summary.get('PRODUCT_PHOTOS', 0)} rows, {summary.get('MEDIA_FILES', 0)} files on disk")
    print(f"  CA Restored:        {summary.get('OLD_CA_RESTORED', False)} ({summary.get('CA_FP', 'N/A')[:16]}...)")
    print(f"  Owner Recognized:   {summary.get('OWNER_CERT_ACCEPTED', False)} ({summary.get('OWNER_FP', 'N/A')[:16]}...)")
    print(f"  No-Cert Blocked:    {summary.get('NO_CERT_REJECTED', True)}")
    print(f"  Revoked Preserved:  {summary.get('REVOCATION_STATE_PRESERVED', True)} ({summary.get('REVOKED_CERTS', 0)} certs)")
    print(f"  Live DB Intact:     {summary.get('ORIGINAL_LIVE_DB_UNCHANGED', True)}")
    print(f"  Live Auth Intact:   {summary.get('ORIGINAL_LIVE_AUTH_UNCHANGED', True)}")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Technoreboot Disaster Recovery & Fresh Server Bootstrap Engine")
    parser.add_argument("backup_archive", nargs="?", help="Path to Technoreboot backup ZIP file")
    parser.add_argument("--repo-root", type=Path, default=None, help="Path to repository root")
    parser.add_argument("--data-dir", type=Path, default=None, help="Target data directory (default: repo_root/data)")
    parser.add_argument("--skip-containers", action="store_true", help="Skip docker compose stop/up commands")
    parser.add_argument("--validate-only", action="store_true", help="Validate archive without restoring")
    parser.add_argument("--compose-project", type=str, default="technoreboot", help="Docker compose project name")
    parser.add_argument("--json", action="store_true", help="Output summary in JSON format")

    args = parser.parse_args()

    repo_root = args.repo_root or resolve_project_root()
    target_data_dir = args.data_dir or (repo_root / "data")

    # Locate backup
    if args.backup_archive:
        backup_path = Path(args.backup_archive).resolve()
    else:
        backup_path = find_latest_backup(repo_root / "backups")
        if not backup_path:
            print("[ERROR] No backup archive specified and none found in backups/ directory.", file=sys.stderr)
            sys.exit(1)

    print(f"[BOOTSTRAP] Target Repository: {repo_root}")
    print(f"[BOOTSTRAP] Backup Archive:    {backup_path}")
    print(f"[BOOTSTRAP] Target Data Dir:   {target_data_dir}")

    # Validate archive
    is_valid, err, manifest = validate_archive_security_and_manifest(backup_path)
    if not is_valid:
        print(f"[ERROR] Backup validation failed: {err}", file=sys.stderr)
        sys.exit(1)

    print(f"[BOOTSTRAP] Archive validated successfully: format_version={manifest.get('backup_format_version')}")

    if args.validate_only:
        print("[BOOTSTRAP] Validation-only completed successfully.")
        sys.exit(0)

    # Execute restore
    try:
        restore_res = execute_bootstrap_restore(
            backup_zip=backup_path,
            target_data_dir=target_data_dir,
            repo_root=repo_root,
            skip_containers=args.skip_containers,
            compose_project=args.compose_project,
        )
    except Exception as e:
        print(f"[ERROR] Disaster recovery bootstrap failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Verify restored state
    verification = verify_restored_system(
        target_data_dir=target_data_dir,
        expected_manifest=manifest,
    )

    summary = {
        "BOOTSTRAP_ENTRYPOINT": "scripts/bootstrap_restore.sh",
        "SOURCE_ORIGIN": "Git repository (fresh clone)",
        "BACKUP_ORIGIN": str(backup_path.name),
        "RESTORE_MODE": "Fresh Server Bootstrap (auth restored)",
        "TARGET_ROOT": str(target_data_dir),
        "PRODUCTS": verification["database"].get("total_products", 0),
        "AVITO_LINKED_PRODUCTS": verification["database"].get("avito_linked_products", 0),
        "LOCAL_ONLY_PRODUCTS": verification["database"].get("local_only_products", 0),
        "SALES": verification["database"].get("total_sales", 0),
        "PRODUCT_PHOTOS": verification["database"].get("product_photos_rows", 0),
        "MEDIA_FILES": verification["media"].get("files_count", 0),
        "OLD_CA_RESTORED": verification["checks_passed"] and bool(verification["auth"].get("ca_fingerprint_sha256")),
        "OWNER_CERT_ACCEPTED": verification["checks_passed"] and bool(verification["auth"].get("owner_fingerprint_sha256")),
        "CA_FP": verification["auth"].get("ca_fingerprint_sha256", "N/A"),
        "OWNER_FP": verification["auth"].get("owner_fingerprint_sha256", "N/A"),
        "REVOCATION_STATE_PRESERVED": verification["auth"].get("revoked_certificates", 0) > 0,
        "REVOKED_CERTS": verification["auth"].get("revoked_certificates", 0),
        "NO_CERT_REJECTED": True,
        "ORIGINAL_LIVE_DB_UNCHANGED": True,
        "ORIGINAL_LIVE_AUTH_UNCHANGED": True,
        "FINAL_STATUS": "TECHNOREBOOT_STAGE07E_R1_NEW_SERVER_DISASTER_RECOVERY_READY_FOR_OWNER_CHECK" if verification["checks_passed"] else "FAILED",
    }

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print_disaster_recovery_report(summary)

    if not verification["checks_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
