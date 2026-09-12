"""
Technoreboot Admin Shell — Backup and Restore Service
Stage 07B-R2: Web Backup / Restore (Owner UI only)

Provides web-oriented backup creation and restore functionality:
- Full consistent backup package creation (SQLite online backup + storage + auth + avito)
- Strict pre-validation of uploaded backup archives
- Data restoration with post-restore verification
"""

import os
import sys
import shutil
import sqlite3
import json
import zipfile
import tempfile
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from cryptography import x509
from cryptography.hazmat.primitives import hashes


def get_project_root() -> Path:
    """Resolve project root directory."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent.parent,
        Path("/"),
        Path.cwd(),
        Path(r"C:\tbootit"),
    ]
    for c in candidates:
        if (c / "docker-compose.yml").is_file() and (c / "data").is_dir():
            return c
    return script_dir.parent.parent


def get_data_dir() -> Path:
    """Resolve mutable data directory."""
    env_data = os.getenv("DATA_DIR")
    if env_data and Path(env_data).is_dir():
        return Path(env_data)
    if Path("/data/db").is_dir():
        return Path("/data")
    project_root = get_project_root()
    if (project_root / "data" / "db").is_dir():
        return project_root / "data"
    return Path("/data")


def get_auth_dir() -> Path:
    """Resolve auth storage directory."""
    env_auth = os.getenv("AUTH_STORAGE_DIR")
    if env_auth and Path(env_auth).is_dir():
        return Path(env_auth)
    if Path("/app/auth-data").is_dir():
        return Path("/app/auth-data")
    return get_data_dir() / "auth"


def get_git_commit(project_root: Path) -> str:
    """Extract current git commit hash safely."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def copy_tree_files(src_dir: Path, dst_dir: Path) -> Tuple[int, int]:
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


def inspect_auth_pki(auth_dir: Path) -> Dict[str, Any]:
    """Extract CA and OWNER fingerprints and registry stats."""
    metrics = {
        "ca_fingerprint_sha256": None,
        "owner_fingerprint_sha256": None,
        "owner_serial_hex": None,
        "total_certificates": 0,
        "revoked_certificates": 0,
    }

    try:
        ca_file = auth_dir / "ca" / "ca.crt"
        if ca_file.is_file():
            ca_cert = x509.load_pem_x509_certificate(ca_file.read_bytes())
            metrics["ca_fingerprint_sha256"] = ca_cert.fingerprint(hashes.SHA256()).hex().upper()

        owner_file = auth_dir / "certificates" / "owner.crt"
        if owner_file.is_file():
            owner_cert = x509.load_pem_x509_certificate(owner_file.read_bytes())
            metrics["owner_fingerprint_sha256"] = owner_cert.fingerprint(hashes.SHA256()).hex().upper()
            metrics["owner_serial_hex"] = hex(owner_cert.serial_number)[2:].upper()
    except Exception:
        pass

    registry_file = auth_dir / "registry.json"
    if registry_file.is_file():
        try:
            reg_data = json.loads(registry_file.read_text(encoding="utf-8"))
            if isinstance(reg_data, list):
                metrics["total_certificates"] = len(reg_data)
                metrics["revoked_certificates"] = sum(
                    1 for c in reg_data if isinstance(c, dict) and c.get("status") == "REVOKED"
                )
            elif isinstance(reg_data, dict):
                certs = reg_data.get("certificates", [])
                metrics["total_certificates"] = len(certs)
                metrics["revoked_certificates"] = sum(
                    1 for c in certs if isinstance(c, dict) and c.get("status") == "REVOKED"
                )
        except Exception:
            pass

    return metrics


