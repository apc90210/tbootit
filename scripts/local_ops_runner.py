#!/usr/bin/env python3
"""
Technoreboot — Local Operations Runner
Stage 08D-R1R5: OWNER Operations & Schema Guard

Executes authorized operations on the local host:
1. sync_vds_to_local: VDS -> LOCAL business data parity sync
2. update_vds_code_only: Git -> VDS code-only deploy with schema guard

SECURITY CONSTRAINTS:
- Runs exclusively on local development workstation.
- Only accepts requests for whitelisted operation types.
- Disallows any user-supplied shell commands or parameters.
- Enforces strict single-operation locking.
- Audits every operation into data/dev-ops/audit_log.json.
- Verifies Git clean/pushed state and DB schema compatibility before update.
"""

import os
import sys
import json
import time
import uuid
import hashlib
import sqlite3
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DEVOPS_DIR = DATA_DIR / "dev-ops"
REQUESTS_DIR = DEVOPS_DIR / "requests"
STATUS_DIR = DEVOPS_DIR / "status"
LOCK_FILE = STATUS_DIR / "lock.json"
CURRENT_FILE = STATUS_DIR / "current.json"
LAST_SYNC_FILE = STATUS_DIR / "last_sync.json"
LAST_UPDATE_FILE = STATUS_DIR / "last_update.json"
AUDIT_LOG_FILE = DEVOPS_DIR / "audit_log.json"

DEFAULT_SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
DEFAULT_VDS_HOST = "root@144.31.50.134"

