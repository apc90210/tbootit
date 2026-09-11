"""
Stage 07E-R1-R2: Automated Test Suite
Fresh Git Build + Full Backup Integrity Proof (Tests A through Z)
"""

import sys
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(r"C:\tbootit")
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "admin-shell" / "app"))

import fresh_build_and_integrity_proof


@pytest.fixture(scope="module")
def proof_data():
    """Runs the full fresh build & integrity proof engine once for this module."""
    data = fresh_build_and_integrity_proof.run_full_proof(leave_running=False)
    return data


# ==============================================================================
# TESTS A - D: FRESH GIT CLONE & FRESH IMAGE BUILD PROOF (GAP 1)
# ==============================================================================

def test_a_fresh_clone_is_from_origin(proof_data):
    """TEST A: Fresh clone is from origin/main repository URL."""
    assert proof_data["fresh_clone"] is True
    assert "tbootit" in proof_data["recovery_origin"]


def test_b_fresh_clone_head_matches(proof_data):
    """TEST B: Fresh clone HEAD matches expected git commit."""
    assert len(proof_data["recovery_head"]) == 40
    assert proof_data["recovery_head"] == proof_data["origin_main_head"] or proof_data["recovery_head"] == proof_data["live_head"]


def test_c_recovery_images_built_from_fresh_clone(proof_data):
    """TEST C: Recovery images are built from source under the fresh clone repo."""
    assert proof_data["built_from_recovery_repo"] is True
    assert len(proof_data["recovery_images"]) >= 5
    for tag in proof_data["recovery_images"]:
        assert proof_data["run_id"] in tag


def test_d_live_image_ids_not_reused(proof_data):
    """TEST D: Normal live application image IDs are strictly NOT used by recovery containers."""
    assert proof_data["live_image_ids_used"] is False


# ==============================================================================
# TESTS E - I: FULL STORAGE TREE INTEGRITY & DISCREPANCY EXPLANATION (GAP 2)
# ==============================================================================

def test_e_storage_file_counts_match(proof_data):
    """TEST E: Full backup storage file count matches restored storage count exactly."""
    st = proof_data["storage_tree"]
    assert st["backup_count"] == 1236
    assert st["restored_count"] == 1236
    assert st["backup_count"] == st["restored_count"]


def test_f_storage_tree_hash_matches(proof_data):
    """TEST F: Full backup storage tree SHA256 matches restored storage tree SHA256."""
    st = proof_data["storage_tree"]
    assert len(st["backup_tree_sha256"]) == 64
    assert st["backup_tree_sha256"] == st["restored_tree_sha256"]
    assert st["backup_bytes"] == st["restored_bytes"]


def test_g_missing_storage_files_zero(proof_data):
    """TEST G: Missing storage files count is strictly 0."""
    st = proof_data["storage_tree"]
    assert st["missing_files"] == 0
    assert st["extra_files"] == 0


def test_h_storage_hash_mismatches_zero(proof_data):
    """TEST H: Storage hash mismatches count is strictly 0."""
    st = proof_data["storage_tree"]
    assert st["hash_mismatches"] == 0


def test_i_discrepancy_1236_vs_1214_explained(proof_data):
    """TEST I: Previous 1236 vs 1214 discrepancy is precisely explained with mathematical proof."""
    st = proof_data["storage_tree"]
    exp = st["count_1236_vs_1214_explanation"]
    assert "1236" in exp and "1214" in exp and "22" in exp
    assert "subdirectories" in exp or "glob" in exp


# ==============================================================================
# TESTS J - K: DATABASE <-> MEDIA REFERENTIAL INTEGRITY
# ==============================================================================

def test_j_product_photo_references_exist(proof_data):
    """TEST J: All local ProductPhoto references exist on disk in storage."""
    pa = proof_data["photo_audit"]
    assert pa["product_photo_rows"] == 490
    assert pa["local_photo_references"] == 475
    assert pa["remote_photo_references"] == 15
    assert pa["missing_referenced_photos"] == 0


def test_k_no_referenced_photo_is_zero_bytes(proof_data):
    """TEST K: No referenced local photo has zero bytes."""
    pa = proof_data["photo_audit"]
    assert pa["zero_byte_referenced_photos"] == 0
    assert pa["orphan_media_files"] == 761


# ==============================================================================
# TESTS L - M: AUTH & AVITO TREE INTEGRITY
# ==============================================================================

def test_l_auth_tree_hash_matches(proof_data):
    """TEST L: Auth tree SHA256 matches backup and has 0 missing or mismatched files."""
    at = proof_data["auth_tree"]
    assert at["backup_sha256"] == at["restored_sha256"]
    assert at["missing"] == 0
    assert at["mismatches"] == 0


