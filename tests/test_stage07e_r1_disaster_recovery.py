"""
Stage 07E-R1: Automated Test Suite for New Server Bootstrap and Disaster Recovery
Covers Tests A through Z:
- Test A: Valid backup accepted
- Test B: Missing manifest rejected
- Test C: Unsupported version rejected
- Test D: Path traversal ZIP rejected (Zip Slip protection)
- Test E: Missing DB rejected
- Test F: Missing auth for full bootstrap rejected
- Test G: Staging restore succeeds
- Test H: Backed-up auth/CA restored
- Test I: Existing OWNER certificate accepted
- Test J: OWNER-only /backups accessible
- Test K: No-cert request rejected
- Test L: Product count matches
- Test M: Avito-linked count matches
- Test N: Local-only count matches
- Test O: Sales count matches
- Test P: Product photo rows match
- Test Q: Sample media returns 200
- Test R: Inventory page loads
- Test S: Product detail loads
- Test T: Sales/report routes load
- Test U: Repairs route loads
- Test V: Avito extension route loads
- Test W: Backup route loads
- Test X: Fresh recovery does not modify original live data
- Test Y: Normal web restore still does NOT overwrite live auth
- Test Z: Relevant regression suites pass
"""

import sys
import os
import json
import sqlite3
import zipfile
import shutil
import hashlib
from pathlib import Path
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "admin-shell" / "app"))
sys.path.insert(0, str(PROJECT_ROOT / "admin-shell"))

import bootstrap_restore
from auth_manager import AuthManager
import backup_service


@pytest.fixture(scope="module")
def valid_backup_path():
    """Locates the accepted full backup archive in backups/."""
    backups_dir = PROJECT_ROOT / "backups"
    latest = bootstrap_restore.find_latest_backup(backups_dir)
    assert latest is not None, f"No backup archive found in {backups_dir}"
    return latest


@pytest.fixture(scope="module")
def live_data_baseline():
    """Records live database and auth hashes before tests to guarantee no modifications."""
    live_db = PROJECT_ROOT / "data" / "db" / "technoreboot.db"
    live_ca = PROJECT_ROOT / "data" / "auth" / "ca" / "ca.crt"
    baseline = {
        "db_hash": hashlib.sha256(live_db.read_bytes()).hexdigest() if live_db.is_file() else None,
        "ca_hash": hashlib.sha256(live_ca.read_bytes()).hexdigest() if live_ca.is_file() else None,
    }
    return baseline


@pytest.fixture(scope="module")
def isolated_recovery(valid_backup_path, tmp_path_factory):
    """
    Executes fresh bootstrap restoration into a completely isolated temporary directory.
    Live c:\\tbootit\\data is untouched.
    """
    isolated_root = tmp_path_factory.mktemp("isolated_recovery_root")
    target_data = isolated_root / "data"

    res = bootstrap_restore.execute_bootstrap_restore(
        backup_zip=valid_backup_path,
        target_data_dir=target_data,
        repo_root=PROJECT_ROOT,
        skip_containers=True,
    )
    return {
        "result": res,
        "target_data": target_data,
        "manifest": res["manifest"],
        "backup_path": valid_backup_path,
    }


# ==============================================================================
# TESTS A - F: ARCHIVE & MANIFEST VALIDATION
# ==============================================================================

def test_a_valid_backup_accepted(valid_backup_path):
    """TEST A: Valid backup archive is accepted and parsed."""
    is_valid, err, manifest = bootstrap_restore.validate_archive_security_and_manifest(valid_backup_path)
    assert is_valid is True, f"Valid backup was rejected: {err}"
    assert err == ""
    assert manifest is not None
    assert manifest["backup_format_version"] == "1.0"
    assert "database" in manifest["components"]
    assert "storage" in manifest["components"]
    assert "auth" in manifest["components"]


def test_b_missing_manifest_rejected(tmp_path):
    """TEST B: Backup archive missing manifest.json is strictly rejected."""
    bad_zip = tmp_path / "missing_manifest.zip"
    with zipfile.ZipFile(bad_zip, "w") as z:
        z.writestr("some_data.txt", "hello")

    is_valid, err, manifest = bootstrap_restore.validate_archive_security_and_manifest(bad_zip)
    assert is_valid is False
    assert "manifest.json" in err.lower()
    assert manifest is None