def create_backup(target_file: Optional[Path] = None) -> Tuple[Path, Dict[str, Any]]:
    """
    Creates a full system backup package.
    Returns: (output_zip_path, manifest_dict)
    """
    data_dir = get_data_dir()
    project_root = get_project_root()
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    staging_dir = Path(tempfile.mkdtemp(prefix=f"tnr_backup_stage_{timestamp_str}_"))

    try:
        # 1. Database backup
        db_src = data_dir / "db" / "technoreboot.db"
        if not db_src.is_file():
            raise FileNotFoundError(f"Database file not found: {db_src}")

        dst_db = staging_dir / "database" / "technoreboot.db"
        dst_db.parent.mkdir(parents=True, exist_ok=True)

        src_conn = sqlite3.connect(f"file:{db_src}?mode=ro", uri=True)
        try:
            dst_conn = sqlite3.connect(str(dst_db))
            try:
                src_conn.backup(dst_conn, pages=100)
            finally:
                dst_conn.close()

            # Collect stats
            cur = src_conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
            tables = [r[0] for r in cur.fetchall()]
            table_stats = {}
            total_rows = 0
            for t in tables:
                try:
                    cur.execute(f'SELECT count(*) FROM "{t}"')
                    cnt = cur.fetchone()[0]
                    table_stats[t] = cnt
                    total_rows += cnt
                except Exception:
                    table_stats[t] = 0
        finally:
            src_conn.close()

        # 2. Photos & Media Storage
        storage_src = data_dir / "storage"
        storage_dst = staging_dir / "storage"
        storage_files, storage_bytes = copy_tree_files(storage_src, storage_dst)

        # 3. Auth & PKI
        auth_env = os.environ.get("AUTH_STORAGE_DIR")
        if auth_env and Path(auth_env).is_dir():
            auth_src = Path(auth_env)
        elif sys.platform != "win32" and Path("/app/auth-data").is_dir():
            auth_src = Path("/app/auth-data")
        else:
            auth_src = data_dir / "auth"
        auth_dst = staging_dir / "auth"
        auth_files, auth_bytes = copy_tree_files(auth_src, auth_dst)
        auth_metrics = inspect_auth_pki(auth_dst)

        # 4. Avito Module
        avito_src = data_dir / "avito-module"
        avito_dst = staging_dir / "avito-module"
        avito_files, avito_bytes = copy_tree_files(avito_src, avito_dst)

        # 5. Manifest
        manifest = {
            "backup_format_version": "1.0",
            "backup_type": "full",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "git_commit": get_git_commit(project_root),
            "components": ["database", "storage", "auth", "avito-module"],
            "database": {
                "sqlite_file": "database/technoreboot.db",
                "tables_count": len(tables),
                "total_rows": total_rows,
                "tables": table_stats,
            },
            "storage": {
                "files_count": storage_files,
                "total_bytes": storage_bytes,
            },
            "auth": {
                "ca_fingerprint_sha256": auth_metrics["ca_fingerprint_sha256"],
                "owner_fingerprint_sha256": auth_metrics["owner_fingerprint_sha256"],
                "owner_serial_hex": auth_metrics["owner_serial_hex"],
                "total_certificates": auth_metrics["total_certificates"],
                "revoked_certificates": auth_metrics["revoked_certificates"],
            },
            "avito": {
                "files_count": avito_files,
                "total_bytes": avito_bytes,
            },
        }

        manifest_file = staging_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        # 6. Compress into ZIP
        if not target_file:
            target_file = Path(tempfile.gettempdir()) / f"TECHNOREBOOT_BACKUP_{timestamp_str}.zip"

        target_file.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target_file, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zip_out:
            for root, dirs, files in os.walk(staging_dir):
                for f in files:
                    fp = Path(root) / f
                    arcname = fp.relative_to(staging_dir).as_posix()
                    zip_out.write(fp, arcname=arcname)

        return target_file, manifest

    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)


