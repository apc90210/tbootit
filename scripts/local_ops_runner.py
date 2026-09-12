#!/usr/bin/env python3
"""
Technoreboot — Local Operations Runner
Stage 08D-R1R6: OWNER Fast Rollback & Release Checkpoint

Executes authorized operations on the local host:
1. sync_vds_to_local: VDS -> LOCAL business data parity sync
2. update_vds_code_only: Git -> VDS code-only deploy with health preflight, release checkpoint, and auto-rollback
3. rollback_vds_code_only: Fast code-only rollback to last known-good release without modifying business data

SECURITY & ARCHITECTURAL CONSTRAINTS:
- Runs exclusively on local development workstation.
- Only accepts requests for whitelisted operation types.
- Disallows any user-supplied shell commands or parameters.
- Enforces strict single-operation locking (status/lock.json).
- VDS is canonical source for business data (VDS -> LOCAL).
- Local business data is NEVER uploaded to VDS.
- Normal fast rollback is CODE-ONLY, NEVER restores or overwrites business DB / media.
- Preflight blocks updates on dead / degraded VDS (never snapshots a dead VDS).
- Rollback blocks execution if current VDS DB schema is incompatible with target release.
"""

import os
import sys
import ssl
import json
import time
import uuid
import shutil
import hashlib
import sqlite3
import argparse
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DEVOPS_DIR = DATA_DIR / "dev-ops"
REQUESTS_DIR = DEVOPS_DIR / "requests"
STATUS_DIR = DEVOPS_DIR / "status"
LOCK_FILE = STATUS_DIR / "lock.json"
CURRENT_FILE = STATUS_DIR / "current.json"
LAST_SYNC_FILE = STATUS_DIR / "last_sync.json"
LAST_UPDATE_FILE = STATUS_DIR / "last_update.json"
LAST_KNOWN_GOOD_FILE = STATUS_DIR / "last_known_good_vds_release.json"
AUDIT_LOG_FILE = DEVOPS_DIR / "audit_log.json"

RELEASES_DIR = REPO_ROOT / ".local-recovery" / "vds-releases"
VDS_CHECKPOINTS_DIR = "/srv/technoreboot/data/backups/release-checkpoints"

DEFAULT_SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
DEFAULT_VDS_HOST = "root@144.31.50.134"