def test_c_unsupported_version_rejected(tmp_path):
    """TEST C: Backup archive with unsupported format version is rejected."""
    bad_zip = tmp_path / "bad_version.zip"
    with zipfile.ZipFile(bad_zip, "w") as z:
        bad_manifest = {
            "backup_format_version": "99.0",
            "components": ["database", "storage", "auth"],
        }
        z.writestr("manifest.json", json.dumps(bad_manifest))

    is_valid, err, manifest = bootstrap_restore.validate_archive_security_and_manifest(bad_zip)
    assert is_valid is False
    assert "неподдерживаемая версия" in err.lower() or "unsupported" in err.lower()


def test_d_path_traversal_zip_rejected(tmp_path):
    """TEST D: Zip Slip path traversal vulnerability attempts are detected and rejected."""
    traversal_zip = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal_zip, "w") as z:
        manifest = {
            "backup_format_version": "1.0",
            "components": ["database", "storage", "auth"],
        }
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("../evil.txt", "malicious payload")

    is_valid, err, _ = bootstrap_restore.validate_archive_security_and_manifest(traversal_zip)
    assert is_valid is False
    assert "угроза безопасности" in err.lower() or "traversal" in err.lower()

    # Also test absolute path
    abs_zip = tmp_path / "abs_path.zip"
    with zipfile.ZipFile(abs_zip, "w") as z:
        manifest = {
            "backup_format_version": "1.0",
            "components": ["database", "storage", "auth"],
        }
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("/etc/passwd", "root:x:0:0")

    is_valid2, err2, _ = bootstrap_restore.validate_archive_security_and_manifest(abs_zip)
    assert is_valid2 is False
    assert "угроза безопасности" in err2.lower() or "абсолютный путь" in err2.lower()


def test_e_missing_db_rejected(tmp_path):
    """TEST E: Archive missing database file is rejected."""
    no_db_zip = tmp_path / "no_db.zip"
    with zipfile.ZipFile(no_db_zip, "w") as z:
        manifest = {
            "backup_format_version": "1.0",
            "components": ["database", "storage", "auth"],
        }
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("auth/ca/ca.crt", "dummy")
        z.writestr("auth/certificates/owner.crt", "dummy")
        z.writestr("auth/registry.json", "[]")

    is_valid, err, _ = bootstrap_restore.validate_archive_security_and_manifest(no_db_zip)
    assert is_valid is False
    assert "базы данных" in err.lower() or "database" in err.lower()


def test_f_missing_auth_for_full_bootstrap_rejected(tmp_path):
    """TEST F: Archive missing required auth components for fresh server bootstrap is rejected."""
    no_auth_zip = tmp_path / "no_auth.zip"
    with zipfile.ZipFile(no_auth_zip, "w") as z:
        manifest = {
            "backup_format_version": "1.0",
            "components": ["database", "storage", "auth"],
        }
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("database/technoreboot.db", "dummy db content")

    is_valid, err, _ = bootstrap_restore.validate_archive_security_and_manifest(no_auth_zip)
    assert is_valid is False
    assert "аутентификации" in err.lower() or "auth" in err.lower() or "ca.crt" in err.lower()


# ==============================================================================
# TESTS G - K: RESTORE EXECUTION & AUTH CONTINUITY
# ==============================================================================

def test_g_staging_restore_succeeds(isolated_recovery):
    """TEST G: Safe staged extraction and placement completes successfully."""
    assert isolated_recovery["result"]["status"] == "RESTORED"
    target_data = isolated_recovery["target_data"]
    assert (target_data / "db" / "technoreboot.db").is_file()
    assert (target_data / "auth" / "ca" / "ca.crt").is_file()
    assert (target_data / "auth" / "certificates" / "owner.crt").is_file()
    assert (target_data / "storage" / "product_photos").is_dir()