def validate_backup(zip_path: Path) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Validates uploaded backup archive before any destructive action.
    Returns: (is_valid, error_message, manifest_dict_or_None)
    """
    if not zip_path.is_file():
        return False, "Файл резервной копии не найден.", None

    if not zipfile.is_zipfile(zip_path):
        return False, "Загруженный файл не является допустимым ZIP-архивом.", None

    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            corrupt = z.testzip()
            if corrupt is not None:
                return False, f"Архив поврежден (ошибка в {corrupt}).", None

            namelist = set(z.namelist())
            if "manifest.json" not in namelist:
                return False, "В архиве отсутствует файл manifest.json.", None

            manifest_bytes = z.read("manifest.json")
            manifest = json.loads(manifest_bytes.decode("utf-8"))

            if manifest.get("backup_format_version") != "1.0":
                return False, f"Неподдерживаемая версия формата бэкапа: {manifest.get('backup_format_version')}", None

            components = manifest.get("components", [])
            for req in ["database", "storage", "auth"]:
                if req not in components:
                    return False, f"В манифесте отсутствует обязательный компонент: {req}.", None

            # Check critical files
            if "database/technoreboot.db" not in namelist:
                return False, "В архиве отсутствует файл базы данных database/technoreboot.db.", None

            required_auth = [
                "auth/ca/ca.crt",
                "auth/certificates/owner.crt",
                "auth/registry.json",
            ]
            for rf in required_auth:
                if rf not in namelist:
                    return False, f"В архиве отсутствует обязательный файл аутентификации: {rf}.", None

            return True, "", manifest

    except Exception as e:
        return False, f"Ошибка при чтении архива: {e}", None


def _clean_and_copy_dir(src: Path, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    for child in dst.iterdir():
        if child.is_dir():
            src_child = src / child.name
            if src_child.is_dir():
                _clean_and_copy_dir(src_child, child)
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


def restore_backup(zip_path: Path) -> Tuple[bool, str]:
    """
    Restores mutable persistent state from a verified backup archive.
    Returns: (success, message)
    """
    is_valid, err_msg, manifest = validate_backup(zip_path)
    if not is_valid:
        return False, err_msg

    data_dir = get_data_dir()
    extract_dir = Path(tempfile.mkdtemp(prefix="tnr_restore_extract_"))

    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)

        # 1. Restore Database
        src_db = extract_dir / "database" / "technoreboot.db"
        dst_db = data_dir / "db" / "technoreboot.db"
        dst_db.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_db, dst_db)

        # 2. Restore Storage
        src_storage = extract_dir / "storage"
        dst_storage = data_dir / "storage"
        if src_storage.is_dir():
            _clean_and_copy_dir(src_storage, dst_storage)

        # 3. Preserve Live Auth (Stage 07B-R3 policy)
        # Normal web restore deliberately preserves data/auth (current CA, OWNER, registry,
        # active/revoked states) to ensure the owner's active browser session and newly issued
        # user certificates are never disrupted or rolled backward.
        # The auth/ component in the zip is kept strictly for disaster recovery.

        # 4. Restore Avito
        src_avito = extract_dir / "avito-module"
        dst_avito = data_dir / "avito-module"
        if src_avito.is_dir():
            _clean_and_copy_dir(src_avito, dst_avito)

        # Post-restore verification: verify database integrity
        conn = sqlite3.connect(str(dst_db))
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM products")
        p_count = cur.fetchone()[0]
        conn.close()

        # Verify live CA & OWNER certificates are intact
        auth_check_dir = get_auth_dir()
        ca_path = auth_check_dir / "ca" / "ca.crt"
        owner_path = auth_check_dir / "certificates" / "owner.crt"
        if not ca_path.is_file() or not owner_path.is_file():
            return False, "Ошибка проверки безопасности: файлы аутентификации отсутствуют."

        ca_cert = x509.load_pem_x509_certificate(ca_path.read_bytes())
        owner_cert = x509.load_pem_x509_certificate(owner_path.read_bytes())
        if not ca_cert or not owner_cert:
            return False, "Ошибка проверки безопасности: не удалось загрузить сертификаты."

        return True, "Бизнес-данные (база данных и медиа-файлы) успешно восстановлены. Текущие сертификаты доступа сохранены."

    except Exception as e:
        return False, f"Ошибка восстановления: {e}"

    finally:
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)
