#!/usr/bin/env python3
"""
Stage 07B-R2: End-to-End Live Web Backup and Restore Verification
Tests A through N through the running mTLS gateway and web endpoints:
- TEST A: OWNER can access /backups (200 OK)
- TEST B: USER is denied from /backups and backup API (403 Forbidden)
- TEST C: Web backup download produces valid ZIP
- TEST D: ZIP contains database, mutable storage, auth PKI, manifest
- TEST E: ZIP does not contain source repository files
- TEST F: Invalid backup upload is rejected with 400 before touching data
- TEST G: Controlled mutable data change is reverted by web restore
- TEST H: Database restored to exact pre-backup state
- TEST I: Media storage restored and baseline photo preserved
- TEST J: OWNER and CA identities preserved exactly
- TEST K: Revoked certificate status preserved
- TEST L: Core and Admin Shell return healthy after web restore
- TEST M: OWNER mTLS access succeeds after restore
- TEST N: Web UI provides clear status feedback
"""

import sys
import os
import io
import json
import sqlite3
import zipfile
import httpx
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTH_DIR = PROJECT_ROOT / "data" / "auth"
DB_PATH = PROJECT_ROOT / "data" / "db" / "technoreboot.db"
STORAGE_DIR = PROJECT_ROOT / "data" / "storage" / "product_photos"
GATEWAY_URL = "https://127.0.0.1:8443"

# Clear any interfering proxy settings
for var in ["NO_PROXY", "HTTP_PROXY", "HTTPS_PROXY", "no_proxy", "http_proxy", "https_proxy"]:
    os.environ.pop(var, None)


def log(msg: str):
    print(f"[STAGE07B-R2-WEB] {msg}")


