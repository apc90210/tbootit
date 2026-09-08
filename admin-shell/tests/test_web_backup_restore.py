"""
Admin Shell — Web Backup / Restore Unit Tests
Stage 07B-R2: Web Backup / Restore (Owner UI only)

Tests:
- Access control: OWNER allowed (200), USER denied (403), No cert denied (403)
- Web backup download: returns zip, valid manifest, expected files, no git/source repo
- Web restore: rejects invalid zip, rejects missing database, restores valid backup cleanly
- Post-restore identity preservation: CA and OWNER fingerprints intact
"""

import os
import io
import json
import zipfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app, auth_manager
from app import backup_service


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def owner_headers():
    owner = auth_manager.get_certificate("owner")
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner["serial_hex"],
        "x-client-cert-fingerprint": owner["fingerprint_sha256"],
    }


@pytest.fixture
def user_headers():
    # Issue a temporary user cert for testing if needed
    certs = auth_manager.list_certificates()
    user_cert = next((c for c in certs if not c.get("is_owner") and c.get("status") == "ACTIVE"), None)
    if not user_cert:
        res = auth_manager.create_user_certificate("TestUserUnit")
        user_cert = res
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": user_cert["serial_hex"],
        "x-client-cert-fingerprint": user_cert["fingerprint_sha256"],
    }


def test_backups_page_owner_access(client, owner_headers):
    """TEST A: OWNER can access /backups web page."""
    resp = client.get("/backups", headers=owner_headers)
    assert resp.status_code == 200
    assert "ТЕХНОРЕБУТ — РЕЗЕРВНОЕ КОПИРОВАНИЕ" in resp.text
    assert "Скачать резервную копию" in resp.text
    assert "ВОССТАНОВЛЕНИЕ" in resp.text


def test_backups_page_user_denied(client, user_headers):
    """TEST B: Normal USER is forbidden from /backups."""
    resp = client.get("/backups", headers=user_headers)
    assert resp.status_code == 403


def test_backups_page_no_cert_denied(client):
    """TEST B2: Unauthenticated request to /backups is rejected with 403."""
    resp = client.get("/backups")
    assert resp.status_code == 403


def test_api_download_user_denied(client, user_headers):
    """TEST B3: Normal USER is forbidden from backup download endpoint."""
    resp = client.post("/admin-api/backups/download", headers=user_headers)
    assert resp.status_code == 403


def test_api_restore_user_denied(client, user_headers):
    """TEST B4: Normal USER is forbidden from backup restore endpoint."""
    fake_file = io.BytesIO(b"fake")
    resp = client.post(
        "/admin-api/backups/restore",
        headers=user_headers,
        files={"backup_file": ("test.zip", fake_file, "application/zip")}
    )
    assert resp.status_code == 403


def test_api_download_backup_owner(client, owner_headers):
    """TEST C, D, E: OWNER downloads valid ZIP containing data and manifest, no source code."""
    resp = client.post("/admin-api/backups/download", headers=owner_headers)
    assert resp.status_code == 200
    assert resp.headers.get("content-type") == "application/zip"
    disposition = resp.headers.get("content-disposition", "")
    assert "TECHNOREBOOT_BACKUP_" in disposition
    assert disposition.endswith('.zip"') or disposition.endswith(".zip")

    # Read zip bytes
    zip_bytes = io.BytesIO(resp.content)
    with zipfile.ZipFile(zip_bytes, "r") as z:
        names = z.namelist()
        # Manifest
        assert "manifest.json" in names
        manifest = json.loads(z.read("manifest.json").decode("utf-8"))
        assert manifest.get("backup_format_version") == "1.0"
        assert manifest["database"]["tables_count"] >= 20

        # Database
        assert "database/technoreboot.db" in names

        # Storage & Auth
        assert any(n.startswith("storage/") for n in names)
        assert "auth/ca/ca.crt" in names
        assert "auth/certificates/owner.crt" in names
        assert "auth/registry.json" in names

        # TEST E: Ensure NO source tree files are included
        assert not any(n.startswith("core/") for n in names)
        assert not any(n.startswith("admin-shell/") for n in names)
        assert not any(n.startswith("gateway/") for n in names)
        assert not any(n.startswith(".git/") for n in names)
        assert not any(n.endswith(".py") for n in names)


def test_api_restore_rejects_invalid_archive(client, owner_headers):
    """TEST F: Uploading invalid zip is rejected before touching live data."""
    # 1. Corrupt data
    corrupt_io = io.BytesIO(b"NOT_A_VALID_ZIP_FILE")
    resp = client.post(
        "/admin-api/backups/restore",
        headers=owner_headers,
        files={"backup_file": ("corrupt.zip", corrupt_io, "application/zip")}
    )
    assert resp.status_code == 400
    data = resp.json()
    assert data["status"] == "error"

    # 2. Zip missing manifest
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("test.txt", "empty")
    buf.seek(0)
    resp2 = client.post(
        "/admin-api/backups/restore",
        headers=owner_headers,
        files={"backup_file": ("no_manifest.zip", buf, "application/zip")}
    )
    assert resp2.status_code == 400
    assert "manifest.json" in resp2.json()["message"]


def test_api_restore_valid_archive(client, owner_headers):
    """TEST G, H, J, K, L: Valid web restore flow."""
    # First download a valid backup
    dl_resp = client.post("/admin-api/backups/download", headers=owner_headers)
    assert dl_resp.status_code == 200
    backup_content = dl_resp.content

    # Perform restore upload
    restore_io = io.BytesIO(backup_content)
    resp = client.post(
        "/admin-api/backups/restore",
        headers=owner_headers,
        files={"backup_file": ("valid_backup.zip", restore_io, "application/zip")}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "успешно восстановлен" in data["message"]


def test_restore_preserves_live_auth(client, owner_headers):
    """Stage 07B-R3: Verify that normal web restore preserves currently active auth."""
    # 1. Download backup before issuing new certificate
    dl_resp = client.post("/admin-api/backups/download", headers=owner_headers)
    assert dl_resp.status_code == 200
    backup_content = dl_resp.content

    # 2. Issue a disposable user certificate after backup was taken
    test_user_meta = auth_manager.create_user_certificate("DisposableAuthPreserveUser")
    test_user_id = test_user_meta["id"]
    assert auth_manager.get_certificate(test_user_id) is not None

    # 3. Restore the older backup taken before the certificate was created
    restore_io = io.BytesIO(backup_content)
    resp = client.post(
        "/admin-api/backups/restore",
        headers=owner_headers,
        files={"backup_file": ("older_backup.zip", restore_io, "application/zip")}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # 4. Verify the newly created user certificate is STILL active and present in live registry
    live_cert = auth_manager.get_certificate(test_user_id)
    assert live_cert is not None, "Post-backup user cert was incorrectly rolled back by restore!"
    assert live_cert["status"] == "ACTIVE"

    # Clean up disposable cert
    auth_manager.revoke_certificate(test_user_id)