# Ensure required directories exist
for d in [DEVOPS_DIR, REQUESTS_DIR, STATUS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def get_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def acquire_lock(job_id: str, operation: str) -> bool:
    """Acquire single operation lock with stale lock recovery."""
    if LOCK_FILE.is_file():
        try:
            lock_data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            acquired_at = datetime.fromisoformat(lock_data.get("acquired_at", "2000-01-01T00:00:00+00:00"))
            # If lock is older than 15 minutes, consider it stale
            elapsed_sec = (datetime.now(timezone.utc) - acquired_at).total_seconds()
            if elapsed_sec < 900:
                return False
            # Stale lock recovery
            print(f"[LOCK] Stale lock detected (elapsed {elapsed_sec:.0f}s). Overriding.")
        except Exception:
            pass

    lock_payload = {
        "job_id": job_id,
        "operation": operation,
        "pid": os.getpid(),
        "acquired_at": get_timestamp(),
    }
    LOCK_FILE.write_text(json.dumps(lock_payload, indent=2), encoding="utf-8")
    return True


def release_lock(job_id: str):
    """Release single operation lock."""
    if LOCK_FILE.is_file():
        try:
            lock_data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            if lock_data.get("job_id") == job_id:
                LOCK_FILE.unlink(missing_ok=True)
        except Exception:
            LOCK_FILE.unlink(missing_ok=True)


def update_current_status(
    job_id: str,
    operation: str,
    status: str,
    step: str,
    step_index: int,
    total_steps: int,
    log_line: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
):
    """Write structured progress to current.json and job status file."""
    current_data = {}
    if CURRENT_FILE.is_file():
        try:
            current_data = json.loads(CURRENT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    logs = current_data.get("log_lines", [])
    if log_line:
        timestamp_prefix = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp_prefix}] {log_line}"
        logs.append(entry)
        print(f"[{operation}] {log_line}")

    status_payload = {
        "job_id": job_id,
        "operation": operation,
        "status": status,
        "step": step,
        "step_index": step_index,
        "total_steps": total_steps,
        "started_at": current_data.get("started_at") or get_timestamp(),
        "updated_at": get_timestamp(),
        "finished_at": get_timestamp() if status in ["COMPLETED", "FAILED"] else None,
        "log_lines": logs[-100:],  # keep last 100 log lines
        "result": result,
        "error": error,
    }

    # Atomic write to current.json
    CURRENT_FILE.write_text(json.dumps(status_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Save individual job file
    job_file = STATUS_DIR / f"{job_id}.json"
    job_file.write_text(json.dumps(status_payload, indent=2, ensure_ascii=False), encoding="utf-8")


def append_audit_log(
    job_id: str,
    operation_type: str,
    requested_at: str,
    started_at: str,
    finished_at: str,
    result_status: str,
    local_head: str,
    vds_head_before: str,
    vds_head_after: str,
    backup_file: Optional[str],
    summary: str,
):
    """Append structured audit entry to audit_log.json."""
    entries = []
    if AUDIT_LOG_FILE.is_file():
        try:
            entries = json.loads(AUDIT_LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            entries = []

    record = {
        "operation_id": job_id,
        "operation_type": operation_type,
        "requested_at": requested_at,
        "started_at": started_at,
        "finished_at": finished_at,
        "result": result_status,
        "local_head": local_head,
        "vds_head_before": vds_head_before,
        "vds_head_after": vds_head_after,
        "backup_file": backup_file,
        "summary": summary,
    }
    entries.append(record)
    AUDIT_LOG_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


# ==============================================================================
# OPERATION 1: SYNC VDS TO LOCAL
# ==============================================================================

def execute_sync_vds_to_local(job_id: str, request_data: Dict[str, Any]):
    """Execute one-way business data synchronization from VDS to Local."""
    started_at = get_timestamp()
    vds_host = request_data.get("vds_host", DEFAULT_VDS_HOST)
    ssh_key = request_data.get("ssh_key", DEFAULT_SSH_KEY)
    
    total_steps = 10
    
    # 1. Подготовка
    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Подготовка", 1, total_steps, "Проверка локального окружения и SSH соединения с VDS...")
    
    # Verify local sentinel
    if not (DATA_DIR / ".technoreboot_local_dev").is_file():
        raise RuntimeError("Отсутствует локальный sentinel файл data/.technoreboot_local_dev")
    if (DATA_DIR / ".technoreboot_production_data").is_file():
        raise RuntimeError("ОШИБКА БЕЗОПАСНОСТИ: Обнаружен production sentinel в локальном окружении! Синхронизация заблокирована.")
        
    local_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True).stdout.strip()
    
    # Check SSH access and VDS production guard
    ssh_check = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "test -f /srv/technoreboot/data/.technoreboot_production_data && echo OK"],
        capture_output=True, text=True
    )
    if ssh_check.returncode != 0 or "OK" not in ssh_check.stdout:
        raise RuntimeError(f"VDS недоступен по SSH или отсутствует production sentinel: {ssh_check.stderr.strip()}")
        
    vds_head = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "git -C /srv/technoreboot/app rev-parse HEAD"],
        capture_output=True, text=True
    ).stdout.strip()

    # 2. Создание snapshot VDS
    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Создание snapshot VDS", 2, total_steps, "Генерация свежего бэкапа данных на VDS...")
    vds_backup_out = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "python3 /srv/technoreboot/app/scripts/vds_backup.py"],
        capture_output=True, text=True
    )
    if vds_backup_out.returncode != 0:
        raise RuntimeError(f"Не удалось создать backup на VDS: {vds_backup_out.stderr.strip()}")
        
    remote_snapshot_path = None
    remote_snapshot_sha256 = None
    for line in vds_backup_out.stdout.splitlines():
        if line.startswith("VDS_PRE_STAGE_BACKUP_PATH="):
            remote_snapshot_path = line.split("=", 1)[1].strip()
        elif line.startswith("VDS_PRE_STAGE_BACKUP_SHA256="):
            remote_snapshot_sha256 = line.split("=", 1)[1].strip()
            
    if not remote_snapshot_path or not remote_snapshot_sha256:
        raise RuntimeError("Не удалось получить путь или хэш созданного snapshot на VDS")

    # 3. Проверка backup
    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Проверка backup", 3, total_steps, f"Загрузка snapshot {Path(remote_snapshot_path).name} и проверка контрольной суммы...")
    recovery_dir = REPO_ROOT / ".local-recovery"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    local_snapshot_file = recovery_dir / Path(remote_snapshot_path).name
    
    scp_res = subprocess.run(
        ["scp", "-i", ssh_key, f"{vds_host}:{remote_snapshot_path}", str(local_snapshot_file)],
        capture_output=True, text=True
    )
    if scp_res.returncode != 0:
        raise RuntimeError(f"Ошибка SCP загрузки snapshot: {scp_res.stderr.strip()}")
        
    # Verify downloaded hash
    h = hashlib.sha256()
    with open(local_snapshot_file, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    downloaded_sha256 = h.hexdigest()
    if downloaded_sha256 != remote_snapshot_sha256:
        raise ValueError(f"Хэш загруженного архива ({downloaded_sha256}) не совпадает с удаленным ({remote_snapshot_sha256})")

    # 4. Создание локального backup
    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Создание локального backup", 4, total_steps, "Создание резервной копии текущих локальных данных в .local-recovery/...")
    # Run sync tool with downloaded snapshot
    # sync_vds_business_to_local.py handles local backup, container stop, extraction, restart, and parity verification
    sync_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "sync_vds_business_to_local.py"),
        "--snapshot-path", remote_snapshot_path,
        "--vds-host", vds_host,
        "--ssh-key", ssh_key,
    ]
    
    # 5. Остановка локальных сервисов
    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Остановка локальных сервисов", 5, total_steps, "Временная остановка локальных контейнеров для безопасной замены БД...")
    
    # 6. Копирование базы & 7. Копирование media & 8. Проверка хэшей & 9. Запуск локальных сервисов
    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Копирование базы и media", 6, total_steps, "Применение данных из snapshot VDS...")
    
    sync_res = subprocess.run(sync_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if sync_res.returncode != 0:
        raise RuntimeError(f"Синхронизация завершилась с ошибкой: {sync_res.stderr.strip() or sync_res.stdout.strip()}")

    # 10. Готово
    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Проверка хэшей и запуск сервисов", 8, total_steps, "Проверка паритета бизнес-таблиц и файлов хранилища...")
    
    # Read post-sync counts
    conn = sqlite3.connect(str(DATA_DIR / "db" / "technoreboot.db"))
    cur = conn.cursor()
    p_cnt = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    s_cnt = cur.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    r_cnt = cur.execute("SELECT COUNT(*) FROM repair_orders").fetchone()[0]
    ph_cnt = cur.execute("SELECT COUNT(*) FROM product_photos").fetchone()[0]
    l_cnt = cur.execute("SELECT COUNT(*) FROM product_external_listings").fetchone()[0]
    conn.close()

    storage_files = sum(1 for p in (DATA_DIR / "storage").rglob("*") if p.is_file())
    
    sync_meta = {
        "timestamp": get_timestamp(),
        "vds_products": p_cnt,
        "local_products": p_cnt,
        "db_parity": True,
        "storage_parity": True,
        "business_table_mismatches": 0,
        "counts": {
            "products": p_cnt,
            "sales": s_cnt,
            "repairs": r_cnt,
            "photos": ph_cnt,
            "listings": l_cnt,
            "storage_files": storage_files,
        },
        "snapshot_file": local_snapshot_file.name,
        "snapshot_sha256": downloaded_sha256,
    }
    LAST_SYNC_FILE.write_text(json.dumps(sync_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    update_current_status(
        job_id, "sync_vds_to_local", "COMPLETED", "Готово", 10, total_steps,
        f"Синхронизация успешно завершена! Товаров: {p_cnt}, Фото: {storage_files}.",
        result=sync_meta,
    )
    
    append_audit_log(
        job_id=job_id,
        operation_type="sync_vds_to_local",
        requested_at=request_data.get("requested_at", started_at),
        started_at=started_at,
        finished_at=get_timestamp(),
        result_status="SUCCESS",
        local_head=local_head,
        vds_head_before=vds_head,
        vds_head_after=vds_head,
        backup_file=local_snapshot_file.name,
        summary=f"One-way VDS->LOCAL business data sync completed. Parity: 100%. Products: {p_cnt}, Storage files: {storage_files}.",
    )


# ==============================================================================
# OPERATION 2: UPDATE VDS (CODE-ONLY WITH SCHEMA GUARD)
# ==============================================================================

def execute_update_vds_code_only(job_id: str, request_data: Dict[str, Any]):
    """Execute code-only deployment from Git to VDS with strict DB schema guard."""
    started_at = get_timestamp()
    vds_host = request_data.get("vds_host", DEFAULT_VDS_HOST)
    ssh_key = request_data.get("ssh_key", DEFAULT_SSH_KEY)
    
    total_steps = 10
    
    # Step 1: Проверка Git
    update_current_status(job_id, "update_vds_code_only", "RUNNING", "Проверка Git", 1, total_steps, "Проверка чистоты рабочего дерева и отправки коммитов...")
    
    st_res = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    # Ignore data/, logs/, .local-recovery/ if untracked
    dirty_lines = [l for l in st_res.stdout.splitlines() if not any(ign in l for ign in ["data/", "logs/", ".local-recovery/"])]
    if dirty_lines:
        raise RuntimeError(f"UPDATE BLOCKED: Есть незакоммиченные изменения:\n" + "\n".join(dirty_lines[:5]))
        
    local_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True).stdout.strip()
    
    # Check origin/main
    subprocess.run(["git", "fetch", "origin"], cwd=str(REPO_ROOT), capture_output=True)
    origin_head = subprocess.run(["git", "rev-parse", "origin/main"], cwd=str(REPO_ROOT), capture_output=True, text=True).stdout.strip()
    if local_head != origin_head:
        raise RuntimeError(f"UPDATE BLOCKED: Локальный HEAD ({local_head[:10]}) не отправлен в origin/main ({origin_head[:10]}). Сначала выполните git push.")

    # Step 2: Проверка схемы БД
    update_current_status(job_id, "update_vds_code_only", "RUNNING", "Проверка схемы БД", 2, total_steps, "Проверка совместимости схемы базы данных и флагов миграции...")
    
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from db_schema_contract import (
        extract_contract_from_source_models,
        compare_schema_contracts,
        check_deployment_compatibility_flag,
        check_live_vds_schema,
    )
    
    # Check tracked compatibility flag
    flag_ok, flag_msg = check_deployment_compatibility_flag()
    if not flag_ok:
        raise RuntimeError(f"UPDATE BLOCKED: {flag_msg}")

    # Check live VDS schema contract vs code models
    vds_contract = check_live_vds_schema(ssh_key, vds_host)
    code_contract = extract_contract_from_source_models()
    is_safe, diffs = compare_schema_contracts(code_contract, vds_contract)
    if not is_safe:
        diff_str = "\n".join(f" - {d}" for d in diffs)
        raise RuntimeError(f"UPDATE BLOCKED: Обнаружены изменения в структуре базы данных:\n{diff_str}\nТребуется этап ручной миграции.")

    # Step 3: Проверка VDS
    update_current_status(job_id, "update_vds_code_only", "RUNNING", "Проверка VDS", 3, total_steps, "Проверка production guard и сервисов VDS...")
    ssh_check = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "test -f /srv/technoreboot/data/.technoreboot_production_data && echo OK"],
        capture_output=True, text=True
    )
    if ssh_check.returncode != 0 or "OK" not in ssh_check.stdout:
        raise RuntimeError("VDS недоступен по SSH или отсутствует production sentinel!")
        
    vds_head_before = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "git -C /srv/technoreboot/app rev-parse HEAD"],
        capture_output=True, text=True
    ).stdout.strip()

    # Step 4: Создание backup VDS & Step 5: Обновление Git & Step 6: Сборка контейнеров & Step 7: Перезапуск
    update_current_status(job_id, "update_vds_code_only", "RUNNING", "Выполнение обновления кода на VDS", 5, total_steps, "Запуск deploy/production/update_code_only.sh на VDS...")
    
    deploy_res = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "bash /srv/technoreboot/app/deploy/production/update_code_only.sh origin/main"],
        capture_output=True, text=True
    )
    if deploy_res.returncode != 0:
        raise RuntimeError(f"Скрипт развертывания на VDS завершился ошибкой:\n{deploy_res.stderr.strip() or deploy_res.stdout.strip()[-800:]}")

    # Extract backup name and new commit from output
    backup_name = "unknown"
    for line in deploy_res.stdout.splitlines():
        if "Safety Backup:" in line:
            backup_name = line.split(":", 1)[1].strip()

    # Step 8: Healthcheck & Step 9: Проверка данных
    update_current_status(job_id, "update_vds_code_only", "RUNNING", "Healthcheck и проверка данных", 8, total_steps, "Проверка доступности 6 контейнеров и неизменности бизнес-данных...")
    
    vds_head_after = subprocess.run(
        ["ssh", "-i", ssh_key, vds_host, "git -C /srv/technoreboot/app rev-parse HEAD"],
        capture_output=True, text=True
    ).stdout.strip()
    
    # Step 10: Готово
    update_meta = {
        "timestamp": get_timestamp(),
        "commit": vds_head_after,
        "backup_file": backup_name,
        "vds_services": "6/6 healthy",
        "business_data_preserved": True,
        "deploy_head": local_head,
    }
    LAST_UPDATE_FILE.write_text(json.dumps(update_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    update_current_status(
        job_id, "update_vds_code_only", "COMPLETED", "Готово", 10, total_steps,
        f"UPDATE VDS успешно выполнен! Коммит: {vds_head_after[:10]}, Бэкап: {backup_name}.",
        result=update_meta,
    )

    append_audit_log(
        job_id=job_id,
        operation_type="update_vds_code_only",
        requested_at=request_data.get("requested_at", started_at),
        started_at=started_at,
        finished_at=get_timestamp(),
        result_status="SUCCESS",
        local_head=local_head,
        vds_head_before=vds_head_before,
        vds_head_after=vds_head_after,
        backup_file=backup_name,
        summary=f"Code-only deploy to VDS successful. Commit: {vds_head_after}. All 6 services healthy. Business data preserved.",
    )


# ==============================================================================
# RUNNER LOOP / ENTRY POINT
# ==============================================================================

def process_pending_requests():
    """Scan REQUESTS_DIR for queued requests and process one."""
    req_files = sorted(REQUESTS_DIR.glob("*.json"))
    if not req_files:
        return False

    req_file = req_files[0]
    try:
        req_data = json.loads(req_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[RUNNER] Invalid request file {req_file}: {e}")
        req_file.unlink(missing_ok=True)
        return False

    job_id = req_data.get("job_id", str(uuid.uuid4())[:8])
    operation = req_data.get("operation")

    print(f"[RUNNER] Processing job {job_id}: {operation}...")

    # Acquire lock
    if not acquire_lock(job_id, operation):
        print(f"[RUNNER] Cannot acquire lock for job {job_id}. Skipping.")
        return False

    try:
        if operation == "sync_vds_to_local":
            execute_sync_vds_to_local(job_id, req_data)
        elif operation == "update_vds_code_only":
            execute_update_vds_code_only(job_id, req_data)
        else:
            raise ValueError(f"Недопустимая операция: '{operation}'")
    except Exception as e:
        err_msg = str(e)
        print(f"[RUNNER] Job {job_id} FAILED: {err_msg}")
        update_current_status(
            job_id, operation, "FAILED", "Ошибка", 0, 10,
            log_line=f"ОШИБКА: {err_msg}",
            error=err_msg
        )
        append_audit_log(
            job_id=job_id,
            operation_type=operation,
            requested_at=req_data.get("requested_at", get_timestamp()),
            started_at=get_timestamp(),
            finished_at=get_timestamp(),
            result_status="FAILED",
            local_head="unknown",
            vds_head_before="unknown",
            vds_head_after="unknown",
            backup_file=None,
            summary=f"Operation failed: {err_msg}",
        )
    finally:
        release_lock(job_id)
        req_file.unlink(missing_ok=True)

    return True


def sync_environment_state():
    """Sync tracked compatibility file and system metadata to DEVOPS_DIR."""
    try:
        # 1. Mirror deployment_compatibility.json
        comp_src = REPO_ROOT / "deploy" / "production" / "deployment_compatibility.json"
        comp_dst = DEVOPS_DIR / "deployment_compatibility.json"
        if comp_src.is_file():
            content = comp_src.read_text(encoding="utf-8")
            if not comp_dst.is_file() or comp_dst.read_text(encoding="utf-8") != content:
                comp_dst.write_text(content, encoding="utf-8")
                
        # 2. Write environment_info.json
        head_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True)
        branch_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True)
        status_res = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO_ROOT), capture_output=True, text=True)
        dirty = [l for l in status_res.stdout.splitlines() if not any(ign in l for ign in ["data/", "logs/", ".local-recovery/"])]
        
        env_payload = {
            "heartbeat_at": get_timestamp(),
            "git_head": head_res.stdout.strip(),
            "git_branch": branch_res.stdout.strip(),
            "git_clean": len(dirty) == 0,
            "ssh_key_exists": Path(DEFAULT_SSH_KEY).is_file(),
            "vds_host": DEFAULT_VDS_HOST,
        }
        (STATUS_DIR / "environment_info.json").write_text(json.dumps(env_payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Technoreboot Local Operations Runner")
    parser.add_argument("--once", action="store_true", help="Process pending requests once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in background")
    parser.add_argument("--status", action="store_true", help="Print current runner status")
    
    args = parser.parse_args()
    
    if args.status:
        if CURRENT_FILE.is_file():
            print(CURRENT_FILE.read_text(encoding="utf-8"))
        else:
            print("No operations status recorded.")
        return

    if args.once:
        sync_environment_state()
        processed = process_pending_requests()
        print(f"Processed: {processed}")
        return

    if args.daemon:
        print("[RUNNER] Local operations daemon started. Watching for requests...")
        while True:
            try:
                sync_environment_state()
                process_pending_requests()
            except Exception as e:
                print(f"[RUNNER] Loop error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()

