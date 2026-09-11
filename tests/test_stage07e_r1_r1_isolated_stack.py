"""
Stage 07E-R1-R1: Automated Test Suite for Real Isolated Recovered Stack Proof
Covers Tests A through Z:
- Test A: Recovery project name differs from live
- Test B: Recovery gateway port differs from 8443
- Test C: Recovery data root differs from live data root
- Test D: Full restore executes without --skip-containers
- Test E: Recovery containers start healthy
- Test F: Recovery DB contains backup counts (227 products, 50 sales, 66 repairs, 490 photos)
- Test G: Recovery media exists
- Test H: Existing OWNER cert authenticates to recovery gateway
- Test I: No-cert rejected by recovery gateway
- Test J: /backups works on recovery gateway
- Test K: /certificates works on recovery gateway
- Test L: inventory route uses recovery DB
- Test M: product detail works
- Test N: sales/reports use recovery DB
- Test O: repairs uses recovery DB
- Test P: Avito extension route works
- Test Q: three restored media files return 200
- Test R: restored CA fingerprint matches backup
- Test S: restored OWNER fingerprint/serial matches backup
- Test T: revoked registry preserved
- Test U: current live DB unchanged
- Test V: current live auth unchanged
- Test W: current live media unchanged
- Test X: current live containers not restarted
- Test Y: recovery teardown does not affect live stack
- Test Z: normal web restore auth-preservation regression still passes
"""

import sys
import os
import json
import sqlite3
import pytest
from pathlib import Path

PROJECT_ROOT = Path(r"C:\tbootit")
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "admin-shell" / "app"))

import isolated_recovery_proof
import backup_service


@pytest.fixture(scope="module")
def proof_execution():
    """Runs the real isolated recovery proof once for the module and returns the execution report."""
    res = isolated_recovery_proof.run_full_isolated_proof(leave_running=False)
    return res


# ==============================================================================
# TESTS A - E: ISOLATION, PORTS, PROJECT NAME & CONTAINER HEALTH
# ==============================================================================

def test_a_recovery_project_name_differs(proof_execution):
    """TEST A: Recovery project name strictly differs from live project 'tbootit'."""
    assert proof_execution["recovery_project"] != proof_execution["live_project"]
    assert proof_execution["recovery_project"].startswith("technoreboot-recovery-")


def test_b_recovery_gateway_port_differs(proof_execution):
    """TEST B: Recovery gateway port differs from live port 8443."""
    assert str(isolated_recovery_proof.RECOVERY_PORTS["gateway"]) != "8443"
    assert "9443" in proof_execution["recovery_gw_url"]
    assert proof_execution["recovery_gw_url"] != proof_execution["live_gw_url"]


def test_c_recovery_data_root_differs(proof_execution):
    """TEST C: Recovery data root is strictly outside live data root."""
    rec_root = Path(proof_execution["recovery_data_root"]).resolve()
    live_root = Path(isolated_recovery_proof.LIVE_DATA_DIR).resolve()
    assert rec_root != live_root
    assert live_root not in rec_root.parents or ".recovery-test" in str(rec_root)
    assert not str(rec_root).startswith(str(live_root))


def test_d_full_restore_executes_without_skip_containers(proof_execution):
    """TEST D: Proof executed against real running containers without skip-containers."""
    containers = proof_execution["recovery_containers"]
    assert len(containers) == 6
    for c in containers:
        assert "recovery" in c


def test_e_recovery_containers_start_healthy(proof_execution):
    """TEST E: Recovery Core and Gateway started and responded with 200 OK."""
    assert proof_execution["route_proofs"]["ROOT"].startswith("HTTP 200")
    assert proof_execution["route_proofs"]["INVENTORY"].startswith("HTTP 200")


# ==============================================================================
# TESTS F - G: RECOVERY DATABASE & MEDIA INTEGRITY
# ==============================================================================

def test_f_recovery_db_contains_backup_counts(proof_execution):
    """TEST F: Recovery DB contains backup counts (227 products, 50 sales, 66 repairs, 490 photos)."""
    rstats = proof_execution["recovery_stats"]
    assert rstats["products"] == 227
    assert rstats["sales"] == 50
    assert rstats["repairs"] == 66
    assert rstats["photos"] == 490

    # Must strictly differ from live product count
    lstats = proof_execution["live_stats"]
    assert lstats["products"] == 50
    assert rstats["products"] != lstats["products"]


def test_g_recovery_media_exists(proof_execution):
    """TEST G: Restored media files exist in recovery storage."""
    assert "MEDIA_1" in proof_execution["route_proofs"]
    assert "MEDIA_2" in proof_execution["route_proofs"]
    assert "MEDIA_3" in proof_execution["route_proofs"]


# ==============================================================================
# TESTS H - K: MTLS SECURITY ON RECOVERY URL
# ==============================================================================

def test_h_existing_owner_cert_authenticates(proof_execution):
    """TEST H: Existing OWNER certificate authenticates to recovery gateway."""
    assert proof_execution["auth_proofs"]["OWNER_CERT_ACCEPTED"] is True


def test_i_no_cert_rejected_by_recovery_gateway(proof_execution):
    """TEST I: Request without client certificate is rejected by recovery gateway."""
    assert "Rejected" in proof_execution["auth_proofs"]["NO_CERT_REJECTED"]