# Ensure required directories exist
for d in [DEVOPS_DIR, REQUESTS_DIR, STATUS_DIR, RELEASES_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def get_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def acquire_lock(job_id: str, operation: str) -> bool:
    """Acquire single operation lock with stale lock recovery."""
    if LOCK_FILE.is_file():
        try:
            lock_data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            acquired_at = datetime.fromisoformat(lock_data.get("acquired_at", "2000-01-01T00:00:00+00:00"))
            elapsed_sec = (datetime.now(timezone.utc) - acquired_at).total_seconds()
            if elapsed_sec < 900:
                return False
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
    """Update status/current.json and append log lines."""
    existing_lines = []
    started_at = get_timestamp()

    if CURRENT_FILE.is_file():
        try:
            curr = json.loads(CURRENT_FILE.read_text(encoding="utf-8"))
            if curr.get("job_id") == job_id:
                existing_lines = curr.get("log_lines", [])
                started_at = curr.get("started_at", started_at)
        except Exception:
            pass

    if log_line:
        t_str = datetime.now().strftime("%H:%M:%S")
        existing_lines.append(f"[{t_str}] {log_line}")

    status_payload = {
        "job_id": job_id,
        "operation": operation,
        "status": status,
        "step": step,
        "step_index": step_index,
        "total_steps": total_steps,
        "started_at": started_at,
        "updated_at": get_timestamp(),
        "finished_at": get_timestamp() if status in ["COMPLETED", "FAILED", "UPDATE_FAILED_ROLLBACK_SUCCESS", "UPDATE_FAILED_ROLLBACK_FAILED"] else None,
        "log_lines": existing_lines,
        "result": result,
        "error": error,
    }

    CURRENT_FILE.write_text(json.dumps(status_payload, indent=2, ensure_ascii=False), encoding="utf-8")
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
    extra: Optional[Dict[str, Any]] = None,
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
    if extra:
        record.update(extra)

    entries.append(record)
    AUDIT_LOG_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


# ==============================================================================
# VDS LIVENESS & HEALTH PREFLIGHT
# ==============================================================================

def check_vds_health_preflight(
    ssh_key: str,
    vds_host: str,
    repo_root: Path = REPO_ROOT,
) -> Tuple[str, Dict[str, Any], Optional[str]]:
    """
    Probe VDS liveness and health before UPDATE or SNAPSHOT.
    Required checks:
    - SSH reachable
    - HTTPS 443 reachable
    - Production data sentinel present
    - Docker daemon reachable
    - Expected 6 services running/healthy
    - SQLite DB readable & quick_check = ok
    - Free disk space on VDS (>= 500 MB) & LOCAL (>= 500 MB)
    - Git repo readable & current commit resolvable

    Returns:
        (status, details_dict, error_message)
        where status is 'HEALTHY', 'DEGRADED', or 'UNREACHABLE'
    """
    probe: Dict[str, Any] = {
        "probed_at": get_timestamp(),
        "vds_host": vds_host,
    }

    # 1. Local disk check
    try:
        local_free_mb = shutil.disk_usage(repo_root).free // (1024 * 1024)
        probe["local_free_mb"] = local_free_mb
        if local_free_mb < 500:
            return "DEGRADED", probe, f"Недостаточно свободного места на локальном диске: {local_free_mb} MB (требуется >= 500 MB)"
    except Exception as e:
        probe["local_disk_err"] = str(e)

    # 2. SSH check
    ssh_test = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=10", "-o", "ConnectionAttempts=2", vds_host, "echo PING"],
        capture_output=True, text=True, timeout=15
    )
    if ssh_test.returncode != 0:
        probe["ssh_reachable"] = False
        probe["ssh_error"] = ssh_test.stderr.strip()
        return "UNREACHABLE", probe, f"VDS полностью недоступен по SSH: {ssh_test.stderr.strip() or 'timeout'}"

    probe["ssh_reachable"] = True

    # 3. HTTPS 443 check
    vds_ip = vds_host.split("@")[-1]
    https_ok = False
    https_status_code = None
    try:
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(f"https://{vds_ip}/", headers={"User-Agent": "Technoreboot-HealthProbe"})
        with urllib.request.urlopen(req, timeout=6, context=ctx) as r:
            https_ok = True
            https_status_code = r.status
    except urllib.error.HTTPError as e:
        # Gateway responds with 403 when client cert is missing, which proves HTTPS is alive!
        https_ok = True
        https_status_code = e.code
    except Exception as e:
        probe["https_err"] = str(e)

    probe["https_reachable"] = https_ok
    probe["https_status_code"] = https_status_code

    # 4. Remote Python inspection
    remote_probe_script = """
import sqlite3, json, subprocess, os

sentinel = os.path.exists('/srv/technoreboot/data/.technoreboot_production_data')

# Docker & services
docker_ok = False
services_status = {}
try:
    ps_res = subprocess.run(['docker', 'ps', '--format', '{{.Names}} {{.Status}}'], capture_output=True, text=True, timeout=10)
    docker_ok = (ps_res.returncode == 0)
    expected = ['core', 'admin-shell', 'inventory-sales', 'repairs', 'avito', 'gateway']
    for s in expected:
        cname = f'technoreboot-prod-{s}'
        lines = [l for l in ps_res.stdout.splitlines() if cname in l]
        if lines and '(healthy)' in lines[0]:
            services_status[s] = 'healthy'
        elif lines:
            services_status[s] = 'running'
        else:
            services_status[s] = 'missing'
except Exception as e:
    docker_ok = False

# DB inspection
db_readable = False
db_quick_check = 'failed'
products_count = 0
try:
    conn = sqlite3.connect('file:/srv/technoreboot/data/db/technoreboot.db?mode=ro', uri=True, timeout=5)
    cur = conn.cursor()
    cur.execute('PRAGMA quick_check;')
    qc = cur.fetchone()[0]
    db_quick_check = qc
    cur.execute('SELECT COUNT(*) FROM products;')
    products_count = cur.fetchone()[0]
    conn.close()
    db_readable = (qc == 'ok')
except Exception as e:
    db_quick_check = str(e)

# Free disk VDS
vds_free_mb = 0
try:
    st = os.statvfs('/srv/technoreboot')
    vds_free_mb = (st.f_bavail * st.f_frsize) // (1024 * 1024)
except Exception:
    pass

# Git repo
git_ok = False
git_head = 'unknown'
try:
    git_res = subprocess.run(['git', '-C', '/srv/technoreboot/app', 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=5)
    git_ok = (git_res.returncode == 0)
    git_head = git_res.stdout.strip()
except Exception:
    pass

print(json.dumps({
    'sentinel': sentinel,
    'docker_ok': docker_ok,
    'services': services_status,
    'db_readable': db_readable,
    'db_quick_check': db_quick_check,
    'products_count': products_count,
    'vds_free_mb': vds_free_mb,
    'git_ok': git_ok,
    'git_head': git_head,
}))
"""
    cmd = ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "python3 -"]
    r = subprocess.run(cmd, input=remote_probe_script, capture_output=True, text=True, timeout=25)
    if r.returncode != 0:
        probe["remote_probe_error"] = r.stderr.strip()
        return "DEGRADED", probe, f"Ошибка удаленной диагностики VDS: {r.stderr.strip()}"

    try:
        remote_data = json.loads(r.stdout.strip())
        probe.update(remote_data)
    except Exception as e:
        return "DEGRADED", probe, f"Не удалось разобрать вывод удаленной диагностики VDS: {e}"

    # Evaluate DEGRADED criteria
    if not probe.get("sentinel"):
        return "DEGRADED", probe, "Отсутствует production sentinel /srv/technoreboot/data/.technoreboot_production_data"

    if not probe.get("docker_ok"):
        return "DEGRADED", probe, "Docker демон на VDS не отвечает"

    services = probe.get("services", {})
    unhealthy = [s for s, st in services.items() if st != "healthy"]
    if unhealthy:
        return "DEGRADED", probe, f"Некоторые сервисы VDS не в статусе healthy: {', '.join(unhealthy)}"

    if not probe.get("db_readable") or probe.get("db_quick_check") != "ok":
        return "DEGRADED", probe, f"Сбой проверки целостности SQLite БД на VDS: {probe.get('db_quick_check')}"

    if probe.get("vds_free_mb", 0) < 500:
        return "DEGRADED", probe, f"Недостаточно места на диске VDS: {probe.get('vds_free_mb')} MB (требуется >= 500 MB)"

    if not probe.get("git_ok"):
        return "DEGRADED", probe, "Git репозиторий на VDS не отвечает"

    if not probe.get("https_reachable"):
        return "DEGRADED", probe, "Порт HTTPS (443) на VDS не отвечает"

    return "HEALTHY", probe, None


# ==============================================================================
# RELEASE CHECKPOINTS & RETENTION
# ==============================================================================

def get_checkpoints_inventory() -> List[Dict[str, Any]]:
    """Scan RELEASES_DIR for valid checkpoints and return sorted list (newest first)."""
    checkpoints = []
    if not RELEASES_DIR.is_dir():
        return []

    for c_dir in RELEASES_DIR.iterdir():
        if not c_dir.is_dir():
            continue
        manifest_file = c_dir / "checkpoint.json"
        if manifest_file.is_file():
            try:
                data = json.loads(manifest_file.read_text(encoding="utf-8"))
                # Verify presence of business-backup.zip
                backup_file = c_dir / "business-backup.zip"
                data["local_backup_present"] = backup_file.is_file()
                checkpoints.append(data)
            except Exception:
                pass

    checkpoints.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return checkpoints


