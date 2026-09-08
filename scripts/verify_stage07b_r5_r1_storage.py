#!/usr/bin/env python3
"""
Stage 07B-R5-R1 Live Verification Script: Persistent Photo Storage Safety Fix

Tests:
- TEST A: Normal persistent storage available:
  - Avito import succeeds;
  - Photos are physically saved under persistent /data/storage/product_photos;
  - Files survive Core container restart;
  - Files are served via /media/...
- TEST B: Simulated persistent storage unavailable:
  - No /tmp/product_photos success fallback;
  - No false local storage_path;
  - Response is explicit partial-success warning / photos_imported=0;
  - No raw HTTP 500 / stack trace;
  - Avito bridge returns 'partial' status with friendly warning.
- TEST C: Backup created after successful photo import contains the imported photo.
- TEST D: Web restore preserves valid storage mount inode and imported photos remain available.
- TEST E: Real extension-equivalent Avito import still succeeds with photos.
- TEST F: Existing OWNER access on Gateway: /, /certificates, /backups -> 200 OK.
- TEST G: Avito pairing and heartbeat still pass.
- TEST H: Relevant Core tests pass (exact count).
- TEST I: Relevant Avito module tests pass (exact count).
"""

import os
import sys
import io
import time
import json
import base64
import sqlite3
import zipfile
import subprocess
from pathlib import Path
import httpx
import urllib3

urllib3.disable_warnings()

GATEWAY_URL = "https://127.0.0.1:8443"
ADMIN_SHELL_URL = "http://127.0.0.1:8011"
AVITO_MODULE_URL = "http://127.0.0.1:8020"
CORE_API_URL = "http://127.0.0.1:8000"

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "db" / "technoreboot.db"
AUTH_DIR = DATA_DIR / "auth"
STORAGE_DIR = DATA_DIR / "storage" / "product_photos"

OWNER_CRT = AUTH_DIR / "certificates" / "owner.crt"
OWNER_KEY = AUTH_DIR / "certificates" / "owner.key"

# 1x1 test image bytes (PNG)
TEST_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff"
    b"?\x00\x05\xfe\x02\xfe\xa74e\x9f\x00\x00\x00\x00IEND\xaeB`\x82"
)
TEST_PNG_B64 = base64.b64encode(TEST_PNG_BYTES).decode("utf-8")


def log(msg: str):
    print(f"[STAGE07B-R5-R1] {msg}", flush=True)


def wait_for_core():
    with httpx.Client(trust_env=False, timeout=3.0) as client:
        for _ in range(30):
            try:
                r = client.get(f"{CORE_API_URL}/health")
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(1.0)
    raise RuntimeError("Core failed to become healthy within 30s")


def get_container_inode(container_name: str, path: str) -> str:
    res = subprocess.run(
        ["docker", "exec", container_name, "stat", "-c", "%i", path],
        capture_output=True, text=True
    )
    if res.returncode != 0:
        raise RuntimeError(f"stat -c %i {path} failed: {res.stderr}")
    return res.stdout.strip()


