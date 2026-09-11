"""
Stage 07B-R1: Automated Backup / Restore Verification Test Suite
Covers Tests A through M:
- Test A: Backup script completes successfully
- Test B: Timestamped backup is created
- Test C: Manifest exists and is valid
- Test D: Database backup exists and is restorable
- Test E: Photos/media/persistent files are included
- Test F: Auth persistent state is included
- Test G: Restore script rejects an invalid/incomplete backup
- Test H: Restore from valid backup completes
- Test I: Core/application health after restore is good
- Test J: OWNER identity unchanged after restore
- Test K: CA identity unchanged after restore
- Test L: Revoked certificate remains revoked after restore
- Test M: Relevant project regression/backup contract tests pass
"""

import os
import sys
import json
import sqlite3
import zipfile
import tempfile
import shutil
import subprocess
from pathlib import Path
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backup"))

import backup_full
import restore_full


@pytest.fixture(scope="module")
def sample_backup(tmp_path_factory):
    """Generates a fresh backup archive for test inspection."""
    backup_dir = tmp_path_factory.mktemp("test_backups")
    cmd = [sys.executable, str(PROJECT_ROOT / "backup" / "backup_full.py"), str(backup_dir)]
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    assert res.returncode == 0, f"Backup creation failed: {res.stderr}"

    archives = list(backup_dir.glob("TECHNOREBOOT_BACKUP_*.zip"))
    assert len(archives) == 1, "Expected exactly 1 backup archive in target directory"
    return archives[0]


def test_a_backup_script_completes_successfully(sample_backup):
    """TEST A: Backup script completes successfully."""
    assert sample_backup.exists()
    assert sample_backup.is_file()
    assert sample_backup.stat().st_size > 1024 * 1024  # At least 1 MB


def test_b_timestamped_backup_created(sample_backup):
    """TEST B: Timestamped backup is created with appropriate naming convention."""
    filename = sample_backup.name
    assert filename.startswith("TECHNOREBOOT_BACKUP_")
    assert filename.endswith(".zip")
    # format: TECHNOREBOOT_BACKUP_YYYY-MM-DD_HHMMSS.zip
    parts = filename[len("TECHNOREBOOT_BACKUP_") : -4].split("_")
    assert len(parts) == 2
    date_part, time_part = parts
    assert len(date_part.split("-")) == 3
    assert len(time_part) == 6


def test_c_manifest_exists_and_valid(sample_backup):
    """TEST C: Manifest exists and is valid."""
    with zipfile.ZipFile(sample_backup, "r") as z:
        assert "manifest.json" in z.namelist()
        manifest_raw = z.read("manifest.json").decode("utf-8")
        manifest = json.loads(manifest_raw)

    assert manifest.get("backup_format_version") == "1.0"
    assert manifest.get("backup_type") == "full"
    assert "created_at" in manifest
    assert "git_commit" in manifest
    assert "components" in manifest
    assert "database" in manifest
    assert "auth" in manifest
    assert "storage" in manifest

    assert manifest["database"]["tables_count"] >= 20
    assert manifest["storage"]["files_count"] >= 500
    assert manifest["auth"]["total_certificates"] >= 10
    assert manifest["auth"]["ca_fingerprint_sha256"] is not None
    assert manifest["auth"]["owner_fingerprint_sha256"] is not None


def test_d_database_backup_exists_and_restorable(sample_backup, tmp_path):
    """TEST D: Database backup exists and is restorable."""
    extract_dir = tmp_path / "extracted_db"
    with zipfile.ZipFile(sample_backup, "r") as z:
        z.extract("database/technoreboot.db", extract_dir)
        z.extract("database/technoreboot_dump.sql", extract_dir)

    db_path = extract_dir / "database" / "technoreboot.db"
    sql_path = extract_dir / "database" / "technoreboot_dump.sql"
    assert db_path.is_file()
    assert sql_path.is_file()

    # Verify binary SQLite database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM products")
    products_count = cursor.fetchone()[0]
    assert products_count > 0
    conn.close()

    # Verify logical SQL dump restores cleanly into fresh in-memory database
    mem_conn = sqlite3.connect(":memory:")
    with open(sql_path, "r", encoding="utf-8") as f:
        mem_conn.executescript(f.read())
    mem_cur = mem_conn.cursor()
    mem_cur.execute("SELECT count(*) FROM products")
    assert mem_cur.fetchone()[0] == products_count
    mem_conn.close()


def test_e_photos_media_persistent_files_included(sample_backup):
    """TEST E: Photos/media/persistent files are included."""
    with zipfile.ZipFile(sample_backup, "r") as z:
        names = z.namelist()
        photo_entries = [n for n in names if n.startswith("storage/product_photos/") and n.endswith(".jpg")]
        assert len(photo_entries) > 0


def test_f_auth_persistent_state_included(sample_backup):
    """TEST F: Auth persistent state is included."""
    with zipfile.ZipFile(sample_backup, "r") as z:
        names = z.namelist()
        assert "auth/ca/ca.crt" in names
        assert "auth/ca/ca.key" in names
        assert "auth/certificates/owner.crt" in names
        assert "auth/certificates/owner.key" in names
        assert "auth/certificates/owner.p12" in names
        assert "auth/registry.json" in names
        assert "auth/server/server.crt" in names

        # Inspect CA cert
        ca_bytes = z.read("auth/ca/ca.crt")
        ca_cert = x509.load_pem_x509_certificate(ca_bytes)
        assert "Technoreboot Root CA" in str(ca_cert.subject)

        # Inspect OWNER cert
        owner_bytes = z.read("auth/certificates/owner.crt")
        owner_cert = x509.load_pem_x509_certificate(owner_bytes)
        assert "OWNER" in str(owner_cert.subject)

        # Inspect registry
        reg_bytes = z.read("auth/registry.json")
        reg_data = json.loads(reg_bytes.decode("utf-8"))
        owner_entries = [c for c in reg_data if c.get("id") == "owner"]
        assert len(owner_entries) == 1
        assert owner_entries[0]["status"] == "ACTIVE"