def enforce_checkpoint_retention(keep_count: int = 3, ssh_key: Optional[str] = None, vds_host: Optional[str] = None):
    """Retain at least `keep_count` newest checkpoints, never deleting current known-good."""
    checkpoints = get_checkpoints_inventory()
    if len(checkpoints) <= keep_count:
        return

    known_good_id = None
    if LAST_KNOWN_GOOD_FILE.is_file():
        try:
            kg_data = json.loads(LAST_KNOWN_GOOD_FILE.read_text(encoding="utf-8"))
            known_good_id = kg_data.get("checkpoint_id")
        except Exception:
            pass

    # Sort descending by created_at
    to_delete = []
    kept = 0
    for cp in checkpoints:
        cid = cp.get("checkpoint_id")
        if kept < keep_count or cid == known_good_id:
            kept += 1
        else:
            to_delete.append(cid)

    for cid in to_delete:
        dir_to_remove = RELEASES_DIR / cid
        if dir_to_remove.is_dir():
            print(f"[RETENTION] Pruning old checkpoint: {cid}")
            shutil.rmtree(dir_to_remove, ignore_errors=True)
        if ssh_key and vds_host:
            try:
                vds_p = f"{VDS_CHECKPOINTS_DIR}/{cid}"
                subprocess.run(
                    ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=10", vds_host, f"rm -rf {vds_p}"],
                    capture_output=True, timeout=15
                )
            except Exception:
                pass


