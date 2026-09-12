import os
import sys
import json
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import local_ops_runner as ops
from local_ops_runner import (
    create_vds_release_checkpoint,
    enforce_checkpoint_retention,
    get_checkpoints_inventory,
    compute_file_sha256,
)


@pytest.fixture
def mock_releases_dir(tmp_path, monkeypatch):
    test_releases = tmp_path / "vds-releases"
    test_releases.mkdir(parents=True, exist_ok=True)
    test_devops = tmp_path / "dev-ops"
    test_devops.mkdir(parents=True, exist_ok=True)
    test_status = test_devops / "status"
    test_status.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(ops, "RELEASES_DIR", test_releases)
    monkeypatch.setattr(ops, "DEVOPS_DIR", test_devops)
    monkeypatch.setattr(ops, "LAST_KNOWN_GOOD_FILE", test_status / "last_known_good_vds_release.json")
    return test_releases, test_devops


def test_create_vds_release_checkpoint_success(mock_releases_dir, tmp_path, monkeypatch):
    """Verify release checkpoint creates local snapshot, matches SHA256, and records manifest."""
    test_releases, test_devops = mock_releases_dir

    fake_backup_data = b"ZIP_BACKUP_CONTENT_TEST_12345"
    import hashlib
    fake_sha = hashlib.sha256(fake_backup_data).hexdigest()

    # Function to simulate SCP downloading the file locally
    def mock_run_side_effect(cmd, *args, **kwargs):
        cmd_str = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)
        
        # Remote backup creation
        if "vds_backup.py" in cmd_str:
            return MagicMock(returncode=0, stdout=f"Created backup: TECHNOREBOOT_BACKUP_2026-09-12_120000.zip\n", stderr="")
        
        # sha256sum on VDS
        if "sha256sum" in cmd_str:
            return MagicMock(returncode=0, stdout=f"{fake_sha}  /srv/technoreboot/data/backups/TECHNOREBOOT_BACKUP_2026-09-12_120000.zip\n", stderr="")
        
        # scp from VDS to local
        if cmd[0] == "scp":
            local_dest = Path(cmd[-1])
            local_dest.write_bytes(fake_backup_data)
            return MagicMock(returncode=0, stdout="", stderr="")
            
        # remote tagging script
        if "technoreboot-rollback" in kwargs.get("input", "") or "docker" in kwargs.get("input", ""):
            return MagicMock(returncode=0, stdout='{"core": "sha256:core123", "gateway": "sha256:gw123"}', stderr="")

        # remote details script (counts, ca_sha, storage_tree_sha)
        if "SELECT COUNT(*)" in kwargs.get("input", ""):
            return MagicMock(returncode=0, stdout='{"counts": {"products": 149, "sales": 0, "repair_orders": 0, "product_photos": 149, "product_external_listings": 149}, "ca_sha": "fake_ca_sha", "storage_tree_sha": "fake_st_sha"}', stderr="")

        return MagicMock(returncode=0, stdout="OK", stderr="")

    with patch("subprocess.run", side_effect=mock_run_side_effect):
        with patch("db_schema_contract.check_live_vds_schema", return_value={"tables": {}}):
            with patch("db_schema_contract.extract_contract_from_source_models", return_value={"tables": {}}):
                manifest = create_vds_release_checkpoint(
                    job_id="test_job_1",
                    ssh_key="fake_key",
                    vds_host="root@144.31.50.134",
                    previous_head="prev12345678",
                    target_head="targ87654321",
                    preflight_data={"status": "HEALTHY", "products_count": 149},
                )

    assert manifest["status"] == "COMPLETED"
    assert manifest["business_backup_file"] == "TECHNOREBOOT_BACKUP_2026-09-12_120000.zip"
    assert manifest["business_backup_sha256"] == fake_sha
    assert manifest["business_counts"]["products"] == 149
    assert manifest["rollback_allowed"] is True
    assert manifest["previous_head"] == "prev12345678"
    assert manifest["target_head"] == "targ87654321"

    cid = manifest["checkpoint_id"]
    local_manifest_file = test_releases / cid / "checkpoint.json"
    assert local_manifest_file.is_file()

    saved_manifest = json.loads(local_manifest_file.read_text(encoding="utf-8"))
    assert saved_manifest["checkpoint_id"] == cid
    assert saved_manifest["business_backup_sha256"] == fake_sha

    # Check mirror in dev-ops/checkpoints
    devops_manifest = test_devops / "checkpoints" / cid / "checkpoint.json"
    assert devops_manifest.is_file()


