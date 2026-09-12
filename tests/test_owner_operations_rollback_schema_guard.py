import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import local_ops_runner as ops
from local_ops_runner import execute_rollback_vds_code_only


@pytest.fixture
def mock_checkpoint_env(tmp_path, monkeypatch):
    test_releases = tmp_path / "vds-releases"
    test_releases.mkdir(parents=True)
    test_devops = tmp_path / "dev-ops"
    test_devops.mkdir(parents=True)
    status_dir = test_devops / "status"
    audit_dir = test_devops / "audit"
    status_dir.mkdir(parents=True)
    audit_dir.mkdir(parents=True)

    monkeypatch.setattr(ops, "RELEASES_DIR", test_releases)
    monkeypatch.setattr(ops, "DEVOPS_DIR", test_devops)
    monkeypatch.setattr(ops, "STATUS_DIR", status_dir)
    monkeypatch.setattr(ops, "CURRENT_FILE", status_dir / "current.json")
    monkeypatch.setattr(ops, "LAST_UPDATE_FILE", status_dir / "last_update.json")
    monkeypatch.setattr(ops, "LAST_KNOWN_GOOD_FILE", status_dir / "last_known_good_vds_release.json")
    monkeypatch.setattr(ops, "AUDIT_LOG_FILE", test_devops / "audit_log.json")
    return test_releases, test_devops


def test_rollback_schema_guard_matching_allows_rollback(mock_checkpoint_env):
    """When live VDS DB schema matches target checkpoint schema, rollback schema guard allows rollback."""
    test_releases, test_devops = mock_checkpoint_env

    matching_hash = "abcde12345matchinghash"
    cid = "checkpoint_match_1"
    cdir = test_releases / cid
    cdir.mkdir()
    manifest = {
        "checkpoint_id": cid,
        "previous_head": "head1234",
        "previous_schema_sha256": matching_hash,
        "created_at": "2026-09-12T12:00:00+03:00",
        "rollback_allowed": True,
    }
    (cdir / "checkpoint.json").write_text(json.dumps(manifest), encoding="utf-8")
    (cdir / "business-backup.zip").write_bytes(b"dummy")

    checkout_executed = False

    def mock_run(cmd, *args, **kwargs):
        nonlocal checkout_executed
        cmd_str = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)
        if "checkout -f" in cmd_str:
            checkout_executed = True
            return MagicMock(returncode=0, stdout="HEAD is now at head1234", stderr="")
        if "git -C /srv/technoreboot/app rev-parse HEAD" in cmd_str:
            return MagicMock(returncode=0, stdout="head1234", stderr="")
        return MagicMock(returncode=0, stdout="OK", stderr="")

    with patch("subprocess.run", side_effect=mock_run):
        with patch("db_schema_contract.check_live_vds_schema", return_value={"tables": {}}):
            with patch("db_schema_contract.compute_contract_sha256", return_value=matching_hash):
                with patch("local_ops_runner.check_vds_health_preflight", return_value=("HEALTHY", {"git_head": "head1234"}, None)):
                    execute_rollback_vds_code_only(
                        job_id="test_match_job",
                        request_data={"checkpoint_id": cid, "ssh_key": "fake_key", "vds_host": "root@fake_host"}
                    )

    assert checkout_executed is True


def test_rollback_schema_guard_mismatch_blocks_rollback(mock_checkpoint_env):
    """When live VDS DB schema differs from target checkpoint schema, rollback is HARD BLOCKED."""
    test_releases, test_devops = mock_checkpoint_env

    old_schema_hash = "1111111111oldhash"
    live_schema_hash = "9999999999newhashdiffering"

    cid = "checkpoint_diff_1"
    cdir = test_releases / cid
    cdir.mkdir()
    manifest = {
        "checkpoint_id": cid,
        "previous_head": "head_old",
        "previous_schema_sha256": old_schema_hash,
        "created_at": "2026-09-12T12:00:00+03:00",
        "rollback_allowed": True,
    }
    (cdir / "checkpoint.json").write_text(json.dumps(manifest), encoding="utf-8")
    (cdir / "business-backup.zip").write_bytes(b"dummy")

    checkout_executed = False

    def mock_run(cmd, *args, **kwargs):
        nonlocal checkout_executed
        cmd_str = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)
        if "checkout -f" in cmd_str:
            checkout_executed = True
        return MagicMock(returncode=0, stdout="OK", stderr="")

    with patch("subprocess.run", side_effect=mock_run):
        with patch("db_schema_contract.check_live_vds_schema", return_value={"tables": {}}):
            with patch("db_schema_contract.compute_contract_sha256", return_value=live_schema_hash):
                with pytest.raises(RuntimeError) as exc_info:
                    execute_rollback_vds_code_only(
                        job_id="test_diff_job",
                        request_data={"checkpoint_id": cid, "ssh_key": "fake_key", "vds_host": "root@fake_host"}
                    )
                
                assert "ROLLBACK BLOCKED" in str(exc_info.value)
                assert "структура базы данных отличается" in str(exc_info.value)
                assert "База VDS не изменена" in str(exc_info.value)

    # Verify that checkout was NEVER executed
    assert checkout_executed is False
