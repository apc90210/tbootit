import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from local_ops_runner import check_vds_health_preflight


def test_preflight_ssh_unreachable():
    """Unreachable SSH must be classified as UNREACHABLE and block update."""
    with patch("subprocess.run") as mock_run:
        # Mock local disk check passing
        with patch("shutil.disk_usage", return_value=MagicMock(free=10 * 1024 * 1024 * 1024)):
            # Mock SSH failing
            mock_run.return_value = MagicMock(returncode=255, stderr="Connection timed out", stdout="")
            status, probe, err = check_vds_health_preflight("fake_key", "root@fake_host")
            assert status == "UNREACHABLE"
            assert "VDS полностью недоступен по SSH" in err


def test_preflight_dead_https_alive_ssh_is_degraded():
    """If SSH is reachable but HTTPS port 443 fails, classify as DEGRADED."""
    with patch("subprocess.run") as mock_run:
        with patch("shutil.disk_usage", return_value=MagicMock(free=10 * 1024 * 1024 * 1024)):
            # 1. SSH ping OK
            # 2. Remote Python probe OK
            remote_json = '{"sentinel": true, "docker_ok": true, "services": {"core": "healthy", "admin-shell": "healthy", "inventory-sales": "healthy", "repairs": "healthy", "avito": "healthy", "gateway": "healthy"}, "db_readable": true, "db_quick_check": "ok", "products_count": 149, "vds_free_mb": 5000, "git_ok": true, "git_head": "abc12345"}'
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="PING"),
                MagicMock(returncode=0, stdout=remote_json, stderr=""),
            ]
            # Mock HTTPS failing
            with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
                status, probe, err = check_vds_health_preflight("fake_key", "root@fake_host")
                assert status == "DEGRADED"
                assert "HTTPS" in err


def test_preflight_unhealthy_service_is_degraded():
    """Unhealthy container on VDS must classify as DEGRADED and block update."""
    with patch("subprocess.run") as mock_run:
        with patch("shutil.disk_usage", return_value=MagicMock(free=10 * 1024 * 1024 * 1024)):
            remote_json = '{"sentinel": true, "docker_ok": true, "services": {"core": "healthy", "admin-shell": "healthy", "inventory-sales": "unhealthy", "repairs": "healthy", "avito": "healthy", "gateway": "healthy"}, "db_readable": true, "db_quick_check": "ok", "products_count": 149, "vds_free_mb": 5000, "git_ok": true, "git_head": "abc12345"}'
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="PING"),
                MagicMock(returncode=0, stdout=remote_json, stderr=""),
            ]
            with patch("urllib.request.urlopen") as mock_url:
                mock_url.return_value.__enter__.return_value.status = 200
                status, probe, err = check_vds_health_preflight("fake_key", "root@fake_host")
                assert status == "DEGRADED"
                assert "inventory-sales" in err


def test_preflight_unreadable_db_is_degraded():
    """Unreadable or corrupted SQLite DB must classify as DEGRADED."""
    with patch("subprocess.run") as mock_run:
        with patch("shutil.disk_usage", return_value=MagicMock(free=10 * 1024 * 1024 * 1024)):
            remote_json = '{"sentinel": true, "docker_ok": true, "services": {"core": "healthy", "admin-shell": "healthy", "inventory-sales": "healthy", "repairs": "healthy", "avito": "healthy", "gateway": "healthy"}, "db_readable": false, "db_quick_check": "corrupt database", "products_count": 0, "vds_free_mb": 5000, "git_ok": true, "git_head": "abc12345"}'
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="PING"),
                MagicMock(returncode=0, stdout=remote_json, stderr=""),
            ]
            with patch("urllib.request.urlopen") as mock_url:
                mock_url.return_value.__enter__.return_value.status = 200
                status, probe, err = check_vds_health_preflight("fake_key", "root@fake_host")
                assert status == "DEGRADED"
                assert "целостности" in err or "SQLite" in err


def test_preflight_low_vds_disk_is_degraded():
    """Low free disk space on VDS (< 500 MB) must classify as DEGRADED."""
    with patch("subprocess.run") as mock_run:
        with patch("shutil.disk_usage", return_value=MagicMock(free=10 * 1024 * 1024 * 1024)):
            remote_json = '{"sentinel": true, "docker_ok": true, "services": {"core": "healthy", "admin-shell": "healthy", "inventory-sales": "healthy", "repairs": "healthy", "avito": "healthy", "gateway": "healthy"}, "db_readable": true, "db_quick_check": "ok", "products_count": 149, "vds_free_mb": 120, "git_ok": true, "git_head": "abc12345"}'
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="PING"),
                MagicMock(returncode=0, stdout=remote_json, stderr=""),
            ]
            with patch("urllib.request.urlopen") as mock_url:
                mock_url.return_value.__enter__.return_value.status = 200
                status, probe, err = check_vds_health_preflight("fake_key", "root@fake_host")
                assert status == "DEGRADED"
                assert "места на диске VDS" in err


def test_preflight_low_local_disk_is_degraded():
    """Low free disk space on LOCAL (< 500 MB) must classify as DEGRADED."""
    with patch("shutil.disk_usage", return_value=MagicMock(free=200 * 1024 * 1024)):  # 200 MB
        status, probe, err = check_vds_health_preflight("fake_key", "root@fake_host")
        assert status == "DEGRADED"
        assert "локальном диске" in err