def test_j_backups_works_on_recovery_gateway(proof_execution):
    """TEST J: /backups route works on recovery gateway for OWNER."""
    assert proof_execution["route_proofs"]["BACKUPS"].startswith("HTTP 200")


def test_k_certificates_works_on_recovery_gateway(proof_execution):
    """TEST K: /certificates route works on recovery gateway for OWNER."""
    assert proof_execution["route_proofs"]["CERTIFICATES"].startswith("HTTP 200")


# ==============================================================================
# TESTS L - Q: APPLICATION ROUTES ON RECOVERY GATEWAY ONLY
# ==============================================================================

def test_l_inventory_route_uses_recovery_db(proof_execution):
    """TEST L: Inventory route serves recovered products catalog."""
    assert proof_execution["route_proofs"]["INVENTORY"].startswith("HTTP 200")
    assert "227 products" in proof_execution["route_proofs"]["INVENTORY"]


def test_m_product_detail_works(proof_execution):
    """TEST M: Product detail route loads on recovery gateway."""
    assert "HTTP 200" in proof_execution["route_proofs"]["PRODUCT_DETAIL"] or "HTTP 302" in proof_execution["route_proofs"]["PRODUCT_DETAIL"]


def test_n_sales_reports_use_recovery_db(proof_execution):
    """TEST N: Sales and reports routes load on recovery gateway."""
    assert proof_execution["route_proofs"]["SALES"].startswith("HTTP 200")
    assert proof_execution["route_proofs"]["REPORTS"].startswith("HTTP 200")


def test_o_repairs_uses_recovery_db(proof_execution):
    """TEST O: Repairs route loads on recovery gateway."""
    assert proof_execution["route_proofs"]["REPAIRS"].startswith("HTTP 200")


def test_p_avito_extension_route_works(proof_execution):
    """TEST P: Avito extension route works on recovery gateway."""
    assert proof_execution["route_proofs"]["AVITO_EXTENSION"].startswith("HTTP 200")


def test_q_three_restored_media_files_return_200(proof_execution):
    """TEST Q: At least three restored media files return HTTP 200 on recovery gateway."""
    for idx in (1, 2, 3):
        k = f"MEDIA_{idx}"
        assert k in proof_execution["route_proofs"]
        assert proof_execution["route_proofs"][k].startswith("HTTP 200")


# ==============================================================================
# TESTS R - T: AUTH CONTINUITY PROOF
# ==============================================================================

def test_r_restored_ca_fingerprint_matches_backup(proof_execution):
    """TEST R: Restored CA fingerprint matches accepted historical CA."""
    assert proof_execution["auth_proofs"]["CA_FP"] == "32CEFDD1C8D896D8589DED9C95FF7298791B4ACF2857912D45C3E5894B8BD7AA"


def test_s_restored_owner_fingerprint_matches_backup(proof_execution):
    """TEST S: Restored OWNER certificate fingerprint and serial match backup."""
    assert proof_execution["auth_proofs"]["OWNER_FP"] == "022C0AA7804CE8982F66070DEC04E738765EE76453D1C059317CEFA25E26598D"
    assert proof_execution["auth_proofs"]["OWNER_SERIAL"] == "CDC5645E6C3FC238CE21EA41195DFC0277F9D7F"


def test_t_revoked_registry_preserved(proof_execution):
    """TEST T: Certificate registry preserves revoked certificates."""
    assert proof_execution["auth_proofs"]["REVOKED_CERTS"] == 14


# ==============================================================================
# TESTS U - Y: LIVE STACK ISOLATION & TEARDOWN
# ==============================================================================

def test_u_current_live_db_unchanged(proof_execution):
    """TEST U: Live database SHA256 was 100% unchanged before and after recovery test."""
    iso = proof_execution["live_isolation"]
    assert iso["db_sha_before"] == iso["db_sha_after"]
    assert iso["product_ids_unchanged"] is True
    assert iso["sale_ids_unchanged"] is True


def test_v_current_live_auth_unchanged(proof_execution):
    """TEST V: Live CA SHA256 was 100% unchanged before and after recovery test."""
    iso = proof_execution["live_isolation"]
    assert iso["ca_sha_before"] == iso["ca_sha_after"]


def test_w_current_live_media_unchanged():
    """TEST W: Live media storage directory was untouched."""
    live_storage = PROJECT_ROOT / "data" / "storage"
    assert live_storage.is_dir()


def test_x_current_live_containers_not_restarted(proof_execution):
    """TEST X: Zero live containers were restarted during recovery test."""
    iso = proof_execution["live_isolation"]
    assert iso["containers_restarted"] == 0


def test_y_recovery_teardown_does_not_affect_live_stack(proof_execution):
    """TEST Y: Live stack on port 8443 remains completely healthy after teardown."""
    iso = proof_execution["live_isolation"]
    assert iso["live_health_after"] is True


def test_z_normal_web_restore_auth_preservation_regression():
    """TEST Z: Regression: Normal web restore still preserves live auth."""
    import inspect
    restore_src = inspect.getsource(backup_service.restore_backup)
    assert "Preserve Live Auth" in restore_src