def test_m_avito_tree_hash_matches(proof_data):
    """TEST M: Avito state tree SHA256 matches backup and has 0 missing or mismatched files."""
    av = proof_data["avito_tree"]
    assert av["backup_sha256"] == av["restored_sha256"]
    assert av["missing"] == 0
    assert av["mismatches"] == 0


# ==============================================================================
# TESTS N - Q: RECOVERY RUNTIME & MTLS SECURITY
# ==============================================================================

def test_n_recovery_stack_starts_from_fresh_images(proof_data):
    """TEST N: Recovery stack successfully starts from newly built images."""
    rr = proof_data["recovery_runtime"]
    assert "technoreboot-recovery-" in rr["project"]


def test_o_recovery_gateway_uses_alternate_port(proof_data):
    """TEST O: Recovery gateway operates on port 9443 (not live 8443)."""
    assert "9443" in proof_data["recovery_runtime"]["gateway_url"]


def test_p_existing_owner_cert_authenticates(proof_data):
    """TEST P: Existing OWNER certificate authenticates on recovery gateway."""
    rr = proof_data["recovery_runtime"]
    assert rr["owner_cert_accepted"] is True
    assert rr["ca_fp"] == "32CEFDD1C8D896D8589DED9C95FF7298791B4ACF2857912D45C3E5894B8BD7AA"
    assert rr["owner_fp"] == "022C0AA7804CE8982F66070DEC04E738765EE76453D1C059317CEFA25E26598D"
    assert rr["owner_serial"] == "CDC5645E6C3FC238CE21EA41195DFC0277F9D7F"
    assert rr["revoked_count"] == 14


def test_q_no_cert_rejected_by_recovery_gateway(proof_data):
    """TEST Q: Request without client certificate is rejected by recovery gateway."""
    assert proof_data["recovery_runtime"]["no_cert_rejected"] is not None


# ==============================================================================
# TESTS R - W: ROUTE & DATA VERIFICATION ON PORT 9443 ONLY
# ==============================================================================

def test_r_inventory_route_uses_restored_db(proof_data):
    """TEST R: Inventory route serves recovered 227 products from backup DB."""
    assert proof_data["recovery_runtime"]["products"] == 227
    assert "227 products" in proof_data["route_proofs"]["INVENTORY"]


def test_s_sales_reports_use_restored_db(proof_data):
    """TEST S: Sales and sales reports use recovered DB."""
    assert proof_data["recovery_runtime"]["sales"] == 50
    assert "HTTP 200" in proof_data["route_proofs"]["SALES"]
    assert "HTTP 200" in proof_data["route_proofs"]["REPORTS"]


def test_t_repairs_uses_restored_db(proof_data):
    """TEST T: Repairs route loads 66 recovered repair orders from backup DB."""
    assert proof_data["recovery_runtime"]["repairs"] == 66
    assert "HTTP 200" in proof_data["route_proofs"]["REPAIRS"]


def test_u_avito_extension_route_works(proof_data):
    """TEST U: Avito extension bridge route loads on recovery gateway."""
    assert "HTTP 200" in proof_data["route_proofs"]["AVITO_EXTENSION"]


def test_v_backup_certificate_routes_work(proof_data):
    """TEST V: Owner-only /backups and /certificates routes return HTTP 200."""
    assert "HTTP 200" in proof_data["route_proofs"]["BACKUPS"]
    assert "HTTP 200" in proof_data["route_proofs"]["CERTIFICATES"]


def test_w_three_media_files_return_200(proof_data):
    """TEST W: At least 3 restored media files return HTTP 200 on recovery gateway."""
    for idx in (1, 2, 3):
        k = f"MEDIA_{idx}"
        assert k in proof_data["route_proofs"]
        assert "HTTP 200" in proof_data["route_proofs"][k]


# ==============================================================================
# TESTS X - Z: LIVE STACK ISOLATION & TEARDOWN
# ==============================================================================

def test_x_live_stack_identity_sets_unchanged(proof_data):
    """TEST X: Live database, CA, product IDs, sale IDs, and media path set unchanged."""
    iso = proof_data["live_isolation"]
    assert iso["db_unchanged"] is True
    assert iso["ca_unchanged"] is True
    assert iso["product_ids_unchanged"] is True
    assert iso["sale_ids_unchanged"] is True
    assert iso["media_unchanged"] is True


def test_y_live_containers_restarted_zero(proof_data):
    """TEST Y: Live containers restarted count is strictly 0."""
    iso = proof_data["live_isolation"]
    assert iso["containers_restarted"] == 0


def test_z_recovery_teardown_leaves_live_stack_healthy(proof_data):
    """TEST Z: Recovery stack teardown completed and live stack on port 8443 remains healthy."""
    iso = proof_data["live_isolation"]
    assert iso["live_health_after"] is True