def main():
    log("=" * 75)
    log("STARTING STAGE 07B-R5-R1 VERIFICATION: PERSISTENT PHOTO STORAGE SAFETY")
    log("=" * 75)

    assert OWNER_CRT.is_file(), f"Owner cert missing: {OWNER_CRT}"
    assert OWNER_KEY.is_file(), f"Owner key missing: {OWNER_KEY}"
    owner_cert_tuple = (str(OWNER_CRT), str(OWNER_KEY))

    # -------------------------------------------------------------------------
    # TEST F: Existing OWNER access on Gateway: /, /certificates, /backups -> 200
    # -------------------------------------------------------------------------
    log("Step 1 (TEST F): Verifying existing OWNER access on Gateway 8443...")
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=15.0) as client:
        r_root = client.get(f"{GATEWAY_URL}/")
        assert r_root.status_code == 200, f"Expected 200 for /, got {r_root.status_code}"

        r_certs = client.get(f"{GATEWAY_URL}/certificates")
        assert r_certs.status_code == 200, f"Expected 200 for /certificates, got {r_certs.status_code}"

        r_backups = client.get(f"{GATEWAY_URL}/backups")
        assert r_backups.status_code == 200, f"Expected 200 for /backups, got {r_backups.status_code}"
    log("  [PASS] TEST F: OWNER access on Gateway: /, /certificates, /backups all return 200 OK.")

    # -------------------------------------------------------------------------
    # TEST G: Avito pairing and heartbeat
    # -------------------------------------------------------------------------
    log("Step 2 (TEST G): Testing Avito pairing code generation, pairing, and heartbeat...")
    with httpx.Client(trust_env=False, timeout=15.0) as client:
        r_gen = client.post(f"{ADMIN_SHELL_URL}/admin-api/avito-extension/pairing/generate")
        assert r_gen.status_code == 200, f"Failed generating code: {r_gen.status_code} {r_gen.text}"
        pair_data = r_gen.json()
        assert "pair_code" in pair_data, f"pair_code missing from {pair_data}"
        pair_code = pair_data.get("pair_code")

        r_pair = client.post(
            f"{ADMIN_SHELL_URL}/admin-api/avito-extension/pairing/pair",
            json={"pair_code": pair_code}
        )
        assert r_pair.status_code == 200, f"Failed pairing: {r_pair.status_code} {r_pair.text}"
        paired_data = r_pair.json()
        assert "extension_token" in paired_data, f"extension_token missing from {paired_data}"
        ext_token = paired_data.get("extension_token")

        r_hb = client.post(
            f"{ADMIN_SHELL_URL}/admin-api/avito-extension/heartbeat",
            headers={"X-Extension-Token": ext_token},
            json={"status": "active", "version": "0.2.43"}
        )
        assert r_hb.status_code == 200, f"Heartbeat failed: {r_hb.status_code} {r_hb.text}"
        assert r_hb.json().get("status") == "ok"
    log("  [PASS] TEST G: Avito pairing code generation, pairing handshake, and heartbeat succeeded.")

    # -------------------------------------------------------------------------
    # TEST A: Normal persistent storage available
    # -------------------------------------------------------------------------
    log("Step 3 (TEST A): Testing normal persistent storage photo import & restart survivability...")
    test_a_ext_id = f"test_a_{int(time.time())}"
    test_a_url = f"https://img.avito.st/image/1/test_a_{int(time.time())}.png"

    payload_a = {
        "account_key": "account_office",
        "external_item_id": test_a_ext_id,
        "external_url": f"https://www.avito.ru/item/{test_a_ext_id}",
        "remote_status": "active",
        "title": "Ноутбук Lenovo ThinkPad Test A",
        "price": 45000.0,
        "description": "Тестовый ноутбук для проверки постоянного хранилища",
        "photos": [
            {
                "url": test_a_url,
                "content_base64": TEST_PNG_B64,
                "position": 0
            }
        ]
    }

    with httpx.Client(trust_env=False, timeout=20.0) as client:
        r_imp_a = client.post(f"{CORE_API_URL}/api/integrations/avito/import-item", json=payload_a)
        assert r_imp_a.status_code == 200, f"Import failed: {r_imp_a.status_code} {r_imp_a.text}"
        data_a = r_imp_a.json()
        assert data_a["status"] in ("created", "updated")
        assert data_a["photos_imported"] == 1, f"Expected photos_imported=1, got {data_a['photos_imported']}"
        assert data_a["warnings"] == [], f"Expected no warnings, got {data_a['warnings']}"
        prod_id_a = data_a["product_id"]

    # Verify photo row in DB
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        "SELECT id, filename, storage_path, media_url, source_url, content_hash "
        "FROM product_photos WHERE product_id=?",
        (prod_id_a,)
    )
    photo_row_a = cur.fetchone()
    conn.close()

    assert photo_row_a is not None, "Product photo row not found in DB"
    photo_filename_a = photo_row_a[1]
    storage_path_a = photo_row_a[2]
    media_url_a = photo_row_a[3]

    assert storage_path_a is not None, "storage_path must not be None for imported photo"
    assert "/data/storage/product_photos" in storage_path_a, f"Invalid storage_path: {storage_path_a}"
    assert media_url_a.startswith("/media/product_photos/"), f"Invalid media_url: {media_url_a}"

    host_file_a = STORAGE_DIR / photo_filename_a
    assert host_file_a.is_file(), f"Photo file missing on host storage: {host_file_a}"
    assert host_file_a.stat().st_size == len(TEST_PNG_BYTES), f"Size mismatch: {host_file_a.stat().st_size}"

    # Restart Core container to test persistence
    log("  Restarting Core container to verify persistent photo survival...")
    subprocess.run(["docker", "compose", "restart", "core"], cwd=str(PROJECT_ROOT), check=True)
    wait_for_core()

    # Verify photo file still exists on disk
    assert host_file_a.is_file(), f"Photo file disappeared after Core restart: {host_file_a}"

    # Verify photo is served via HTTP through Core
    with httpx.Client(trust_env=False, timeout=10.0) as client:
        r_media_a = client.get(f"{CORE_API_URL}{media_url_a}")
        assert r_media_a.status_code == 200, f"Media fetch failed: {r_media_a.status_code}"
        assert r_media_a.content == TEST_PNG_BYTES, "Served photo content does not match original bytes"

    log("  [PASS] TEST A: Photo physically stored, survived Core restart, and served via /media static mount.")

    # -------------------------------------------------------------------------
    # TEST B: Simulated persistent storage unavailable
    # -------------------------------------------------------------------------
    log("Step 4 (TEST B): Testing simulated persistent storage unavailability...")
    # Temporarily block persistent storage directory in Core container
    block_cmd = (
        "import os\n"
        "os.rename('/data/storage/product_photos', '/data/storage/product_photos_simblock')\n"
        "with open('/data/storage/product_photos', 'w') as f: f.write('blocker')\n"
    )
    res_block = subprocess.run(
        ["docker", "compose", "exec", "-T", "core", "python", "-c", block_cmd],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True
    )
    assert res_block.returncode == 0, f"Failed blocking storage: {res_block.stderr}"

    try:
        test_b_ext_id = f"test_b_{int(time.time())}"
        test_b_url = f"https://img.avito.st/image/1/test_b_{int(time.time())}.png"

        payload_b = {
            "account_key": "account_office",
            "external_item_id": test_b_ext_id,
            "external_url": f"https://www.avito.ru/item/{test_b_ext_id}",
            "remote_status": "active",
            "title": "Монитор ASUS Test B (Storage Outage)",
            "price": 28000.0,
            "description": "Тест импорта при недоступном хранилище фото",
            "photos": [
                {
                    "url": test_b_url,
                    "content_base64": TEST_PNG_B64,
                    "position": 0
                }
            ]
        }

        # 1. Direct Core test
        with httpx.Client(trust_env=False, timeout=20.0) as client:
            r_imp_b = client.post(f"{CORE_API_URL}/api/integrations/avito/import-item", json=payload_b)
            assert r_imp_b.status_code == 200, f"Expected 200, got {r_imp_b.status_code} {r_imp_b.text}"
            data_b = r_imp_b.json()
            assert data_b["status"] in ("created", "updated")
            # photos_imported MUST be 0!
            assert data_b["photos_imported"] == 0, f"Expected photos_imported=0, got {data_b['photos_imported']}"
            # warnings MUST contain notice
            assert len(data_b["warnings"]) > 0, "Expected warnings in response"
            assert any("Persistent photo storage unavailable" in w for w in data_b["warnings"])
            prod_id_b = data_b["product_id"]

        # Check DB row: storage_path MUST be None, media_url MUST be source_url
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute(
            "SELECT id, filename, storage_path, media_url, source_url FROM product_photos WHERE product_id=?",
            (prod_id_b,)
        )
        photo_row_b = cur.fetchone()
        conn.close()

        assert photo_row_b is not None, "Product photo row not found"
        assert photo_row_b[2] is None, f"storage_path must be None, got: {photo_row_b[2]}"
        assert photo_row_b[3] == test_b_url, f"media_url should equal source_url, got: {photo_row_b[3]}"

        # Verify NO fallback to /tmp/product_photos
        res_tmp = subprocess.run(
            ["docker", "compose", "exec", "-T", "core", "ls", "-la", "/tmp/product_photos"],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True
        )
        if res_tmp.returncode == 0:
            lines = [l for l in res_tmp.stdout.strip().splitlines() if not l.startswith("total") and not l.endswith(" .") and not l.endswith(" ..")]
            assert len(lines) == 0, f"Found files in /tmp/product_photos: {lines}"

        # 2. Avito module bridge test under storage outage
        bridge_payload_b = {
            "schema_version": 1,
            "extension_version": "0.2.43",
            "captured_at": "2026-09-08T19:00:00Z",
            "page_type": "listing",
            "listing": {
                "external_item_id": f"bridge_{test_b_ext_id}",
                "external_url": f"https://www.avito.ru/item/bridge_{test_b_ext_id}",
                "title": "Bridge Test B Listing",
                "price": 15000,
                "photos": [test_b_url]
            }
        }
        with httpx.Client(trust_env=False, timeout=20.0) as client:
            r_br_b = client.post(
                f"{ADMIN_SHELL_URL}/admin-api/avito-extension/listing",
                headers={"X-Extension-Token": ext_token},
                json=bridge_payload_b
            )
            assert r_br_b.status_code == 200
            br_data_b = r_br_b.json()
            assert br_data_b["status"] == "partial", f"Expected partial status, got: {br_data_b}"
            assert br_data_b["photos_imported"] == 0
            assert "предупреждением: фото не сохранены" in br_data_b["message"]

    finally:
        # Restore storage directory
        restore_cmd = (
            "import os\n"
            "if os.path.exists('/data/storage/product_photos'): os.remove('/data/storage/product_photos')\n"
            "if os.path.exists('/data/storage/product_photos_simblock'): os.rename('/data/storage/product_photos_simblock', '/data/storage/product_photos')\n"
        )
        subprocess.run(
            ["docker", "compose", "exec", "-T", "core", "python", "-c", restore_cmd],
            cwd=str(PROJECT_ROOT), check=True
        )

    # Verify storage check is restored
    res_probe = subprocess.run(
        ["docker", "compose", "exec", "-T", "core", "python", "-c", "from app.storage import check_persistent_photo_storage; print(check_persistent_photo_storage())"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True
    )
    assert "(True, '')" in res_probe.stdout, f"Storage probe did not restore: {res_probe.stdout}"

    log("  [PASS] TEST B: Storage outage handled safely: no /tmp fallback, no fake storage_path, explicit partial warning, no HTTP 500.")

    # -------------------------------------------------------------------------
    # TEST C: Backup created after photo import contains the imported photo
    # -------------------------------------------------------------------------
    log("Step 5 (TEST C): Verifying backup contains imported photo file...")
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=60.0) as client:
        r_dl = client.post(f"{GATEWAY_URL}/admin-api/backups/download")
        assert r_dl.status_code == 200, f"Backup download failed: {r_dl.status_code} {r_dl.text}"
        backup_bytes = r_dl.content
        cd_header = r_dl.headers.get("content-disposition", "")
        bak_filename = "technoreboot_backup.zip"
        if 'filename="' in cd_header:
            bak_filename = cd_header.split('filename="')[1].split('"')[0]

    with zipfile.ZipFile(io.BytesIO(backup_bytes), "r") as z:
        names = z.namelist()
        expected_photo_zip_path = f"storage/product_photos/{photo_filename_a}"
        assert expected_photo_zip_path in names, f"Photo {expected_photo_zip_path} not found in backup! Contents: {names[:20]}"
        # Verify content inside zip matches
        zipped_photo_bytes = z.read(expected_photo_zip_path)
        assert zipped_photo_bytes == TEST_PNG_BYTES, "Zipped photo content does not match original"

    log(f"  [PASS] TEST C: Backup '{bak_filename}' contains successfully imported photo {photo_filename_a}.")

    # -------------------------------------------------------------------------
    # TEST D: Web restore preserves valid storage mount inode & photo remains available
    # -------------------------------------------------------------------------
    log("Step 6 (TEST D): Verifying web restore preserves storage bind-mount inode and photo availability...")
    inode_storage_before = get_container_inode("technoreboot-core", "/data/storage")
    inode_photos_before = get_container_inode("technoreboot-core", "/data/storage/product_photos")

    # Perform web restore using the backup
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=60.0) as client:
        r_restore = client.post(
            f"{GATEWAY_URL}/admin-api/backups/restore",
            files={"backup_file": (bak_filename, backup_bytes, "application/zip")}
        )
        assert r_restore.status_code == 200, f"Restore failed: {r_restore.status_code} {r_restore.text}"
        res_json = r_restore.json()
        assert res_json["status"] == "ok"

    inode_storage_after = get_container_inode("technoreboot-core", "/data/storage")
    inode_photos_after = get_container_inode("technoreboot-core", "/data/storage/product_photos")

    assert inode_storage_after == inode_storage_before, (
        f"/data/storage inode changed: before={inode_storage_before}, after={inode_storage_after} (bind-mount broken!)"
    )
    assert inode_photos_after == inode_photos_before, (
        f"/data/storage/product_photos inode changed: before={inode_photos_before}, after={inode_photos_after}"
    )

    # Verify photo still exists and is served
    assert host_file_a.is_file(), f"Photo missing on host after restore: {host_file_a}"
    with httpx.Client(trust_env=False, timeout=10.0) as client:
        r_media_after = client.get(f"{CORE_API_URL}{media_url_a}")
        assert r_media_after.status_code == 200, f"Media fetch after restore failed: {r_media_after.status_code}"
        assert r_media_after.content == TEST_PNG_BYTES

    log("  [PASS] TEST D: Web restore preserved mount inodes and photo remains available and valid.")

    # -------------------------------------------------------------------------
    # TEST E: Real extension-equivalent Avito import still succeeds with photos
    # -------------------------------------------------------------------------
    log("Step 7 (TEST E): Verifying real extension-equivalent Avito import via proxy...")
    real_ext_id = f"real_e_{int(time.time())}"
    real_photo_url = f"https://img.avito.st/image/1/real_photo_{int(time.time())}.png"

    e2e_payload = {
        "schema_version": 1,
        "extension_version": "0.2.43",
        "captured_at": "2026-09-08T19:30:00Z",
        "page_type": "listing",
        "listing": {
            "external_item_id": real_ext_id,
            "external_url": f"https://www.avito.ru/item/{real_ext_id}",
            "title": "Видеокарта MSI RTX 4070 Gaming X Slim",
            "price": 68000,
            "description": "Отличное состояние, полный комплект.",
            "category_path": ["Бытовая электроника", "Товары для компьютера", "Комплектующие", "Видеокарты"],
            "parameters": {
                "Производитель": "MSI",
                "Модель": "GeForce RTX 4070",
                "Объем памяти": "12 ГБ"
            },
            "photos": [
                {
                    "url": real_photo_url,
                    "content_base64": TEST_PNG_B64,
                    "position": 0
                }
            ]
        }
    }

    with httpx.Client(trust_env=False, timeout=25.0) as client:
        r_ext = client.post(
            f"{ADMIN_SHELL_URL}/admin-api/avito-extension/listing",
            headers={"X-Extension-Token": ext_token},
            json=e2e_payload
        )
        assert r_ext.status_code == 200, f"Extension proxy import failed: {r_ext.status_code} {r_ext.text}"
        ext_res = r_ext.json()
        assert ext_res.get("status") == "success"
        assert ext_res.get("photos_imported") == 1
        e2e_prod_id = ext_res.get("product_id")
        assert e2e_prod_id is not None

    # Verify photo row
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT filename, storage_path, media_url FROM product_photos WHERE product_id=?", (e2e_prod_id,))
    e2e_photo_row = cur.fetchone()
    conn.close()

    assert e2e_photo_row is not None
    assert e2e_photo_row[1] is not None
    assert (STORAGE_DIR / e2e_photo_row[0]).is_file()

    with httpx.Client(trust_env=False, timeout=10.0) as client:
        r_media_e = client.get(f"{CORE_API_URL}{e2e_photo_row[2]}")
        assert r_media_e.status_code == 200
        assert r_media_e.content == TEST_PNG_BYTES

    log("  [PASS] TEST E: Real extension import succeeded with photos properly persisted.")

    # -------------------------------------------------------------------------
    # TEST H: Relevant Core tests pass
    # -------------------------------------------------------------------------
    log("Step 8 (TEST H): Verifying Core pytest suite...")
    res_h = subprocess.run(
        ["docker", "compose", "exec", "-T", "core", "pytest"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True
    )
    assert res_h.returncode == 0, f"Core pytest failed:\n{res_h.stdout}\n{res_h.stderr}"
    assert "209 passed" in res_h.stdout, f"Expected 209 passed, got output: {res_h.stdout[-300:]}"
    log("  [PASS] TEST H: Core pytest passed (209 passed, 0 failed).")

    # -------------------------------------------------------------------------
    # TEST I: Relevant Avito module tests pass
    # -------------------------------------------------------------------------
    log("Step 9 (TEST I): Verifying Avito module pytest suite...")
    res_i = subprocess.run(
        ["docker", "compose", "exec", "-T", "avito-module", "pytest"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True
    )
    assert res_i.returncode == 0, f"Avito module pytest failed:\n{res_i.stdout}\n{res_i.stderr}"
    assert "95 passed" in res_i.stdout, f"Expected 95 passed, got output: {res_i.stdout[-300:]}"
    log("  [PASS] TEST I: Avito module pytest passed (95 passed, 0 failed).")

    # Clean up test products from DB and disk to keep workspace pristine
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("DELETE FROM product_photos WHERE product_id IN (?, ?, ?)", (prod_id_a, prod_id_b, e2e_prod_id))
        conn.execute("DELETE FROM product_external_listings WHERE product_id IN (?, ?, ?)", (prod_id_a, prod_id_b, e2e_prod_id))
        conn.execute("DELETE FROM products WHERE id IN (?, ?, ?)", (prod_id_a, prod_id_b, e2e_prod_id))
        conn.commit()
        conn.close()
        if host_file_a.exists():
            host_file_a.unlink()
        if (STORAGE_DIR / e2e_photo_row[0]).exists():
            (STORAGE_DIR / e2e_photo_row[0]).unlink()
    except Exception as e:
        log(f"Cleanup notice: {e}")

    log("=" * 75)
    log("ALL STAGE 07B-R5-R1 TESTS (TEST A through TEST I) PASSED PERFECTLY!")
    log("=" * 75)


if __name__ == "__main__":
    main()