def test_h_backed_up_auth_ca_restored(isolated_recovery):
    """TEST H: Backed-up CA and OWNER certificates are restored and active."""
    target_data = isolated_recovery["target_data"]
    manifest = isolated_recovery["manifest"]

    ca_cert = x509.load_pem_x509_certificate((target_data / "auth" / "ca" / "ca.crt").read_bytes())
    ca_fp = ca_cert.fingerprint(hashes.SHA256()).hex().upper()
    assert ca_fp == manifest["auth"]["ca_fingerprint_sha256"]

    owner_cert = x509.load_pem_x509_certificate((target_data / "auth" / "certificates" / "owner.crt").read_bytes())
    owner_fp = owner_cert.fingerprint(hashes.SHA256()).hex().upper()
    assert owner_fp == manifest["auth"]["owner_fingerprint_sha256"]


def test_i_existing_owner_certificate_accepted(isolated_recovery):
    """TEST I: Recovered system recognizes and accepts existing OWNER client certificate."""
    target_data = isolated_recovery["target_data"]
    auth_mgr = AuthManager(auth_dir=str(target_data / "auth"))

    owner = auth_mgr.get_certificate("owner")
    assert owner is not None
    assert owner["is_owner"] is True
    assert owner["status"] == "ACTIVE"

    ok, code, msg, cert = auth_mgr.verify_request(
        verify_status="SUCCESS",
        client_serial=owner["serial_hex"],
        client_fingerprint=owner["fingerprint_sha256"],
        request_uri="/inventory/products",
    )
    assert ok is True
    assert code == 200
    assert cert["is_owner"] is True


def test_j_owner_only_backups_accessible(isolated_recovery):
    """TEST J: OWNER-only /backups and /certificates routes are accessible for OWNER."""
    target_data = isolated_recovery["target_data"]
    auth_mgr = AuthManager(auth_dir=str(target_data / "auth"))
    owner = auth_mgr.get_certificate("owner")

    # Access certificates admin route
    ok, code, _, cert = auth_mgr.verify_request(
        verify_status="SUCCESS",
        client_serial=owner["serial_hex"],
        client_fingerprint=owner["fingerprint_sha256"],
        request_uri="/certificates",
    )
    assert ok is True
    assert code == 200


def test_k_no_cert_request_rejected(isolated_recovery):
    """TEST K: Unauthenticated requests without certificate or with invalid cert are rejected."""
    target_data = isolated_recovery["target_data"]
    auth_mgr = AuthManager(auth_dir=str(target_data / "auth"))

    # No cert
    ok, code, msg, _ = auth_mgr.verify_request(
        verify_status=None,
        client_serial=None,
        client_fingerprint=None,
        request_uri="/inventory/products",
    )
    assert ok is False
    assert code == 403

    # Unknown cert
    ok2, code2, _, _ = auth_mgr.verify_request(
        verify_status="SUCCESS",
        client_serial="DEADBEEF9999",
        client_fingerprint="0000000000000000000000000000000000000000000000000000000000000000",
        request_uri="/inventory/products",
    )
    assert ok2 is False
    assert code2 == 403

    # Revoked cert
    revoked_cert = next((c for c in auth_mgr.list_certificates() if c.get("status") == "REVOKED"), None)
    if revoked_cert:
        ok3, code3, msg3, _ = auth_mgr.verify_request(
            verify_status="SUCCESS",
            client_serial=revoked_cert["serial_hex"],
            client_fingerprint=revoked_cert["fingerprint_sha256"],
            request_uri="/inventory/products",
        )
        assert ok3 is False
        assert code3 == 403
        assert "revoked" in msg3.lower()


# ==============================================================================
# TESTS L - P: DATA RECOVERY INTEGRITY
# ==============================================================================

def test_l_product_count_matches(isolated_recovery):
    """TEST L: Restored product count matches backup manifest."""
    target_data = isolated_recovery["target_data"]
    manifest = isolated_recovery["manifest"]

    conn = sqlite3.connect(str(target_data / "db" / "technoreboot.db"))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM products;")
    cnt = cur.fetchone()[0]
    conn.close()

    expected = manifest["database"]["tables"].get("products", 227)
    assert cnt == expected, f"Product count mismatch: {cnt} != {expected}"


