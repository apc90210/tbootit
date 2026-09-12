import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
admin_shell_path = str(REPO_ROOT / "admin-shell")
scripts_path = str(REPO_ROOT / "scripts")

for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        mod = sys.modules[k]
        if hasattr(mod, "__file__") and mod.__file__ and "admin-shell" not in mod.__file__:
            sys.modules.pop(k, None)

if admin_shell_path in sys.path:
    sys.path.remove(admin_shell_path)
sys.path.insert(0, admin_shell_path)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import app.main as admin_main
import local_ops_runner as ops
from local_ops_runner import execute_rollback_vds_code_only, execute_update_vds_code_only

app = admin_main.app
auth_manager = admin_main.auth_manager
client = TestClient(app)


@pytest.fixture
def owner_headers():
    return {"x-auth-is-owner": "1"}


@pytest.fixture
def seller_cert():
    users = [c for c in auth_manager.list_certificates() if not c.get("is_owner") and c.get("status") == "ACTIVE"]
    if users:
        return users[0]
    return auth_manager.create_user_certificate("Тестовый Продавец Rollback RBAC")


def test_rollback_user_forbidden(seller_cert):
    """USER role certificate must receive 403 on rollback endpoint."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }
    resp = client.post("/admin-api/system/operations/rollback", headers=seller_headers)
    assert resp.status_code == 403
    assert "Owner certificate required" in resp.json()["detail"]


def test_rollback_anonymous_forbidden():
    """Anonymous request must receive 403 on rollback endpoint."""
    resp = client.post("/admin-api/system/operations/rollback")
    assert resp.status_code == 403
    assert "Owner certificate required" in resp.json()["detail"]


def test_rollback_environment_guard_blocks_on_vds(monkeypatch, owner_headers):
    """In production / VDS environment, rollback must be blocked with 403."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    resp = client.post("/admin-api/system/operations/rollback", headers=owner_headers)
    assert resp.status_code == 403
    assert "доступны только из локальной DEV-среды" in resp.json()["detail"]


def test_rollback_no_checkpoints_returns_400(monkeypatch, owner_headers):
    """If no release checkpoints exist, rollback must be rejected with 400."""
    monkeypatch.setattr(admin_main, "_get_vds_checkpoints", lambda d: [])
    resp = client.post("/admin-api/system/operations/rollback", headers=owner_headers)
    assert resp.status_code == 400
    assert "нет доступных точек восстановления" in resp.json()["detail"]


def test_rollback_blocked_by_checkpoint_flag(monkeypatch, owner_headers):
    """If target checkpoint has rollback_allowed=False, rollback is rejected with 400."""
    fake_cp = [{
        "checkpoint_id": "checkpoint_test_blocked",
        "rollback_allowed": False,
        "rollback_reason": "Схема БД несовместима",
    }]
    monkeypatch.setattr(admin_main, "_get_vds_checkpoints", lambda d: fake_cp)
    resp = client.post("/admin-api/system/operations/rollback", headers=owner_headers)
    assert resp.status_code == 400
    assert "Схема БД несовместима" in resp.json()["detail"]


def test_rollback_owner_allowed_and_queued(monkeypatch, owner_headers, tmp_path):
    """OWNER role with valid checkpoint queues rollback request with 200."""
    fake_cp = [{
        "checkpoint_id": "checkpoint_20260912_120000_abc12345",
        "rollback_allowed": True,
        "rollback_reason": "Доступен быстрый откат",
    }]
    monkeypatch.setattr(admin_main, "_get_vds_checkpoints", lambda d: fake_cp)
    
    resp = client.post("/admin-api/system/operations/rollback", headers=owner_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert data["operation"] == "rollback_vds_code_only"
    assert "job_id" in data


def test_execute_rollback_vds_code_only_success(tmp_path, monkeypatch):
    """Verify execute_rollback_vds_code_only executes checkout, creates safety backup, and does not alter DB."""
    test_releases = tmp_path / "vds-releases"
    test_releases.mkdir(parents=True)
    cid = "checkpoint_20260912_120000_deadbeef"
    cdir = test_releases / cid
    cdir.mkdir()
    
    manifest = {
        "checkpoint_id": cid,
        "previous_head": "prev_commit_12345",
        "previous_schema_sha256": "matching_schema_hash_123",
        "created_at": "2026-09-12T12:00:00+03:00",
        "rollback_allowed": True,
    }
    (cdir / "checkpoint.json").write_text(json.dumps(manifest), encoding="utf-8")
    (cdir / "business-backup.zip").write_bytes(b"backup")

    devops_dir = tmp_path / "dev-ops"
    status_dir = devops_dir / "status"
    audit_dir = devops_dir / "audit"
    status_dir.mkdir(parents=True)
    audit_dir.mkdir(parents=True)

    monkeypatch.setattr(ops, "RELEASES_DIR", test_releases)
    monkeypatch.setattr(ops, "DEVOPS_DIR", devops_dir)
    monkeypatch.setattr(ops, "STATUS_DIR", status_dir)
    monkeypatch.setattr(ops, "CURRENT_FILE", status_dir / "current.json")
    monkeypatch.setattr(ops, "LAST_UPDATE_FILE", status_dir / "last_update.json")
    monkeypatch.setattr(ops, "LAST_KNOWN_GOOD_FILE", status_dir / "last_known_good_vds_release.json")
    monkeypatch.setattr(ops, "AUDIT_LOG_FILE", devops_dir / "audit_log.json")

    def mock_run(cmd, *args, **kwargs):
        cmd_str = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)
        if "test -f /srv/technoreboot/data/.technoreboot_production_data" in cmd_str:
            return MagicMock(returncode=0, stdout="OK\n", stderr="")
        if "vds_backup.py" in cmd_str:
            return MagicMock(returncode=0, stdout="Created backup: TECHNOREBOOT_BACKUP_SAFETY_PRE_ROLLBACK.zip\n", stderr="")
        if "checkout -f" in cmd_str:
            return MagicMock(returncode=0, stdout="HEAD is now at prev_commit_12345\n", stderr="")
        if "git -C /srv/technoreboot/app rev-parse HEAD" in cmd_str:
            return MagicMock(returncode=0, stdout="prev_commit_12345\n", stderr="")
        return MagicMock(returncode=0, stdout="OK\n", stderr="")

    with patch("subprocess.run", side_effect=mock_run):
        with patch("db_schema_contract.check_live_vds_schema", return_value={"tables": {}}):
            with patch("db_schema_contract.compute_contract_sha256", return_value="matching_schema_hash_123"):
                with patch("local_ops_runner.check_vds_health_preflight", return_value=("HEALTHY", {"git_head": "prev_commit_12345"}, None)):
                    execute_rollback_vds_code_only(
                        job_id="test_rollback_job",
                        request_data={"checkpoint_id": cid, "ssh_key": "fake_key", "vds_host": "root@fake_host"}
                    )

    # Check status file updated
    current_status = json.loads((status_dir / "current.json").read_text(encoding="utf-8"))
    assert current_status["status"] == "COMPLETED"
    assert "Откат VDS успешно выполнен" in current_status["log_lines"][-1]
    assert current_status["result"]["business_data_preserved"] is True
    assert current_status["result"]["normal_rollback_code_only"] is True


