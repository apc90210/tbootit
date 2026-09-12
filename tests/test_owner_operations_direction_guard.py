import os
import sys
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
scripts_dir = str(REPO_ROOT / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)


def test_no_local_to_vds_data_upload_scripts():
    """Verify that no scripts or functions upload local database or local storage to VDS."""
    runner_script = (REPO_ROOT / "scripts" / "local_ops_runner.py").read_text(encoding="utf-8")
    
    # Strictly forbid upload of local DB to VDS
    assert "scp" in runner_script
    # Check that scp only ever downloads from VDS (vds_host:... to local)
    assert 'f"{vds_host}:{remote_snapshot_path}"' in runner_script
    assert "technoreboot.db {vds_host}" not in runner_script
    assert "data/db/ {vds_host}" not in runner_script


def test_sync_runner_aborts_if_production_sentinel_local(tmp_path, monkeypatch):
    """Local ops runner must strictly refuse sync if .technoreboot_production_data exists locally."""
    import local_ops_runner
    
    fake_data = tmp_path / "data"
    fake_data.mkdir()
    (fake_data / ".technoreboot_local_dev").write_text("dev", encoding="utf-8")
    (fake_data / ".technoreboot_production_data").write_text("fake_prod", encoding="utf-8")
    
    monkeypatch.setattr(local_ops_runner, "DATA_DIR", fake_data)
    
    with pytest.raises(RuntimeError) as exc_info:
        local_ops_runner.execute_sync_vds_to_local("job_test", {})
    assert "production sentinel" in str(exc_info.value).lower()


def test_sync_requires_local_dev_sentinel(tmp_path, monkeypatch):
    """Local ops runner must require .technoreboot_local_dev."""
    import local_ops_runner
    
    fake_data = tmp_path / "data"
    fake_data.mkdir()
    # Sentinel missing
    monkeypatch.setattr(local_ops_runner, "DATA_DIR", fake_data)
    
    with pytest.raises(RuntimeError) as exc_info:
        local_ops_runner.execute_sync_vds_to_local("job_test", {})
    assert "отсутствует локальный sentinel" in str(exc_info.value).lower()