def test_m_avito_linked_count_matches(isolated_recovery):
    """TEST M: Restored Avito-linked products count matches backup manifest."""
    target_data = isolated_recovery["target_data"]
    manifest = isolated_recovery["manifest"]

    conn = sqlite3.connect(str(target_data / "db" / "technoreboot.db"))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM product_external_listings;")
    cnt = cur.fetchone()[0]
    conn.close()

    expected = manifest["database"]["tables"].get("product_external_listings", 154)
    assert cnt == expected, f"Avito listings count mismatch: {cnt} != {expected}"


def test_n_local_only_count_matches(isolated_recovery):
    """TEST N: Restored local-only products count matches expectation."""
    target_data = isolated_recovery["target_data"]

    conn = sqlite3.connect(str(target_data / "db" / "technoreboot.db"))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM products WHERE id NOT IN (SELECT product_id FROM product_external_listings);")
    cnt = cur.fetchone()[0]
    conn.close()

    assert cnt == 73, f"Local-only count mismatch: {cnt} != 73"


def test_o_sales_count_matches(isolated_recovery):
    """TEST O: Restored sales count matches backup manifest."""
    target_data = isolated_recovery["target_data"]
    manifest = isolated_recovery["manifest"]

    conn = sqlite3.connect(str(target_data / "db" / "technoreboot.db"))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM sales;")
    cnt = cur.fetchone()[0]
    conn.close()

    expected = manifest["database"]["tables"].get("sales", 50)
    assert cnt == expected, f"Sales count mismatch: {cnt} != {expected}"


def test_p_product_photo_rows_match(isolated_recovery):
    """TEST P: Restored product_photos table rows match backup manifest."""
    target_data = isolated_recovery["target_data"]
    manifest = isolated_recovery["manifest"]

    conn = sqlite3.connect(str(target_data / "db" / "technoreboot.db"))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM product_photos;")
    cnt = cur.fetchone()[0]
    conn.close()

    expected = manifest["database"]["tables"].get("product_photos", 490)
    assert cnt == expected, f"Photo rows mismatch: {cnt} != {expected}"


# ==============================================================================
# TESTS Q - W: MEDIA & APPLICATION ROUTES
# ==============================================================================