def test_create_checkpoint_sha_mismatch_fails(mock_releases_dir):
    """If local backup SHA does not match VDS SHA, checkpoint creation must raise RuntimeError."""
    fake_vds_sha = "1111111111111111111111111111111111111111111111111111111111111111"
    
    def mock_run_side_effect(cmd, *args, **kwargs):
        cmd_str = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)
        if "vds_backup.py" in cmd_str:
            return MagicMock(returncode=0, stdout="Created backup: TECHNOREBOOT_BACKUP_2026-09-12_120000.zip\n", stderr="")
        if "sha256sum" in cmd_str:
            return MagicMock(returncode=0, stdout=f"{fake_vds_sha}  backup.zip\n", stderr="")
        if cmd[0] == "scp":
            Path(cmd[-1]).write_bytes(b"CORRUPTED_DIFFERENT_CONTENT")
            return MagicMock(returncode=0, stdout="", stderr="")
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=mock_run_side_effect):
        with pytest.raises(RuntimeError) as exc_info:
            create_vds_release_checkpoint(
                job_id="test_job_2",
                ssh_key="fake_key",
                vds_host="root@fake_host",
                previous_head="prev1111",
                target_head="targ2222",
                preflight_data={},
            )
        assert "не совпадает с VDS" in str(exc_info.value)


def test_enforce_checkpoint_retention_keeps_3(mock_releases_dir):
    """Enforce retention retains at least 3 newest checkpoints, deleting older ones."""
    test_releases, test_devops = mock_releases_dir

    # Create 5 fake checkpoints with timestamps
    for i in range(1, 6):
        cid = f"checkpoint_20260912_12000{i}_commit0{i}"
        cdir = test_releases / cid
        cdir.mkdir(parents=True)
        manifest = {
            "checkpoint_id": cid,
            "created_at": f"2026-09-12T12:00:0{i}+03:00",
            "business_backup_file": f"backup_{i}.zip",
        }
        (cdir / "checkpoint.json").write_text(json.dumps(manifest), encoding="utf-8")
        (cdir / "business-backup.zip").write_bytes(b"dummy")

    inventory_before = get_checkpoints_inventory()
    assert len(inventory_before) == 5

    # Run retention with keep_count=3
    enforce_checkpoint_retention(keep_count=3)

    inventory_after = get_checkpoints_inventory()
    assert len(inventory_after) == 3

    remaining_ids = [cp["checkpoint_id"] for cp in inventory_after]
    # Checkpoints 5, 4, 3 must be kept (newest timestamps)
    assert "checkpoint_20260912_120005_commit05" in remaining_ids
    assert "checkpoint_20260912_120004_commit04" in remaining_ids
    assert "checkpoint_20260912_120003_commit03" in remaining_ids
    # Checkpoints 1 and 2 must have been removed
    assert not (test_releases / "checkpoint_20260912_120001_commit01").exists()
    assert not (test_releases / "checkpoint_20260912_120002_commit02").exists()


def test_enforce_retention_preserves_last_known_good(mock_releases_dir):
    """Checkpoints marked as last known good must never be pruned even if older."""
    test_releases, test_devops = mock_releases_dir

    for i in range(1, 5):
        cid = f"checkpoint_20260912_12000{i}_commit0{i}"
        cdir = test_releases / cid
        cdir.mkdir(parents=True)
        manifest = {
            "checkpoint_id": cid,
            "created_at": f"2026-09-12T12:00:0{i}+03:00",
            "business_backup_file": f"backup_{i}.zip",
        }
        (cdir / "checkpoint.json").write_text(json.dumps(manifest), encoding="utf-8")
        (cdir / "business-backup.zip").write_bytes(b"dummy")

    # Set checkpoint 1 (the oldest) as last_known_good
    kg_file = test_devops / "status" / "last_known_good_vds_release.json"
    kg_file.write_text(json.dumps({"checkpoint_id": "checkpoint_20260912_120001_commit01"}), encoding="utf-8")

    enforce_checkpoint_retention(keep_count=2)

    inventory_after = get_checkpoints_inventory()
    remaining_ids = [cp["checkpoint_id"] for cp in inventory_after]
    # Oldest was kept because it's last_known_good
    assert "checkpoint_20260912_120001_commit01" in remaining_ids
    # Checkpoint 4 was kept because it's the newest
    assert "checkpoint_20260912_120004_commit04" in remaining_ids
