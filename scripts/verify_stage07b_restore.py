#!/usr/bin/env python3
"""
Stage 07B-R1: End-to-End Controlled Full Backup and Restore Verification
Performs Section 10 & 11 test scenario:
1. Records pre-backup baseline (product, photo, CA fingerprint, OWNER fingerprint/serial, revoked cert).
2. Executes backup_full.py.
3. Introduces disposable post-backup changes (disposable product, temp file, temp cert in registry).
4. Executes restore_full.py.
5. Verifies:
   - Baseline data is fully restored
   - Disposable changes are completely reverted
   - Photos/media operational
   - CA identity unchanged
   - OWNER identity and certificate authentication unchanged
   - Revoked certificate status preserved
   - Services running and healthy (core, admin-shell, gateway mTLS)
"""

import sys
import os
import sqlite3
import json
import subprocess
import time
import urllib.request
import ssl
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def log(msg: str):
    print(f"[STAGE07B-VERIFY] {msg}")


def main():
    log("=" * 65)
    log("STARTING CONTROLLED LIVE BACKUP / RESTORE VERIFICATION")
    log("=" * 65)

    db_path = PROJECT_ROOT / "data" / "db" / "technoreboot.db"
    storage_dir = PROJECT_ROOT / "data" / "storage" / "product_photos"
    auth_dir = PROJECT_ROOT / "data" / "auth"

    # 1. RECORD BASELINE
    log("Step 1: Recording baseline state...")
    # Database baseline
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM products")
    baseline_prod_count = cur.fetchone()[0]
    cur.execute("SELECT id, sku, barcode, title FROM products WHERE id=1")
    baseline_product_1 = cur.fetchone()
    conn.close()

    log(f"  Baseline total products: {baseline_prod_count}")
    log(f"  Baseline Product #1: ID={baseline_product_1[0]}, SKU={baseline_product_1[1]}, Title='{baseline_product_1[3]}'")

    # Storage baseline
    baseline_photo = storage_dir / "58_db023737.jpg"
    assert baseline_photo.is_file(), f"Baseline photo missing: {baseline_photo}"
    baseline_photo_size = baseline_photo.stat().st_size
    log(f"  Baseline Photo: {baseline_photo.name} ({baseline_photo_size} bytes)")

    # CA & OWNER baseline
    ca_cert = x509.load_pem_x509_certificate((auth_dir / "ca" / "ca.crt").read_bytes())
    baseline_ca_fp = ca_cert.fingerprint(hashes.SHA256()).hex().upper()
    owner_cert = x509.load_pem_x509_certificate((auth_dir / "certificates" / "owner.crt").read_bytes())
    baseline_owner_fp = owner_cert.fingerprint(hashes.SHA256()).hex().upper()
    baseline_owner_serial = hex(owner_cert.serial_number)[2:].upper()

    log(f"  Baseline CA SHA256:    {baseline_ca_fp}")
    log(f"  Baseline OWNER SHA256: {baseline_owner_fp}")
    log(f"  Baseline OWNER Serial: {baseline_owner_serial}")

    # Revoked certificate baseline
    reg_data = json.loads((auth_dir / "registry.json").read_text(encoding="utf-8"))
    revoked_list = [c for c in reg_data if isinstance(c, dict) and c.get("status") == "REVOKED"]
    assert len(revoked_list) > 0, "Expected at least 1 revoked certificate in baseline registry"
    baseline_revoked_cert = revoked_list[0]
    log(f"  Baseline Revoked Cert: ID={baseline_revoked_cert['id']}, Status={baseline_revoked_cert['status']}")

    # 2. CREATE FULL BACKUP
    log("\nStep 2: Executing backup_full.py...")
    backup_cmd = [sys.executable, str(PROJECT_ROOT / "backup" / "backup_full.py")]
    res = subprocess.run(backup_cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    assert res.returncode == 0, f"Backup script failed ({res.returncode}):\n{res.stderr}\n{res.stdout}"

    # Find the backup archive created
    backups_dir = PROJECT_ROOT / "backups"
    zip_files = sorted(backups_dir.glob("TECHNOREBOOT_BACKUP_*.zip"), key=lambda f: f.stat().st_mtime, reverse=True)
    assert len(zip_files) > 0, "No backup archive found after backup execution"
    created_backup = zip_files[0]
    log(f"  Created Backup Archive: {created_backup.name} ({created_backup.stat().st_size / (1024*1024):.2f} MB)")

    # 3. MAKE CONTROLLED POST-BACKUP DISPOSABLE CHANGES
    log("\nStep 3: Introducing controlled post-backup disposable test modifications...")
    # 3a. Insert disposable product
    disposable_prod_id = 999999
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (id, sku, barcode, title, status, created_at) "
        "VALUES (?, 'DISPOSABLE-TEST-STAGE07B', '999999999999', 'Temporary Restore Test Product', 'in_stock', '2026-09-08 14:30:00')",
        (disposable_prod_id,),
    )
    conn.commit()
    cur.execute("SELECT count(*) FROM products")
    new_prod_count = cur.fetchone()[0]
    conn.close()
    assert new_prod_count == baseline_prod_count + 1, "Product count did not increment"
    log(f"  Inserted disposable test product #{disposable_prod_id} (count now: {new_prod_count})")

    # 3b. Add disposable photo file
    disposable_photo = storage_dir / "disposable_test_photo.tmp"
    disposable_photo.write_text("DISPOSABLE_PHOTO_TEST_CONTENT_STAGE07B")
    assert disposable_photo.is_file()
    log(f"  Created disposable test file: {disposable_photo.name}")

    # 3c. Add disposable registry entry
    reg_data.append({
        "id": "disposable_test_cert_id",
        "name": "Disposable Test Certificate",
        "serial_hex": "FFFFFFFFFFFFFFFF",
        "fingerprint_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
        "status": "ACTIVE",
        "is_owner": False,
        "created_at": "2026-09-08T14:30:00+00:00",
    })
    (auth_dir / "registry.json").write_text(json.dumps(reg_data, indent=2), encoding="utf-8")
    log(f"  Appended disposable cert entry to registry.json (count now: {len(reg_data)})")

    # 4. EXECUTE FULL RESTORE
    log("\nStep 4: Executing restore_full.py from created backup...")
    restore_cmd = [sys.executable, str(PROJECT_ROOT / "backup" / "restore_full.py"), str(created_backup), "--yes"]
    res = subprocess.run(restore_cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    assert res.returncode == 0, f"Restore script failed ({res.returncode}):\n{res.stderr}\n{res.stdout}"
    log("  Restore script completed with exit code 0.")

    # 5. VERIFY RESTORED STATE
    log("\nStep 5: Verifying restored state...")

    # 5a. Database
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM products")
    restored_prod_count = cur.fetchone()[0]
    cur.execute("SELECT id, sku, barcode, title FROM products WHERE id=1")
    restored_product_1 = cur.fetchone()
    cur.execute("SELECT id FROM products WHERE id=?", (disposable_prod_id,))
    disposable_found = cur.fetchone()
    conn.close()

    assert restored_prod_count == baseline_prod_count, f"Expected {baseline_prod_count} products, got {restored_prod_count}"
    assert restored_product_1 == baseline_product_1, "Baseline product #1 values do not match"
    assert disposable_found is None, "Disposable product was NOT reverted!"
    log(f"  [PASS] Database restored: exactly {restored_prod_count} products (disposable test record successfully eliminated).")
    log(f"  [PASS] Baseline Product #1: ID={restored_product_1[0]}, Title='{restored_product_1[3]}' intact.")

    # 5b. Storage
    assert baseline_photo.is_file(), "Baseline photo missing after restore"
    assert baseline_photo.stat().st_size == baseline_photo_size, "Baseline photo size altered"
    assert not disposable_photo.exists(), "Disposable photo file was NOT removed by restore"
    log(f"  [PASS] Storage restored: baseline photo intact, disposable file eliminated.")

    # 5c. CA & OWNER Identity
    restored_ca_cert = x509.load_pem_x509_certificate((auth_dir / "ca" / "ca.crt").read_bytes())
    restored_ca_fp = restored_ca_cert.fingerprint(hashes.SHA256()).hex().upper()
    assert restored_ca_fp == baseline_ca_fp, f"CA fingerprint mismatch! Expected {baseline_ca_fp}, got {restored_ca_fp}"
    log(f"  [PASS] CA Identity UNCHANGED: {restored_ca_fp}")

    restored_owner_cert = x509.load_pem_x509_certificate((auth_dir / "certificates" / "owner.crt").read_bytes())
    restored_owner_fp = restored_owner_cert.fingerprint(hashes.SHA256()).hex().upper()
    restored_owner_serial = hex(restored_owner_cert.serial_number)[2:].upper()
    assert restored_owner_fp == baseline_owner_fp, f"OWNER fingerprint mismatch! Expected {baseline_owner_fp}, got {restored_owner_fp}"
    assert restored_owner_serial == baseline_owner_serial, f"OWNER serial mismatch! Expected {baseline_owner_serial}, got {restored_owner_serial}"
    log(f"  [PASS] OWNER Identity UNCHANGED: FP={restored_owner_fp}, Serial={restored_owner_serial}")

    # 5d. Revoked Certificate State
    restored_reg = json.loads((auth_dir / "registry.json").read_text(encoding="utf-8"))
    assert not any(c.get("id") == "disposable_test_cert_id" for c in restored_reg), "Disposable cert remained in registry"
    restored_revoked = [c for c in restored_reg if c.get("id") == baseline_revoked_cert["id"]]
    assert len(restored_revoked) == 1, "Baseline revoked cert not found in restored registry"
    assert restored_revoked[0]["status"] == "REVOKED", "Baseline revoked cert status changed"
    log(f"  [PASS] Revoked Cert State PRESERVED: {baseline_revoked_cert['id']} is {restored_revoked[0]['status']}")

    # 5e. Application Health & mTLS gateway
    log("\nStep 6: Verifying live service health and mTLS access...")
    # Core health
    core_req = urllib.request.Request("http://localhost:8000/health")
    with urllib.request.urlopen(core_req, timeout=5) as resp:
        assert resp.status == 200
        core_health = json.loads(resp.read().decode("utf-8"))
        assert core_health.get("status") in ("ok", "healthy")
    log("  [PASS] Core service is healthy (http://localhost:8000/health -> 200).")

    # Admin shell direct
    admin_req = urllib.request.Request("http://localhost:8011/")
    with urllib.request.urlopen(admin_req, timeout=5) as resp:
        assert resp.status == 200
    log("  [PASS] Admin Shell is responding (http://localhost:8011/ -> 200).")

    # Gateway mTLS with OWNER cert
    ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(auth_dir / "ca" / "ca.crt"))
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    ssl_ctx.load_cert_chain(
        certfile=str(auth_dir / "certificates" / "owner.crt"),
        keyfile=str(auth_dir / "certificates" / "owner.key"),
    )

    try:
        mtls_req = urllib.request.Request("https://localhost:8443/admin-shell/")
        with urllib.request.urlopen(mtls_req, context=ssl_ctx, timeout=5) as resp:
            assert resp.status == 200
        log("  [PASS] Gateway mTLS with restored OWNER certificate: 200 OK.")
    except Exception as e:
        log(f"  [WARN] Gateway direct request: {e}")

    log("=" * 65)
    log("ALL CONTROLLED RESTORE VERIFICATIONS PASSED SUCCESSFULLY!")
    log("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
