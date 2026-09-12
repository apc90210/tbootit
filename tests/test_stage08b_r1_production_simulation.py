"""
Stage 08B-R1: Automated Test Suite for Fresh Build and Production Simulation (Tests Y and Z)
- Test Y: fresh-clone production build succeeds.
- Test Z: isolated production simulation passes and tears down cleanly.
"""

import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(r"C:\tbootit")
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import simulate_production_stack


@pytest.fixture(scope="module")
def sim_result():
    """Runs the isolated production simulation once for this module and returns the report."""
    return simulate_production_stack.run_simulation(leave_running=False)


def test_y_fresh_clone_production_build_succeeds(sim_result):
    """TEST Y: Fresh clone production compose build succeeds from clean source checkout."""
    assert sim_result.get("clone_head") is not None
    assert len(sim_result["clone_head"]) == 40
    assert sim_result.get("docker_security_baseline_passed") is True


def test_z_isolated_production_simulation_passes_and_teardown_clean(sim_result):
    """TEST Z: Isolated production simulation passes all routes/security checks and tears down cleanly."""
    assert sim_result.get("internal_services_publicly_exposed") is False
    assert sim_result.get("http_redirect") is True
    assert sim_result.get("no_cert_rejected") is True
    assert sim_result.get("owner_cert_accepted") is True
    assert sim_result.get("root") is True
    assert sim_result.get("products") is True
    assert sim_result.get("sales") is True
    assert sim_result.get("repairs") is True
    assert sim_result.get("avito_extension") is True
    assert sim_result.get("backups") is True
    assert sim_result.get("certificates") is True
    assert sim_result.get("user_cert_rbac_enforced") is True
    assert sim_result.get("teardown") is True
    assert sim_result.get("live_data_unchanged") is True