def test_auto_rollback_on_update_failure(tmp_path, monkeypatch):
    """If update_code_only.sh fails on VDS, automated rollback must trigger and record UPDATE_FAILED_ROLLBACK_SUCCESS."""
    devops_dir = tmp_path / "dev-ops"
    status_dir = devops_dir / "status"
    audit_dir = devops_dir / "audit"
    status_dir.mkdir(parents=True)
    audit_dir.mkdir(parents=True)

    monkeypatch.setattr(ops, "DEVOPS_DIR", devops_dir)
    monkeypatch.setattr(ops, "STATUS_DIR", status_dir)
    monkeypatch.setattr(ops, "CURRENT_FILE", status_dir / "current.json")
    monkeypatch.setattr(ops, "LAST_UPDATE_FILE", status_dir / "last_update.json")
    monkeypatch.setattr(ops, "LAST_KNOWN_GOOD_FILE", status_dir / "last_known_good_vds_release.json")
    monkeypatch.setattr(ops, "AUDIT_LOG_FILE", devops_dir / "audit_log.json")

    fake_checkpoint_manifest = {
        "checkpoint_id": "checkpoint_auto_rb_test",
        "business_backup_file": "backup.zip",
        "business_backup_sha256": "sha123",
        "previous_schema_sha256": "schema123",
    }

    # Simulate deploy failing
    def mock_run(cmd, *args, **kwargs):
        cmd_str = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)
        if "update_code_only.sh" in cmd_str:
            return MagicMock(returncode=1, stderr="Build failed: syntax error in container build", stdout="")
        if "checkout -f" in cmd_str:
            return MagicMock(returncode=0, stdout="Reverted to previous commit", stderr="")
        if "status" in cmd_str or "porcelain" in cmd_str:
            return MagicMock(returncode=0, stdout="", stderr="")
        if "rev-parse" in cmd_str:
            return MagicMock(returncode=0, stdout="test_mock_commit", stderr="")
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=mock_run):
        with patch("local_ops_runner.create_vds_release_checkpoint", return_value=fake_checkpoint_manifest):
            with patch("local_ops_runner.check_vds_health_preflight") as mock_preflight:
                # Preflight 1: initial update preflight -> HEALTHY
                # Preflight 2: auto-rollback health check -> HEALTHY
                mock_preflight.side_effect = [
                    ("HEALTHY", {"git_head": "previous_working_commit"}, None),
                    ("HEALTHY", {"git_head": "previous_working_commit"}, None),
                ]
                with patch("db_schema_contract.check_deployment_compatibility_flag", return_value=(True, "OK")):
                    with patch("db_schema_contract.check_live_vds_schema", return_value={"tables": {}}):
                        with patch("db_schema_contract.extract_contract_from_source_models", return_value={"tables": {}}):
                            with patch("db_schema_contract.compare_schema_contracts", return_value=(True, [])):
                                with patch("time.sleep", return_value=None):
                                    with pytest.raises(RuntimeError) as exc_info:
                                        execute_update_vds_code_only(
                                            job_id="test_update_fail_job",
                                            request_data={"ssh_key": "fake_key", "vds_host": "root@fake_host"}
                                        )
                                    assert "Автоматический откат" in str(exc_info.value) or "UPDATE_FAILED" in str(exc_info.value)

    # Status must be UPDATE_FAILED_ROLLBACK_SUCCESS
    current_status = json.loads((status_dir / "current.json").read_text(encoding="utf-8"))
    assert current_status["status"] == "UPDATE_FAILED_ROLLBACK_SUCCESS"