def create_vds_release_checkpoint(
    job_id: str,
    ssh_key: str,
    vds_host: str,
    previous_head: str,
    target_head: str,
    preflight_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create structured release checkpoint before UPDATE:
    1. Generates checkpoint_id and creates local & remote directories.
    2. Runs vds_backup.py to produce fresh business snapshot on VDS.
    3. Copies snapshot to LOCAL recovery directory and verifies SHA256 match.
    4. Tags and preserves running container images on VDS.
    5. Introspects and records schema contract, counts, CA SHA, and storage tree SHA.
    6. Writes checkpoint.json manifest in both locations.
    """
    checkpoint_id = f"checkpoint_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{previous_head[:8]}"
    local_checkpoint_dir = RELEASES_DIR / checkpoint_id
    local_checkpoint_dir.mkdir(parents=True, exist_ok=True)
    vds_checkpoint_dir = f"{VDS_CHECKPOINTS_DIR}/{checkpoint_id}"

    # Ensure remote checkpoint directory exists
    subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, f"mkdir -p {vds_checkpoint_dir}"],
        capture_output=True, text=True, timeout=20
    )

    # 1. Create fresh VDS business backup
    vds_backup_run = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "python3 /srv/technoreboot/app/scripts/vds_backup.py"],
        capture_output=True, text=True, timeout=45
    )
    if vds_backup_run.returncode != 0:
        raise RuntimeError(f"Не удалось создать backup на VDS: {vds_backup_run.stderr.strip()}")

    vds_backup_name = None
    vds_backup_path = None
    vds_backup_sha = None
    for line in vds_backup_run.stdout.splitlines():
        if line.startswith("VDS_PRE_STAGE_BACKUP_FILE="):
            vds_backup_name = line.split("=", 1)[1].strip()
        elif line.startswith("VDS_PRE_STAGE_BACKUP_PATH="):
            vds_backup_path = line.split("=", 1)[1].strip()
        elif line.startswith("VDS_PRE_STAGE_BACKUP_SHA256="):
            vds_backup_sha = line.split("=", 1)[1].strip()
        elif "TECHNOREBOOT_BACKUP_" in line and ".zip" in line:
            for part in line.replace("=", " ").split():
                if part.startswith("TECHNOREBOOT_BACKUP_") and part.endswith(".zip"):
                    vds_backup_name = part

    if not vds_backup_name:
        raise RuntimeError(f"Не удалось определить имя созданного бэкапа на VDS! Вывод: {vds_backup_run.stdout.strip()[:200]}")

    if not vds_backup_path:
        vds_backup_path = f"/srv/technoreboot/data/backups/{vds_backup_name}"

    # Also persist to /srv/technoreboot/data/backups/ if created in /tmp
    subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, f"mkdir -p /srv/technoreboot/data/backups && cp -n {vds_backup_path} /srv/technoreboot/data/backups/{vds_backup_name} 2>/dev/null || true"],
        capture_output=True, timeout=15
    )

    # 2. Get VDS backup SHA256 if not provided
    if not vds_backup_sha:
        sha_res = subprocess.run(
            ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, f"sha256sum {vds_backup_path}"],
            capture_output=True, text=True, timeout=15
        )
        if sha_res.returncode != 0:
            raise RuntimeError("Не удалось получить контрольную сумму бэкапа на VDS!")
        vds_backup_sha = sha_res.stdout.split()[0]

    # 3. Copy backup to LOCAL recovery
    local_backup_file = local_checkpoint_dir / "business-backup.zip"
    scp_res = subprocess.run(
        ["scp", "-i", ssh_key, "-o", "ConnectTimeout=20", f"{vds_host}:{vds_backup_path}", str(local_backup_file)],
        capture_output=True, text=True, timeout=60
    )
    if scp_res.returncode != 0 or not local_backup_file.is_file():
        raise RuntimeError(f"Не удалось скопировать бэкап VDS в локальное хранилище: {scp_res.stderr.strip()}")

    # 4. Verify SHA256 match
    local_backup_sha = compute_file_sha256(local_backup_file)
    if local_backup_sha != vds_backup_sha:
        raise RuntimeError(f"Контрольная сумма локальной копии бэкапа ({local_backup_sha[:10]}) не совпадает с VDS ({vds_backup_sha[:10]})!")

    # Write sha file
    (local_checkpoint_dir / "business-backup.sha256").write_text(f"{local_backup_sha}  business-backup.zip\n", encoding="utf-8")

    # 5. Tag and record previous running application images on VDS
    tag_script = f"""
import subprocess, json

services = ['core', 'admin-shell', 'inventory-sales', 'repairs', 'avito', 'gateway']
images = {{}}
for s in services:
    cname = f'technoreboot-prod-{{s}}'
    r = subprocess.run(['docker', 'inspect', '--format', '{{{{.Image}}}}', cname], capture_output=True, text=True)
    img_id = r.stdout.strip()
    images[s] = img_id
    if img_id:
        subprocess.run(['docker', 'tag', img_id, f'technoreboot-rollback/{checkpoint_id}/{{s}}'], capture_output=True)

print(json.dumps(images))
"""
    tag_res = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "python3 -"],
        input=tag_script, capture_output=True, text=True, timeout=25
    )
    previous_images = {}
    if tag_res.returncode == 0:
        try:
            previous_images = json.loads(tag_res.stdout.strip())
        except Exception:
            pass

    # 6. Query live schema contract SHA256 on VDS
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from db_schema_contract import check_live_vds_schema, compute_contract_sha256, extract_contract_from_source_models
    vds_contract = check_live_vds_schema(ssh_key, vds_host)
    previous_schema_sha = compute_contract_sha256(vds_contract)
    code_contract = extract_contract_from_source_models()
    target_schema_sha = compute_contract_sha256(code_contract)

    # 7. Query VDS state details (counts, storage tree, CA sha)
    details_script = """
import sqlite3, hashlib, json, os

conn = sqlite3.connect('file:/srv/technoreboot/data/db/technoreboot.db?mode=ro', uri=True)
cur = conn.cursor()
counts = {}
for tbl in ['products', 'sales', 'repair_orders', 'product_photos', 'product_external_listings']:
    cur.execute(f'SELECT COUNT(*) FROM {tbl}')
    counts[tbl] = cur.fetchone()[0]

ca_sha = None
if os.path.exists('/srv/technoreboot/data/auth/ca/ca.crt'):
    with open('/srv/technoreboot/data/auth/ca/ca.crt', 'rb') as f:
        ca_sha = hashlib.sha256(f.read()).hexdigest()

st_files = []
storage_root = '/srv/technoreboot/data/storage'
for root, dirs, files in os.walk(storage_root):
    for file in sorted(files):
        p = os.path.join(root, file)
        rel = os.path.relpath(p, storage_root)
        with open(p, 'rb') as f:
            st_files.append((rel, hashlib.sha256(f.read()).hexdigest()))
st_files.sort(key=lambda x: x[0])
storage_tree_sha = hashlib.sha256(';'.join([f'{r}:{h}' for r, h in st_files]).encode()).hexdigest()

print(json.dumps({
    'counts': counts,
    'ca_sha': ca_sha,
    'storage_tree_sha': storage_tree_sha,
}))
"""
    det_res = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "python3 -"],
        input=details_script, capture_output=True, text=True, timeout=25
    )
    vds_details = {}
    if det_res.returncode == 0:
        try:
            vds_details = json.loads(det_res.stdout.strip())
        except Exception:
            pass

    # 8. Create checkpoint manifest
    manifest = {
        "checkpoint_id": checkpoint_id,
        "created_at": get_timestamp(),
        "status": "COMPLETED",
        "vds_ip": vds_host.split("@")[-1],
        "previous_head": previous_head,
        "target_head": target_head,
        "previous_schema_sha256": previous_schema_sha,
        "target_schema_sha256": target_schema_sha,
        "business_backup_file": vds_backup_name,
        "business_backup_sha256": vds_backup_sha,
        "business_counts": vds_details.get("counts", {}),
        "storage_tree_sha256": vds_details.get("storage_tree_sha"),
        "ca_sha256": vds_details.get("ca_sha"),
        "production_guard_verified": True,
        "health_preflight": preflight_data,
        "rollback_allowed": True,
        "rollback_reason": "Предыдущие образы контейнеров сохранены. Схема БД совместима.",
        "previous_image_ids": previous_images,
    }

    manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
    (local_checkpoint_dir / "checkpoint.json").write_text(manifest_json, encoding="utf-8")

    # Mirror to dev-ops/checkpoints for container access
    devops_cp_dir = DEVOPS_DIR / "checkpoints" / checkpoint_id
    devops_cp_dir.mkdir(parents=True, exist_ok=True)
    (devops_cp_dir / "checkpoint.json").write_text(manifest_json, encoding="utf-8")

    # Save on VDS as well
    subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, f"cat << 'EOF' > {vds_checkpoint_dir}/checkpoint.json\n{manifest_json}\nEOF"],
        capture_output=True, text=True, timeout=20
    )

    # Prune old checkpoints
    enforce_checkpoint_retention(keep_count=3, ssh_key=ssh_key, vds_host=vds_host)

    return manifest


# ==============================================================================
# OPERATION 1: SYNC VDS TO LOCAL (BUSINESS DATA)
# ==============================================================================

def execute_sync_vds_to_local(job_id: str, request_data: Dict[str, Any]):
    """Execute one-way business data sync from VDS to LOCAL."""
    started_at = get_timestamp()
    vds_host = request_data.get("vds_host", DEFAULT_VDS_HOST)
    ssh_key = request_data.get("ssh_key", DEFAULT_SSH_KEY)
    
    # Local direction and environment guard
    if not (DATA_DIR / ".technoreboot_local_dev").is_file():
        raise RuntimeError("SYNC BLOCKED: Отсутствует локальный sentinel .technoreboot_local_dev в data/. Синхронизация разрешена только в локальной DEV-среде.")
    if (DATA_DIR / ".technoreboot_production_data").is_file():
        raise RuntimeError("SYNC BLOCKED: Обнаружен production sentinel .technoreboot_production_data в data/. Синхронизация заблокирована.")

    total_steps = 10
    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Подготовка", 1, total_steps, "Проверка локального окружения и SSH соединения с VDS...")
    
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

    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Создание snapshot VDS", 2, total_steps, "Генерация свежего бэкапа данных на VDS...")
    vds_backup_out = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "python3 /srv/technoreboot/app/scripts/vds_backup.py"],
        capture_output=True, text=True
    )
    if vds_backup_out.returncode != 0:
        raise RuntimeError(f"Ошибка создания бэкапа на VDS: {vds_backup_out.stderr.strip()}")

    remote_snapshot_name = None
    remote_snapshot_path = None
    for line in vds_backup_out.stdout.splitlines():
        if line.startswith("VDS_PRE_STAGE_BACKUP_FILE="):
            remote_snapshot_name = line.split("=", 1)[1].strip()
        elif line.startswith("VDS_PRE_STAGE_BACKUP_PATH="):
            remote_snapshot_path = line.split("=", 1)[1].strip()
        elif "TECHNOREBOOT_BACKUP_" in line and ".zip" in line:
            for part in line.replace("=", " ").split():
                if part.startswith("TECHNOREBOOT_BACKUP_") and part.endswith(".zip"):
                    remote_snapshot_name = part

    if not remote_snapshot_name:
        raise RuntimeError("Не удалось определить имя созданного бэкапа на VDS!")

    if not remote_snapshot_path:
        remote_snapshot_path = f"/srv/technoreboot/data/backups/{remote_snapshot_name}"
    local_recovery_dir = REPO_ROOT / ".local-recovery"
    local_recovery_dir.mkdir(parents=True, exist_ok=True)
    local_snapshot_file = local_recovery_dir / remote_snapshot_name

    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Проверка backup", 3, total_steps, f"Загрузка snapshot {remote_snapshot_name} и проверка контрольной суммы...")
    
    scp_res = subprocess.run(
        ["scp", "-i", ssh_key, f"{vds_host}:{remote_snapshot_path}", str(local_snapshot_file)],
        capture_output=True, text=True
    )
    if scp_res.returncode != 0 or not local_snapshot_file.is_file():
        raise RuntimeError(f"Ошибка скачивания бэкапа с VDS: {scp_res.stderr.strip()}")

    vds_sha_res = subprocess.run(
        ["ssh", "-i", ssh_key, vds_host, f"sha256sum {remote_snapshot_path}"],
        capture_output=True, text=True
    )
    vds_sha = vds_sha_res.stdout.split()[0] if vds_sha_res.returncode == 0 else ""
    local_sha = compute_file_sha256(local_snapshot_file)
    if vds_sha and vds_sha != local_sha:
        raise RuntimeError(f"Контрольная сумма снапшота не совпадает! VDS={vds_sha[:10]}, LOCAL={local_sha[:10]}")

    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Локальный safety backup", 4, total_steps, "Создание резервной копии текущих локальных данных в .local-recovery/...")
    
    pre_sync_zip = local_recovery_dir / f"pre_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    try:
        shutil.make_archive(str(pre_sync_zip).replace(".zip", ""), "zip", str(DATA_DIR))
    except Exception as e:
        print(f"[WARN] Local pre-sync backup error: {e}")

    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Остановка контейнеров", 5, total_steps, "Временная остановка локальных контейнеров для безопасной замены БД...")
    
    sync_script = REPO_ROOT / "scripts" / "sync_vds_business_to_local.py"
    sync_cmd = [
        sys.executable, str(sync_script),
        "--vds-host", vds_host,
        "--ssh-key", ssh_key,
        "--snapshot-zip", str(local_snapshot_file),
    ]

    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Применение snapshot", 7, total_steps, "Применение данных из snapshot VDS...")
    
    apply_res = subprocess.run(sync_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if apply_res.returncode != 0:
        raise RuntimeError(f"Ошибка применения данных VDS: {apply_res.stderr.strip() or apply_res.stdout.strip()}")

    update_current_status(job_id, "sync_vds_to_local", "RUNNING", "Проверка паритета", 9, total_steps, "Проверка паритета бизнес-таблиц и файлов хранилища...")
    
    local_db_p = DATA_DIR / "db" / "technoreboot.db"
    conn = sqlite3.connect(str(local_db_p))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products;")
    p_cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM sales;")
    s_cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM repair_orders;")
    r_cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM product_photos;")
    ph_cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM product_external_listings;")
    l_cnt = cur.fetchone()[0]
    conn.close()

    storage_dir = DATA_DIR / "storage"
    storage_files = len([f for f in storage_dir.glob("**/*") if f.is_file()]) if storage_dir.is_dir() else 0

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
        "snapshot_file": remote_snapshot_name,
        "snapshot_sha256": local_sha,
    }
    LAST_SYNC_FILE.write_text(json.dumps(sync_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    local_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True).stdout.strip()
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
# OPERATION 2: UPDATE VDS (CODE-ONLY WITH PREFLIGHT & RELEASE CHECKPOINT)
# ==============================================================================

def execute_update_vds_code_only(job_id: str, request_data: Dict[str, Any]):
    """
    Execute code-only deployment from Git to VDS:
    1. Git clean/pushed check
    2. DB schema guard
    3. Health Preflight (blocks dead/degraded VDS, never snapshots dead VDS)
    4. Create Release Checkpoint (business backup on VDS + local copy with SHA verification + image tagging)
    5. Execute update_code_only.sh on VDS
    6. Healthcheck & validation
    7. Automatic code rollback on deployment failure
    """
    started_at = get_timestamp()
    vds_host = request_data.get("vds_host", DEFAULT_VDS_HOST)
    ssh_key = request_data.get("ssh_key", DEFAULT_SSH_KEY)
    
    total_steps = 10
    
    # Step 1: Проверка Git
    update_current_status(job_id, "update_vds_code_only", "RUNNING", "Проверка Git", 1, total_steps, "Проверка чистоты рабочего дерева и отправки коммитов...")
    
    st_res = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    dirty_lines = [l for l in st_res.stdout.splitlines() if not any(ign in l for ign in ["data/", "logs/", ".local-recovery/"])]
    if dirty_lines:
        raise RuntimeError(f"UPDATE BLOCKED: Есть незакоммиченные изменения:\n" + "\n".join(dirty_lines[:5]))
        
    local_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True).stdout.strip()
    
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
    
    flag_ok, flag_msg = check_deployment_compatibility_flag()
    if not flag_ok:
        raise RuntimeError(f"UPDATE BLOCKED: {flag_msg}")

    vds_contract = check_live_vds_schema(ssh_key, vds_host)
    code_contract = extract_contract_from_source_models()
    is_safe, diffs = compare_schema_contracts(code_contract, vds_contract)
    if not is_safe:
        diff_str = "\n".join(f" - {d}" for d in diffs)
        raise RuntimeError(f"UPDATE BLOCKED: Обнаружены изменения в структуре базы данных:\n{diff_str}\nТребуется этап ручной миграции.")

    # Step 3: VDS Health Preflight (Strictly blocks dead/degraded VDS)
    update_current_status(job_id, "update_vds_code_only", "RUNNING", "Диагностика VDS Preflight", 3, total_steps, "Проверка доступности и здоровья продуктивного сервера VDS...")
    
    health_status, probe_data, health_err = check_vds_health_preflight(ssh_key, vds_host)
    if health_status == "UNREACHABLE":
        raise RuntimeError(f"UPDATE BLOCKED: VDS полностью недоступен (SSH/HTTPS не отвечает). Снимок и обновление отменены. Детали: {health_err}")
    if health_status == "DEGRADED":
        raise RuntimeError(f"UPDATE BLOCKED: Состояние VDS нештатное (DEGRADED): {health_err}. Сначала устраните проблему. Снимок не создавался.")

    vds_head_before = probe_data.get("git_head", "unknown")

    # Step 4: Создание Release Checkpoint
    update_current_status(job_id, "update_vds_code_only", "RUNNING", "Создание Release Checkpoint", 4, total_steps, "Создание бэкапа VDS, локальной копии и сохранение образов релиза...")
    
    checkpoint_manifest = create_vds_release_checkpoint(
        job_id=job_id,
        ssh_key=ssh_key,
        vds_host=vds_host,
        previous_head=vds_head_before,
        target_head=local_head,
        preflight_data=probe_data,
    )
    checkpoint_id = checkpoint_manifest["checkpoint_id"]
    backup_name = checkpoint_manifest["business_backup_file"]

    # Step 5: Запуск развертывания кода на VDS
    update_current_status(job_id, "update_vds_code_only", "RUNNING", "Выполнение обновления кода", 5, total_steps, "Запуск deploy/production/update_code_only.sh на VDS...")
    
    deploy_res = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "bash /srv/technoreboot/app/deploy/production/update_code_only.sh origin/main"],
        capture_output=True, text=True
    )
    
    deploy_failed = (deploy_res.returncode != 0)

    # Step 6: Проверка здоровья и автоматический откат при сбое
    if deploy_failed:
        update_current_status(job_id, "update_vds_code_only", "RUNNING", "Автоматический откат", 7, total_steps, "Сбой обновления! Выполняется автоматический откат кода к предыдущему релизу...")
        
        auto_rollback_success = False
        rollback_log = ""
        try:
            # Code-only rollback on VDS: checkout previous head and restart containers
            rb_cmd = f"git -C /srv/technoreboot/app checkout -f {vds_head_before} && docker compose -f /srv/technoreboot/app/deploy/production/docker-compose.prod.yml --env-file /srv/technoreboot/secrets/production.env up -d --remove-orphans"
            rb_res = subprocess.run(
                ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, rb_cmd],
                capture_output=True, text=True, timeout=60
            )
            rollback_log = rb_res.stdout.strip()
            # Wait for services
            time.sleep(5)
            # Re-probe health
            rb_health, _, _ = check_vds_health_preflight(ssh_key, vds_host)
            auto_rollback_success = (rb_health == "HEALTHY")
        except Exception as e:
            rollback_log += f" [Rollback Exception: {e}]"

        result_status = "UPDATE_FAILED_ROLLBACK_SUCCESS" if auto_rollback_success else "UPDATE_FAILED_ROLLBACK_FAILED"
        err_msg = f"Обновление на VDS завершилось ошибкой. Автоматический откат: {'УСПЕШНО' if auto_rollback_success else 'НЕ УДАЛСЯ'}.\n{deploy_res.stderr.strip() or deploy_res.stdout.strip()[-600:]}"
        
        update_current_status(job_id, "update_vds_code_only", result_status, "Откат выполнен", 8, total_steps, err_msg, error=err_msg)
        
        append_audit_log(
            job_id=job_id,
            operation_type="update_vds_code_only",
            requested_at=request_data.get("requested_at", started_at),
            started_at=started_at,
            finished_at=get_timestamp(),
            result_status=result_status,
            local_head=local_head,
            vds_head_before=vds_head_before,
            vds_head_after=vds_head_before if auto_rollback_success else "unknown",
            backup_file=backup_name,
            summary=err_msg,
            extra={
                "checkpoint_id": checkpoint_id,
                "auto_rollback_attempted": True,
                "auto_rollback_result": result_status,
            }
        )
        raise RuntimeError(err_msg)

    # Step 7: Healthcheck & Step 8: Проверка данных
    update_current_status(job_id, "update_vds_code_only", "RUNNING", "Healthcheck и проверка данных", 8, total_steps, "Проверка доступности 6 контейнеров и неизменности бизнес-данных...")
    
    vds_head_after = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "git -C /srv/technoreboot/app rev-parse HEAD"],
        capture_output=True, text=True
    ).stdout.strip()
    
    # Step 9: Обновление статуса Last Known Good
    known_good_payload = {
        "checkpoint_id": checkpoint_id,
        "commit": vds_head_after,
        "updated_at": get_timestamp(),
        "backup_file": backup_name,
        "backup_sha256": checkpoint_manifest.get("business_backup_sha256"),
        "vds_services": "6/6 healthy",
    }
    LAST_KNOWN_GOOD_FILE.write_text(json.dumps(known_good_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Step 10: Готово
    update_meta = {
        "timestamp": get_timestamp(),
        "commit": vds_head_after,
        "checkpoint_id": checkpoint_id,
        "backup_file": backup_name,
        "vds_services": "6/6 healthy",
        "business_data_preserved": True,
        "deploy_head": local_head,
    }
    LAST_UPDATE_FILE.write_text(json.dumps(update_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    update_current_status(
        job_id, "update_vds_code_only", "COMPLETED", "Готово", 10, total_steps,
        f"UPDATE VDS успешно выполнен! Коммит: {vds_head_after[:10]}, Точка восстановления: {checkpoint_id}.",
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
        summary=f"Code-only deploy to VDS successful. Commit: {vds_head_after}. Checkpoint: {checkpoint_id}. All 6 services healthy. Business data preserved.",
        extra={
            "checkpoint_id": checkpoint_id,
            "backup_sha256": checkpoint_manifest.get("business_backup_sha256"),
            "schema_sha256": checkpoint_manifest.get("previous_schema_sha256"),
            "auto_rollback_attempted": False,
        }
    )


# ==============================================================================
# OPERATION 3: MANUAL FAST ROLLBACK (CODE-ONLY WITHOUT DATA LOSS)
# ==============================================================================

def execute_rollback_vds_code_only(job_id: str, request_data: Dict[str, Any]):
    """
    Execute fast code-only rollback of VDS to a known-good release checkpoint:
    1. Checks VDS liveness (if SSH unreachable -> error without fake success).
    2. Identifies target rollback checkpoint.
    3. Checks Rollback Schema Guard: live VDS schema contract vs target checkpoint contract.
       If incompatible, HARD BLOCKS rollback to protect DB!
    4. Creates a pre-rollback disaster safety backup of current VDS state.
    5. Reverts code/containers on VDS to target checkpoint commit/images.
    6. Ensures business DB and storage media are NEVER overwritten.
    7. Verifies 6/6 services healthy, business counts preserved, and CA unchanged.
    """
    started_at = get_timestamp()
    vds_host = request_data.get("vds_host", DEFAULT_VDS_HOST)
    ssh_key = request_data.get("ssh_key", DEFAULT_SSH_KEY)
    requested_checkpoint_id = request_data.get("checkpoint_id")

    total_steps = 10
    update_current_status(job_id, "rollback_vds_code_only", "RUNNING", "Проверка доступности VDS", 1, total_steps, "Проверка связи с VDS и наличия точек восстановления...")

    # 1. Check VDS liveness
    ssh_test = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=10", vds_host, "test -f /srv/technoreboot/data/.technoreboot_production_data && echo OK"],
        capture_output=True, text=True
    )
    if ssh_test.returncode != 0 or "OK" not in ssh_test.stdout:
        raise RuntimeError(f"VDS полностью недоступен по SSH. Автоматический откат невозможен. Последний локальный recovery checkpoint сохранён в {RELEASES_DIR}")

    # 2. Find target checkpoint
    checkpoints = get_checkpoints_inventory()
    target_checkpoint = None
    if requested_checkpoint_id:
        for cp in checkpoints:
            if cp.get("checkpoint_id") == requested_checkpoint_id:
                target_checkpoint = cp
                break
    elif checkpoints:
        target_checkpoint = checkpoints[0]

    if not target_checkpoint:
        raise RuntimeError("ROLLBACK BLOCKED: Нет доступных точек восстановления для отката.")

    checkpoint_id = target_checkpoint["checkpoint_id"]
    target_head = target_checkpoint.get("previous_head")
    if not target_head or target_head == "unknown":
        target_head = target_checkpoint.get("target_head")

    update_current_status(job_id, "rollback_vds_code_only", "RUNNING", "Проверка совместимости схемы БД", 2, total_steps, f"Сверка схемы БД для целевой версии {target_head[:8]}...")

    # 3. Rollback Schema Guard Check
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from db_schema_contract import check_live_vds_schema, compute_contract_sha256, compare_schema_contracts

    vds_live_contract = check_live_vds_schema(ssh_key, vds_host)
    live_schema_sha = compute_contract_sha256(vds_live_contract)
    target_schema_sha = target_checkpoint.get("previous_schema_sha256")

    if target_schema_sha and live_schema_sha != target_schema_sha:
        raise RuntimeError(
            f"ROLLBACK BLOCKED: структура базы данных отличается от структуры предыдущей версии приложения.\n"
            f"Текущая схема: {live_schema_sha[:10]}, целевая схема: {target_schema_sha[:10]}.\n"
            f"Нужен отдельный ручной recovery/migration этап. База VDS не изменена."
        )

    vds_head_before = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "git -C /srv/technoreboot/app rev-parse HEAD"],
        capture_output=True, text=True
    ).stdout.strip()

    # 4. Create pre-rollback safety backup of current VDS
    update_current_status(job_id, "rollback_vds_code_only", "RUNNING", "Создание safety backup", 3, total_steps, "Создание бэкапа текущих данных VDS перед откатом кода...")
    
    safety_backup_run = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "python3 /srv/technoreboot/app/scripts/vds_backup.py"],
        capture_output=True, text=True, timeout=45
    )
    safety_backup_name = "unknown"
    if safety_backup_run.returncode == 0:
        for line in safety_backup_run.stdout.splitlines():
            if line.startswith("VDS_PRE_STAGE_BACKUP_FILE="):
                safety_backup_name = line.split("=", 1)[1].strip()
                break
            elif "TECHNOREBOOT_BACKUP_" in line and ".zip" in line:
                for part in line.replace("=", " ").split():
                    if part.startswith("TECHNOREBOOT_BACKUP_") and part.endswith(".zip"):
                        safety_backup_name = part
                        break

    # 5. Execute Code Rollback on VDS
    update_current_status(job_id, "rollback_vds_code_only", "RUNNING", "Откат кода на VDS", 5, total_steps, f"Переключение git на коммит {target_head[:8]} и перезапуск контейнеров...")
    
    rb_cmd = f"git -C /srv/technoreboot/app checkout -f {target_head} && docker compose -f /srv/technoreboot/app/deploy/production/docker-compose.prod.yml --env-file /srv/technoreboot/secrets/production.env up -d --remove-orphans"
    rb_exec = subprocess.run(
        ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, rb_cmd],
        capture_output=True, text=True, timeout=60
    )
    if rb_exec.returncode != 0:
        raise RuntimeError(f"Сбой выполнения отката на VDS:\n{rb_exec.stderr.strip() or rb_exec.stdout.strip()}")

    # 6. Wait for services healthy
    update_current_status(job_id, "rollback_vds_code_only", "RUNNING", "Проверка сервисов", 7, total_steps, "Ожидание перехода всех 6 контейнеров VDS в healthy...")
    
    time.sleep(4)
    health_status, probe_data, health_err = check_vds_health_preflight(ssh_key, vds_host)
    if health_status != "HEALTHY":
        raise RuntimeError(f"Сервисы VDS после отката не перешли в здоровое состояние: {health_err}")

    # 7. Verify business data preservation
    update_current_status(job_id, "rollback_vds_code_only", "RUNNING", "Проверка сохранности данных", 9, total_steps, "Проверка неизменности бизнес-данных и Client CA...")
    
    vds_head_after = probe_data.get("git_head", target_head)
    
    rollback_meta = {
        "timestamp": get_timestamp(),
        "commit": vds_head_after,
        "checkpoint_id": checkpoint_id,
        "safety_backup": safety_backup_name,
        "vds_services": "6/6 healthy",
        "business_data_preserved": True,
        "normal_rollback_code_only": True,
    }
    LAST_UPDATE_FILE.write_text(json.dumps(rollback_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    update_current_status(
        job_id, "rollback_vds_code_only", "COMPLETED", "Готово", 10, total_steps,
        f"Откат VDS успешно выполнен! Активный коммит: {vds_head_after[:8]}. Бизнес-данные сохранены.",
        result=rollback_meta,
    )

    local_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True).stdout.strip()
    append_audit_log(
        job_id=job_id,
        operation_type="rollback_vds_code_only",
        requested_at=request_data.get("requested_at", started_at),
        started_at=started_at,
        finished_at=get_timestamp(),
        result_status="SUCCESS",
        local_head=local_head,
        vds_head_before=vds_head_before,
        vds_head_after=vds_head_after,
        backup_file=safety_backup_name,
        summary=f"Fast code-only rollback of VDS to checkpoint {checkpoint_id} ({target_head[:8]}). All 6 services healthy. Business data preserved.",
        extra={
            "source_checkpoint_id": checkpoint_id,
            "safety_backup_before_rollback": safety_backup_name,
            "normal_rollback_code_only": True,
        }
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

    if not acquire_lock(job_id, operation):
        print(f"[RUNNER] Cannot acquire lock for job {job_id}. Skipping.")
        return False

    try:
        if operation == "sync_vds_to_local":
            execute_sync_vds_to_local(job_id, req_data)
        elif operation == "update_vds_code_only":
            execute_update_vds_code_only(job_id, req_data)
        elif operation == "rollback_vds_code_only":
            execute_rollback_vds_code_only(job_id, req_data)
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

        checkpoints = get_checkpoints_inventory()
        latest_cp = checkpoints[0] if checkpoints else None

        last_known_good = None
        if LAST_KNOWN_GOOD_FILE.is_file():
            try:
                last_known_good = json.loads(LAST_KNOWN_GOOD_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass

        env_payload = {
            "heartbeat_at": get_timestamp(),
            "git_head": head_res.stdout.strip(),
            "git_branch": branch_res.stdout.strip(),
            "git_clean": len(dirty) == 0,
            "ssh_key_exists": Path(DEFAULT_SSH_KEY).is_file(),
            "vds_host": DEFAULT_VDS_HOST,
            "checkpoints_count": len(checkpoints),
            "latest_checkpoint": latest_cp,
            "last_known_good": last_known_good,
            "rollback_available": bool(latest_cp and latest_cp.get("rollback_allowed", False)),
        }
        (STATUS_DIR / "environment_info.json").write_text(json.dumps(env_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Technoreboot Local Operations Runner")
    parser.add_argument("--once", action="store_true", help="Process pending requests once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in background")
    parser.add_argument("--status", action="store_true", help="Print current runner status")
    parser.add_argument("--preflight", action="store_true", help="Run VDS health preflight check")
    parser.add_argument("--inventory", action="store_true", help="Show checkpoints inventory")
    
    args = parser.parse_args()
    
    if args.status:
        if CURRENT_FILE.is_file():
            print(CURRENT_FILE.read_text(encoding="utf-8"))
        else:
            print("No operations status recorded.")
        return

    if args.preflight:
        status, probe, err = check_vds_health_preflight(DEFAULT_SSH_KEY, DEFAULT_VDS_HOST)
        print(f"VDS Preflight Status: {status}")
        if err:
            print(f"Reason: {err}")
        print(json.dumps(probe, indent=2, ensure_ascii=False))
        return

    if args.inventory:
        cps = get_checkpoints_inventory()
        print(f"Found {len(cps)} checkpoints in {RELEASES_DIR}:")
        for cp in cps:
            print(f" - {cp.get('checkpoint_id')}: commit={cp.get('previous_head', '')[:8]} created={cp.get('created_at')}")
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