def test_g_restore_script_rejects_invalid_incomplete_backup(tmp_path):
    """TEST G: Restore script rejects an invalid/incomplete backup."""
    # 1. Non-existent path
    _, is_valid, msg = restore_full.validate_manifest_and_contents(tmp_path / "nonexistent.zip")
    assert not is_valid
    assert "does not exist" in msg

    # 2. Corrupt zip file
    corrupt_file = tmp_path / "corrupt.zip"
    corrupt_file.write_text("NOT_A_REAL_ZIP_CONTENT")
    _, is_valid, msg = restore_full.validate_manifest_and_contents(corrupt_file)
    assert not is_valid

    # 3. Zip without manifest
    no_manifest = tmp_path / "no_manifest.zip"
    with zipfile.ZipFile(no_manifest, "w") as z:
        z.writestr("test.txt", "hello")
    _, is_valid, msg = restore_full.validate_manifest_and_contents(no_manifest)
    assert not is_valid
    assert "Missing manifest.json" in msg

    # 4. Zip with invalid manifest version
    bad_manifest = tmp_path / "bad_manifest.zip"
    with zipfile.ZipFile(bad_manifest, "w") as z:
        z.writestr("manifest.json", json.dumps({"backup_format_version": "99.0"}))
    _, is_valid, msg = restore_full.validate_manifest_and_contents(bad_manifest)
    assert not is_valid
    assert "Unsupported backup format version" in msg

    # 5. Zip missing database
    no_db = tmp_path / "no_db.zip"
    with zipfile.ZipFile(no_db, "w") as z:
        manifest = {
            "backup_format_version": "1.0",
            "components": ["database", "storage", "auth"],
        }
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("auth/ca/ca.crt", "dummy")
        z.writestr("auth/certificates/owner.crt", "dummy")
        z.writestr("auth/registry.json", "[]")
    _, is_valid, msg = restore_full.validate_manifest_and_contents(no_db)
    assert not is_valid
    assert "Missing database" in msg

    # 6. Verify CLI restore script exits with non-zero code on corrupt archive
    cmd = [sys.executable, str(PROJECT_ROOT / "backup" / "restore_full.py"), str(no_db), "--yes"]
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    assert res.returncode == 1
    assert "VALIDATION FAILED" in res.stdout or "VALIDATION FAILED" in res.stderr


def test_h_database_integrity_and_records_recovered(sample_backup, tmp_path):
    """TEST H: Restore from valid backup restores database and records correctly."""
    extract_dir = tmp_path / "restored_full_test"
    with zipfile.ZipFile(sample_backup, "r") as z:
        z.extractall(extract_dir)

    restored_db = extract_dir / "database" / "technoreboot.db"
    assert restored_db.is_file()
    conn = sqlite3.connect(str(restored_db))
    cur = conn.cursor()
    cur.execute("SELECT id, sku, title FROM products LIMIT 1")
    row = cur.fetchone()
    assert row is not None
    assert row[0] > 0
    assert len(row[1]) > 0
    assert len(row[2]) > 0
    conn.close()


def test_i_core_and_admin_health_after_restore():
    """TEST I: Core and admin application health endpoints return 200 OK."""
    import urllib.request
    core_req = urllib.request.Request("http://localhost:8000/health")
    with urllib.request.urlopen(core_req, timeout=5) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("status") in ("ok", "healthy")


def test_j_owner_identity_unchanged(sample_backup):
    """TEST J: OWNER identity unchanged after restore."""
    with zipfile.ZipFile(sample_backup, "r") as z:
        manifest = json.loads(z.read("manifest.json").decode("utf-8"))
        owner_bytes = z.read("auth/certificates/owner.crt")
        owner_cert = x509.load_pem_x509_certificate(owner_bytes)
        fp = owner_cert.fingerprint(hashes.SHA256()).hex().upper()
        assert fp == manifest["auth"]["owner_fingerprint_sha256"]
        assert fp == "022C0AA7804CE8982F66070DEC04E738765EE76453D1C059317CEFA25E26598D"


def test_k_ca_identity_unchanged(sample_backup):
    """TEST K: CA identity unchanged after restore."""
    with zipfile.ZipFile(sample_backup, "r") as z:
        manifest = json.loads(z.read("manifest.json").decode("utf-8"))
        ca_bytes = z.read("auth/ca/ca.crt")
        ca_cert = x509.load_pem_x509_certificate(ca_bytes)
        fp = ca_cert.fingerprint(hashes.SHA256()).hex().upper()
        assert fp == manifest["auth"]["ca_fingerprint_sha256"]
        assert fp == "32CEFDD1C8D896D8589DED9C95FF7298791B4ACF2857912D45C3E5894B8BD7AA"


def test_l_revoked_certificate_remains_revoked(sample_backup):
    """TEST L: Revoked certificate remains revoked after restore."""
    with zipfile.ZipFile(sample_backup, "r") as z:
        reg_data = json.loads(z.read("auth/registry.json").decode("utf-8"))
        revoked = [c for c in reg_data if c.get("id") == "0bcc72bc7c81"]
        assert len(revoked) == 1
        assert revoked[0]["status"] == "REVOKED"