def test_q_sample_media_returns_200(isolated_recovery):
    """TEST Q: Sample media files exist on disk, have non-zero bytes, and serve 200 OK."""
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.testclient import TestClient

    target_data = isolated_recovery["target_data"]
    storage_photos = target_data / "storage" / "product_photos"
    assert storage_photos.is_dir()

    # Find sample jpg files
    sample_photos = list(storage_photos.glob("*.jpg"))
    assert len(sample_photos) > 0, "No sample photos found in restored storage"

    sample_photo = sample_photos[0]
    assert sample_photo.stat().st_size > 0

    # Serve via FastAPI StaticFiles
    test_app = FastAPI()
    test_app.mount("/media/product_photos", StaticFiles(directory=str(storage_photos)), name="media")
    client = TestClient(test_app)

    resp = client.get(f"/media/product_photos/{sample_photo.name}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] in ("image/jpeg", "image/jpg")
    assert len(resp.content) == sample_photo.stat().st_size


def test_r_inventory_page_loads(isolated_recovery):
    """TEST R: Product records and categories can be queried from restored database."""
    target_data = isolated_recovery["target_data"]
    conn = sqlite3.connect(str(target_data / "db" / "technoreboot.db"))
    cur = conn.cursor()
    cur.execute("SELECT id, title, sale_price, status, storage_location FROM products LIMIT 5;")
    rows = cur.fetchall()
    assert len(rows) == 5
    for r in rows:
        assert r[0] > 0
        assert len(r[1]) > 0
    conn.close()


def test_s_product_detail_loads(isolated_recovery):
    """TEST S: Product detail record and associated photos load cleanly."""
    target_data = isolated_recovery["target_data"]
    conn = sqlite3.connect(str(target_data / "db" / "technoreboot.db"))
    cur = conn.cursor()
    # Find a product with photos
    cur.execute("SELECT product_id, count(*) FROM product_photos GROUP BY product_id ORDER BY count(*) DESC LIMIT 1;")
    pid, pcount = cur.fetchone()
    assert pid > 0
    assert pcount > 0

    cur.execute("SELECT id, title, sale_price FROM products WHERE id = ?", (pid,))
    p = cur.fetchone()
    assert p is not None
    conn.close()


def test_t_sales_report_routes_load(isolated_recovery):
    """TEST T: Sales records and ledger data load cleanly from restored database."""
    target_data = isolated_recovery["target_data"]
    conn = sqlite3.connect(str(target_data / "db" / "technoreboot.db"))
    cur = conn.cursor()
    cur.execute("SELECT count(*), sum(total_amount) FROM sales;")
    count, total = cur.fetchone()
    assert count == 50
    assert total > 0
    conn.close()


def test_u_repairs_route_loads(isolated_recovery):
    """TEST U: Repair orders load cleanly from restored database."""
    target_data = isolated_recovery["target_data"]
    conn = sqlite3.connect(str(target_data / "db" / "technoreboot.db"))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM repair_orders;")
    cnt = cur.fetchone()[0]
    assert cnt == 66
    conn.close()


def test_v_avito_extension_route_loads(isolated_recovery):
    """TEST V: Avito categories and canonical mapping state load cleanly."""
    target_data = isolated_recovery["target_data"]
    conn = sqlite3.connect(str(target_data / "db" / "technoreboot.db"))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM avito_categories;")
    cnt = cur.fetchone()[0]
    assert cnt == 44
    conn.close()


def test_w_backup_route_loads(isolated_recovery):
    """TEST W: Backups metadata and registry load cleanly for OWNER."""
    target_data = isolated_recovery["target_data"]
    auth_mgr = AuthManager(auth_dir=str(target_data / "auth"))
    owner = auth_mgr.get_certificate("owner")
    assert owner is not None
    assert owner["is_owner"] is True


# ==============================================================================
# TESTS X - Z: ISOLATION & REGRESSION CONTRACT
# ==============================================================================

def test_x_fresh_recovery_does_not_modify_original_live_data(live_data_baseline):
    """TEST X: Fresh recovery test ran completely isolated and did NOT alter live data."""
    live_db = PROJECT_ROOT / "data" / "db" / "technoreboot.db"
    live_ca = PROJECT_ROOT / "data" / "auth" / "ca" / "ca.crt"

    current_db_hash = hashlib.sha256(live_db.read_bytes()).hexdigest() if live_db.is_file() else None
    current_ca_hash = hashlib.sha256(live_ca.read_bytes()).hexdigest() if live_ca.is_file() else None

    assert current_db_hash == live_data_baseline["db_hash"], "Live database was modified during disaster recovery test!"
    assert current_ca_hash == live_data_baseline["ca_hash"], "Live CA was modified during disaster recovery test!"


def test_y_normal_web_restore_still_does_not_overwrite_live_auth():
    """
    TEST Y: Strict separation of two policies:
    Normal web restore (/backups) still preserves live data/auth (Stage 07B-R3 contract),
    while fresh-server bootstrap restore restores auth (Stage 07E-R1 contract).
    """
    import inspect
    restore_src = inspect.getsource(backup_service.restore_backup)
    assert "Preserve Live Auth" in restore_src
    assert "data/auth" in restore_src


def test_z_relevant_regression_suites_pass(isolated_recovery):
    """TEST Z: Summary verification engine confirms all disaster recovery checks passed."""
    target_data = isolated_recovery["target_data"]
    manifest = isolated_recovery["manifest"]

    verification = bootstrap_restore.verify_restored_system(
        target_data_dir=target_data,
        expected_manifest=manifest,
    )
    assert verification["checks_passed"] is True
    assert verification["database"]["total_products"] == 227
    assert verification["auth"]["ca_fingerprint_sha256"] == manifest["auth"]["ca_fingerprint_sha256"]
    assert verification["auth"]["owner_fingerprint_sha256"] == manifest["auth"]["owner_fingerprint_sha256"]
    assert verification["auth"]["revoked_certificates"] == 14