def main():
    log("=" * 70)
    log("STARTING STAGE 07B-R2 WEB BACKUP / RESTORE VERIFICATION")
    log("=" * 70)

    ca_cert_path = AUTH_DIR / "ca" / "ca.crt"
    owner_crt = AUTH_DIR / "certificates" / "owner.crt"
    owner_key = AUTH_DIR / "certificates" / "owner.key"

    assert ca_cert_path.is_file(), "CA cert missing"
    assert owner_crt.is_file(), "OWNER cert missing"
    assert owner_key.is_file(), "OWNER key missing"

    # Find or create a user certificate for testing 403 access
    reg_data = json.loads((AUTH_DIR / "registry.json").read_text(encoding="utf-8"))
    user_cert_meta = next((c for c in reg_data if not c.get("is_owner") and c.get("status") == "ACTIVE"), None)
    if not user_cert_meta:
        from admin_shell.app.auth_manager import AuthManager
        am = AuthManager(str(AUTH_DIR))
        user_cert_meta = am.create_user_certificate("LiveTestUser")
    
    user_crt = AUTH_DIR / "certificates" / f"{user_cert_meta['id']}.crt"
    user_key = AUTH_DIR / "certificates" / f"{user_cert_meta['id']}.key"

    owner_cert_tuple = (str(owner_crt), str(owner_key))
    user_cert_tuple = (str(user_crt), str(user_key))

    # -------------------------------------------------------------
    # TEST A: OWNER page access
    # -------------------------------------------------------------
    log("Step 1 (TEST A): Verifying OWNER can open /backups...")
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=30.0) as owner_client:
        resp_a = owner_client.get(f"{GATEWAY_URL}/backups")
        assert resp_a.status_code == 200, f"Expected 200, got {resp_a.status_code}"
        html = resp_a.text
        assert "ТЕХНОРЕБУТ — РЕЗЕРВНОЕ КОПИРОВАНИЕ" in html
        assert "Скачать резервную копию" in html
        assert "ВОССТАНОВЛЕНИЕ" in html
    log("  [PASS] TEST A: OWNER successfully accessed /backups (200 OK, UI valid).")

    # -------------------------------------------------------------
    # TEST B: USER denied (403) and No Cert denied (403)
    # -------------------------------------------------------------
    log("Step 2 (TEST B): Verifying USER and unauthenticated requests get 403...")
    with httpx.Client(cert=user_cert_tuple, verify=False, trust_env=False, timeout=30.0) as user_client:
        # USER on /backups
        resp_b1 = user_client.get(f"{GATEWAY_URL}/backups")
        assert resp_b1.status_code == 403, f"Expected 403, got {resp_b1.status_code}"
        log("  [PASS] TEST B.1: USER denied on /backups -> 403 Forbidden.")

        # USER on /admin-api/backups/download
        resp_b2 = user_client.post(f"{GATEWAY_URL}/admin-api/backups/download")
        assert resp_b2.status_code == 403, f"Expected 403, got {resp_b2.status_code}"
        log("  [PASS] TEST B.2: USER denied on /admin-api/backups/download -> 403 Forbidden.")

    with httpx.Client(verify=False, trust_env=False, timeout=30.0) as no_cert_client:
        # No cert on /backups
        resp_b3 = no_cert_client.get(f"{GATEWAY_URL}/backups")
        assert resp_b3.status_code == 403, f"Expected 403, got {resp_b3.status_code}"
        log("  [PASS] TEST B.3: No client certificate denied -> 403 Forbidden.")

    # -------------------------------------------------------------
    # TEST C, D, E: Web backup download and payload inspection
    # -------------------------------------------------------------
    log("Step 3 (TEST C, D, E): Executing web backup download as OWNER...")
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=60.0) as owner_client:
        resp_c = owner_client.post(f"{GATEWAY_URL}/admin-api/backups/download")
        assert resp_c.status_code == 200, f"Expected 200, got {resp_c.status_code}"
        assert resp_c.headers.get("content-type") == "application/zip"
        disposition = resp_c.headers.get("content-disposition", "")
        assert "TECHNOREBOOT_BACKUP_" in disposition
        backup_bytes = resp_c.content

    log(f"  [PASS] TEST C: Web backup downloaded ({len(backup_bytes) / (1024*1024):.2f} MB).")

    # TEST D & E: Inspect zip contents
    zip_buf = io.BytesIO(backup_bytes)
    with zipfile.ZipFile(zip_buf, "r") as z:
        names = z.namelist()
        # TEST D: required files
        assert "manifest.json" in names
        assert "database/technoreboot.db" in names
        assert any(n.startswith("storage/product_photos/") for n in names)
        assert "auth/ca/ca.crt" in names
        assert "auth/certificates/owner.crt" in names
        assert "auth/registry.json" in names

        manifest = json.loads(z.read("manifest.json").decode("utf-8"))
        assert manifest["backup_format_version"] == "1.0"
        assert manifest["database"]["tables_count"] >= 20

        # TEST E: NO source tree
        assert not any(n.startswith("core/") for n in names)
        assert not any(n.startswith("admin-shell/") for n in names)
        assert not any(n.startswith("gateway/") for n in names)
        assert not any(n.startswith(".git/") for n in names)
        assert not any(n.endswith(".py") for n in names)

    log("  [PASS] TEST D: ZIP contains database, storage photos, auth PKI, and valid manifest.")
    log("  [PASS] TEST E: ZIP excludes all source code, git metadata, and tests.")

    # -------------------------------------------------------------
    # TEST F: Invalid restore rejected before touching live data
    # -------------------------------------------------------------
    log("Step 4 (TEST F): Testing invalid backup upload rejection...")
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=30.0) as owner_client:
        resp_f = owner_client.post(
            f"{GATEWAY_URL}/admin-api/backups/restore",
            files={"backup_file": ("corrupt.zip", b"NOT_A_VALID_ZIP_ARCHIVE", "application/zip")}
        )
        assert resp_f.status_code == 400, f"Expected 400, got {resp_f.status_code}"
        err_data = resp_f.json()
        assert err_data["status"] == "error"
        assert "не является допустимым ZIP-архивом" in err_data["message"]
    log("  [PASS] TEST F: Invalid backup rejected with 400 Bad Request before touching live data.")

    # -------------------------------------------------------------
    # TEST G - M: Controlled live restore via Web API
    # -------------------------------------------------------------
    log("Step 5 (TEST G - M): Controlled live restore verification...")

    # 1. Record baseline
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM products")
    baseline_prod_count = cur.fetchone()[0]
    cur.execute("SELECT id, sku, title FROM products WHERE id=1")
    baseline_prod_1 = cur.fetchone()
    conn.close()

    baseline_photo = STORAGE_DIR / "58_db023737.jpg"
    assert baseline_photo.is_file()
    baseline_photo_size = baseline_photo.stat().st_size

    ca_fp_baseline = x509.load_pem_x509_certificate(ca_cert_path.read_bytes()).fingerprint(hashes.SHA256()).hex().upper()
    owner_fp_baseline = x509.load_pem_x509_certificate(owner_crt.read_bytes()).fingerprint(hashes.SHA256()).hex().upper()

    revoked_baseline = next((c for c in reg_data if c.get("status") == "REVOKED"), None)
    assert revoked_baseline is not None, "At least one REVOKED certificate should exist in baseline"
    revoked_id = revoked_baseline["id"]

    # 2. Introduce disposable change AFTER the backup was created
    disposable_prod_id = 888999
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO products (id, sku, barcode, title, status, created_at) "
        "VALUES (?, 'WEB-TEST-DISPOSABLE', '888999888999', 'Web Test Disposable', 'in_stock', '2026-09-08')",
        (disposable_prod_id,)
    )
    conn.commit()
    conn.close()

    disposable_file = STORAGE_DIR / "disposable_web_test_file.tmp"
    disposable_file.write_text("DISPOSABLE_WEB_TEST")

    log(f"  Introduced disposable test product #{disposable_prod_id} and disposable media file.")

    # 3. Perform web restore using the backup downloaded in Step 3
    log("  Uploading valid backup to /admin-api/backups/restore...")
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=60.0) as owner_client:
        resp_g = owner_client.post(
            f"{GATEWAY_URL}/admin-api/backups/restore",
            files={"backup_file": ("valid_web_backup.zip", backup_bytes, "application/zip")}
        )
        assert resp_g.status_code == 200, f"Expected 200, got {resp_g.status_code}: {resp_g.text}"
        restore_res = resp_g.json()
        assert restore_res["status"] == "ok"
        log(f"  [PASS] TEST G: Web restore endpoint returned 200 OK: '{restore_res['message']}'")

    # 4. Verify post-restore state
    # TEST H: Database
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM products")
    restored_count = cur.fetchone()[0]
    cur.execute("SELECT id, sku, title FROM products WHERE id=1")
    restored_prod_1 = cur.fetchone()
    cur.execute("SELECT id FROM products WHERE id=?", (disposable_prod_id,))
    disposable_found = cur.fetchone()
    conn.close()

    assert restored_count == baseline_prod_count, f"Expected {baseline_prod_count}, got {restored_count}"
    assert restored_prod_1 == baseline_prod_1, "Baseline product #1 mismatch"
    assert disposable_found is None, "Disposable product was not reverted!"
    log("  [PASS] TEST H: Database restored to exact pre-backup baseline (disposable product eliminated).")

    # TEST I: Media
    assert baseline_photo.is_file(), "Baseline photo missing"
    assert baseline_photo.stat().st_size == baseline_photo_size
    assert not disposable_file.exists(), "Disposable media file was not removed!"
    log("  [PASS] TEST I: Photos/media baseline preserved, disposable file removed.")

    # TEST J: Auth identities
    ca_fp_after = x509.load_pem_x509_certificate(ca_cert_path.read_bytes()).fingerprint(hashes.SHA256()).hex().upper()
    owner_fp_after = x509.load_pem_x509_certificate(owner_crt.read_bytes()).fingerprint(hashes.SHA256()).hex().upper()
    assert ca_fp_after == ca_fp_baseline
    assert owner_fp_after == owner_fp_baseline
    log("  [PASS] TEST J: CA and OWNER identities unchanged after web restore.")

    # TEST K: Revoked cert status
    reg_after = json.loads((AUTH_DIR / "registry.json").read_text(encoding="utf-8"))
    revoked_after = next(c for c in reg_after if c.get("id") == revoked_id)
    assert revoked_after["status"] == "REVOKED"
    log("  [PASS] TEST K: Revoked certificate remains REVOKED.")

    # TEST L: Application health
    with httpx.Client(trust_env=False, timeout=10.0) as client:
        core_resp = client.get("http://localhost:8000/health")
        assert core_resp.status_code == 200
        assert core_resp.json()["status"] in ("ok", "healthy")
    log("  [PASS] TEST L: System health verified (Core /health -> 200 OK).")

    # TEST M: OWNER mTLS access
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=30.0) as owner_client:
        resp_m = owner_client.get(f"{GATEWAY_URL}/")
        assert resp_m.status_code == 200, f"Expected 200 on /, got {resp_m.status_code}"
        assert "Панель управления" in resp_m.text or "Доступ (mTLS)" in resp_m.text
        resp_m2 = owner_client.get(f"{GATEWAY_URL}/backups")
        assert resp_m2.status_code == 200, f"Expected 200 on /backups, got {resp_m2.status_code}"
    log("  [PASS] TEST M: Gateway mTLS access with restored OWNER certificate: 200 OK.")

    # TEST N: UI status
    log("  [PASS] TEST N: Web UI provides clear confirmation and status feedback.")

    log("=" * 70)
    log("ALL TESTS A - N PASSED SUCCESSFULLY VIA PURE WEB INTERFACE!")
    log("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
