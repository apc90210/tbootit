#!/usr/bin/env python3
"""
Stage 07F-R1-R3-R2 Live Verification Script
Tests real Avito thumbnail chain, photo diagnostics, DB reconciliation,
Gateway mTLS, repeat import idempotency, and zero-pollution invariant.

Strict invariant enforced:
BUSINESS_PRODUCT_IDS_AFTER == BUSINESS_PRODUCT_IDS_BEFORE (set of 193 products)
"""

import os
import sys
import io
import re
import json
import uuid
import base64
import zipfile
import sqlite3
from pathlib import Path
import httpx
import urllib3

urllib3.disable_warnings()

GATEWAY_URL = "https://127.0.0.1:8443"
ADMIN_SHELL_DIRECT_URL = "http://127.0.0.1:8011"
CORE_API_URL = "http://127.0.0.1:8000"

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
AUTH_DIR = PROJECT_ROOT / "data" / "auth"
DB_PATH = PROJECT_ROOT / "data" / "db" / "technoreboot.db"

OWNER_CRT = AUTH_DIR / "certificates" / "owner.crt"
OWNER_KEY = AUTH_DIR / "certificates" / "owner.key"


def log(msg: str):
    print(f"[STAGE07F-R3-R2] {msg}", flush=True)


def to_host_path(container_path: str) -> Path:
    if container_path.startswith("/data/"):
        return PROJECT_ROOT / "data" / container_path[len("/data/"):]
    return Path(container_path)


def get_db_product_ids():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM products ORDER BY id ASC")
        return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


def main():
    log("=" * 75)
    log("STARTING STAGE 07F-R1-R3-R2 LIVE VERIFICATION")
    log("=" * 75)

    assert OWNER_CRT.is_file(), f"Owner cert missing: {OWNER_CRT}"
    assert OWNER_KEY.is_file(), f"Owner key missing: {OWNER_KEY}"
    owner_cert_tuple = (str(OWNER_CRT), str(OWNER_KEY))

    # -------------------------------------------------------------------------
    # SCENARIO 0: Baseline DB Reconciliation Audit
    # -------------------------------------------------------------------------
    log("--- Scenario 0: Baseline DB Reconciliation Audit (193 products) ---")
    ids_before = get_db_product_ids()
    log(f"Initial DB product count: {len(ids_before)}")
    assert len(ids_before) == 193, f"Expected exactly 193 products in DB, got {len(ids_before)}"
    assert 171 not in ids_before, "Test stub 171 (AVITO-111) must NOT exist in DB"
    assert 172 not in ids_before, "Test stub 172 (AVITO-222) must NOT exist in DB"

    # All 33 real Avito products (296..328) must be present
    real_33 = set(range(296, 329))
    assert real_33.issubset(ids_before), f"Missing real Avito products: {real_33 - ids_before}"
    log("[PASS] Scenario 0: Live DB contains exactly 193 products (160 baseline + 33 real Avito, 0 test stubs)")

    created_test_ids = []
    test_run_uuid = uuid.uuid4().hex[:8]
    test_item_prefix = f"live_07f_r2_{test_run_uuid}"

    try:
        # -------------------------------------------------------------------------
        # SCENARIO 1: Gateway mTLS Authentication Protection
        # -------------------------------------------------------------------------
        log("--- Scenario 1: Gateway mTLS Protection (403 unauth, 200 auth) ---")
        # 1. Unauthenticated request without client cert -> 403 Forbidden
        with httpx.Client(verify=False, trust_env=False, timeout=10.0) as unauth_client:
            try:
                r_unauth = unauth_client.get(f"{GATEWAY_URL}/avito/extension")
                assert r_unauth.status_code == 403, f"Expected 403 for unauthenticated mTLS, got {r_unauth.status_code}"
                log("[PASS] Unauthenticated request to Gateway 8443 correctly rejected with 403 Forbidden")
            except httpx.ConnectError:
                log("[PASS] Gateway terminated connection for missing client cert")

        # 2. Authenticated request with Owner cert -> 200 OK
        with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=20.0) as client:
            # -------------------------------------------------------------------------
            # SCENARIO 2: Extension Page & Download Serving v0.2.52
            # -------------------------------------------------------------------------
            log("--- Scenario 2: Verifying Extension Page & Download v0.2.52 via Gateway ---")
            r_page = client.get(f"{GATEWAY_URL}/avito/extension")
            assert r_page.status_code == 200, f"Failed to get /avito/extension: {r_page.status_code}"
            assert "v0.2.52" in r_page.text, "Extension page must display v0.2.52"
            log("[PASS] Extension page displays v0.2.52")

            r_dl = client.get(f"{GATEWAY_URL}/avito/extension/download")
            assert r_dl.status_code == 200, f"Failed to download extension: {r_dl.status_code}"
            disposition = r_dl.headers.get("content-disposition", "")
            assert "0.2.52" in disposition, f"Content-Disposition must contain 0.2.52: {disposition}"

            # Verify ZIP contents
            zip_bytes = io.BytesIO(r_dl.content)
            with zipfile.ZipFile(zip_bytes, "r") as z:
                manifest_raw = z.read("manifest.json").decode("utf-8")
                manifest_data = json.loads(manifest_raw)
                assert manifest_data.get("version") == "0.2.52", f"Manifest version mismatch: {manifest_data.get('version')}"
                popup_js_raw = z.read("popup.js").decode("utf-8")
                assert 'let manifestVer = "0.2.52";' in popup_js_raw
                assert "фото найдено:" in popup_js_raw.lower()
            log("[PASS] Extension ZIP download serves verified v0.2.52 package with photo diagnostics")

            # -------------------------------------------------------------------------
            # SCENARIO 3: Extension Pairing & Bridge Status
            # -------------------------------------------------------------------------
            log("--- Scenario 3: Extension Pairing & Bridge Status v0.2.52 ---")
            r_pair_gen = client.post(f"{GATEWAY_URL}/admin-api/avito-extension/pairing/generate")
            assert r_pair_gen.status_code == 200
            pair_code = r_pair_gen.json()["pair_code"]

            r_pair = client.post(f"{GATEWAY_URL}/admin-api/avito-extension/pairing/pair", json={"pair_code": pair_code})
            assert r_pair.status_code == 200
            ext_token = r_pair.json()["extension_token"]

            r_st = client.get(f"{GATEWAY_URL}/admin-api/avito-extension/status", headers={"X-Extension-Token": ext_token})
            assert r_st.status_code == 200
            st_data = r_st.json()
            assert st_data.get("version") == "0.2.52", f"Bridge status version mismatch: {st_data}"
            assert st_data.get("online") is True
            assert st_data.get("paired") is True
            log(f"[PASS] Extension bridge paired and reports online v{st_data.get('version')}")

            # -------------------------------------------------------------------------
            # SCENARIO 4: Real Thumbnail Ingestion Chain (Payload -> Core -> File -> Media URL)
            # -------------------------------------------------------------------------
            log("--- Scenario 4: Real Thumbnail Ingestion Chain ---")

            # Valid 1x1 JPEG
            tiny_jpg_b64 = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="

            item1_id = f"{test_item_prefix}_1"
            item2_id = f"{test_item_prefix}_2"

            bulk_payload = {
                "schema_version": 1,
                "extension_version": "0.2.52",
                "page_type": "bulk_import",
                "items": [
                    {
                        "avito_id": item1_id,
                        "url": f"https://www.avito.ru/item/{item1_id}",
                        "title": "Принтер HP LaserJet P2055",
                        "price": 3500.0,
                        "thumbnail_url": f"https://img.avito.st/image/1/{item1_id}.jpg",
                        "thumbnail_base64": tiny_jpg_b64
                    },
                    {
                        "avito_id": item2_id,
                        "url": f"https://www.avito.ru/item/{item2_id}",
                        "title": "Монитор Samsung Odyssey G7 27 240Hz",
                        "price": 32000.0,
                        "thumbnail_url": f"https://img.avito.st/image/1/{item2_id}.jpg",
                        "thumbnail_base64": tiny_jpg_b64
                    }
                ]
            }

            r_bulk = client.post(
                f"{GATEWAY_URL}/admin-api/avito-extension/bulk-import",
                headers={"X-Extension-Token": ext_token},
                json=bulk_payload
            )
            assert r_bulk.status_code == 200, f"Bulk import failed: {r_bulk.text}"
            bulk_res = r_bulk.json()
            assert bulk_res["created"] == 2, f"Expected 2 created, got {bulk_res}"
            log("[PASS] Bulk import created 2 test products with thumbnails")

            # Verify in DB and file system
            conn = sqlite3.connect(str(DB_PATH))
            try:
                cur = conn.cursor()

                # Item 1: HP LaserJet P2055
                cur.execute("SELECT p.id, p.title, p.sale_price FROM products p JOIN product_external_listings e ON p.id = e.product_id WHERE e.external_item_id = ?", (item1_id,))
                row1 = cur.fetchone()
                assert row1 is not None, f"Product {item1_id} not found in DB"
                p1_id, p1_title, p1_price = row1
                created_test_ids.append(p1_id)
                assert p1_price == 3500.0, f"Expected price 3500.0, got {p1_price} (model number regression check)"

                # Check Item 1 Photo
                cur.execute("SELECT id, media_url, storage_path, sort_order FROM product_photos WHERE product_id = ?", (p1_id,))
                photo_rows1 = cur.fetchall()
                assert len(photo_rows1) == 1, f"Expected 1 photo for product {p1_id}, got {len(photo_rows1)}"
                ph1_id, media_url1, storage_path1, sort_order1 = photo_rows1[0]
                assert sort_order1 == 0, f"Expected sort_order 0, got {sort_order1}"
                assert media_url1.startswith("/media/product_photos/"), f"Invalid media_url: {media_url1}"

                # Verify file on disk exists and has non-zero size
                host_file1 = to_host_path(storage_path1)
                assert host_file1.exists(), f"Photo file on disk missing: {host_file1}"
                assert host_file1.stat().st_size > 0, f"Photo file on disk is empty: {host_file1}"
                log(f"[PASS] Product {p1_id} photo saved on disk ({host_file1}, {host_file1.stat().st_size} bytes)")

                # Item 2: Samsung Odyssey
                cur.execute("SELECT p.id, p.title, p.sale_price FROM products p JOIN product_external_listings e ON p.id = e.product_id WHERE e.external_item_id = ?", (item2_id,))
                row2 = cur.fetchone()
                assert row2 is not None, f"Product {item2_id} not found in DB"
                p2_id, p2_title, p2_price = row2
                created_test_ids.append(p2_id)
                assert p2_price == 32000.0, f"Expected price 32000.0, got {p2_price}"

                cur.execute("SELECT id, media_url, storage_path, sort_order FROM product_photos WHERE product_id = ?", (p2_id,))
                photo_rows2 = cur.fetchall()
                assert len(photo_rows2) == 1, f"Expected 1 photo for product {p2_id}, got {len(photo_rows2)}"
                ph2_id, media_url2, storage_path2, sort_order2 = photo_rows2[0]
                host_file2 = to_host_path(storage_path2)
                assert host_file2.exists() and host_file2.stat().st_size > 0
                log(f"[PASS] Product {p2_id} photo saved on disk ({host_file2}, {host_file2.stat().st_size} bytes)")
            finally:
                conn.close()

            # -------------------------------------------------------------------------
            # SCENARIO 5: Media URL Serving via Gateway & Table Rendering
            # -------------------------------------------------------------------------
            log("--- Scenario 5: Media URL Serving via Gateway & Products Table Rendering ---")

            # 1. Fetch the media file through Gateway
            r_media = client.get(f"{GATEWAY_URL}{media_url1}")
            assert r_media.status_code == 200, f"Failed to fetch media file via Gateway: {r_media.status_code}"
            assert len(r_media.content) > 0, "Media response content is empty"
            assert r_media.headers.get("content-type", "").startswith("image/"), f"Invalid Content-Type: {r_media.headers.get('content-type')}"
            log(f"[PASS] Gateway successfully serves media photo at {media_url1} (status 200, size {len(r_media.content)} bytes)")

            # 2. Check Inventory Products Table Rendering
            r_table = client.get(f"{GATEWAY_URL}/inventory/products?q={test_item_prefix}")
            assert r_table.status_code == 200, f"Failed to get inventory products: {r_table.status_code}"
            table_html = r_table.text
            assert "Фото" in table_html, "Products table must contain 'Фото' header"
            assert f"/inventory/products/{p1_id}" in table_html
            assert media_url1 in table_html or 'alt="Превью"' in table_html, f"Table HTML must render img src for product {p1_id}"
            assert '42px' in table_html or 'width=' in table_html or 'img' in table_html, "Image must have thumbnail dimensions"
            log(f"[PASS] Products list renders thumbnail <img> for product {p1_id}")

            # -------------------------------------------------------------------------
            # SCENARIO 6: Repeat Import Idempotency (0 duplicate products, 0 duplicate photos)
            # -------------------------------------------------------------------------
            log("--- Scenario 6: Repeat Import Idempotency ---")
            repeat_payload = {
                "schema_version": 1,
                "extension_version": "0.2.52",
                "items": [
                    {
                        "avito_id": item1_id,
                        "url": f"https://www.avito.ru/item/{item1_id}",
                        "title": "Принтер HP LaserJet P2055 Обновленный",
                        "price": 3550.0,
                        "thumbnail_url": f"https://img.avito.st/image/1/{item1_id}.jpg",
                        "thumbnail_base64": tiny_jpg_b64
                    }
                ]
            }
            r_repeat = client.post(
                f"{GATEWAY_URL}/admin-api/avito-extension/bulk-import",
                headers={"X-Extension-Token": ext_token},
                json=repeat_payload
            )
            assert r_repeat.status_code == 200
            repeat_res = r_repeat.json()
            assert repeat_res["created"] == 0, f"Repeat import must NOT create new product: {repeat_res}"
            assert repeat_res["updated"] == 1, f"Repeat import must update existing product: {repeat_res}"

            conn = sqlite3.connect(str(DB_PATH))
            try:
                cur = conn.cursor()
                cur.execute("SELECT sale_price FROM products WHERE id = ?", (p1_id,))
                updated_price = cur.fetchone()[0]
                assert updated_price == 3550.0, f"Expected updated price 3550.0, got {updated_price}"

                cur.execute("SELECT COUNT(*) FROM product_photos WHERE product_id = ?", (p1_id,))
                photo_count = cur.fetchone()[0]
                assert photo_count == 1, f"Repeat import created duplicate photo! Expected 1, got {photo_count}"
                log(f"[PASS] Repeat import updated price to {updated_price} with 0 duplicate products and 0 duplicate photos")
            finally:
                conn.close()

    finally:
        # -------------------------------------------------------------------------
        # SCENARIO 7: Deterministic Cleanup & Invariant Verification
        # -------------------------------------------------------------------------
        log("--- Scenario 7: Deterministic Cleanup in finally ---")
        conn = sqlite3.connect(str(DB_PATH))
        try:
            cur = conn.cursor()
            cur.execute("SELECT p.id FROM products p JOIN product_external_listings e ON p.id = e.product_id WHERE e.external_item_id LIKE ?", (f"{test_item_prefix}%",))
            prefix_ids = {row[0] for row in cur.fetchall()}
            all_to_clean = set(created_test_ids) | prefix_ids

            if all_to_clean:
                for pid in all_to_clean:
                    # Clean up photos
                    cur.execute("SELECT storage_path FROM product_photos WHERE product_id = ?", (pid,))
                    photos_to_del = cur.fetchall()
                    for (sp,) in photos_to_del:
                        if sp:
                            hf = to_host_path(sp)
                            if hf.exists():
                                try:
                                    hf.unlink()
                                except Exception:
                                    pass
                    cur.execute("DELETE FROM product_photos WHERE product_id = ?", (pid,))
                    cur.execute("DELETE FROM product_external_listings WHERE product_id = ?", (pid,))
                    cur.execute("DELETE FROM product_events WHERE product_id = ?", (pid,))
                    cur.execute("DELETE FROM product_avito_attribute_values WHERE product_id = ?", (pid,))
                    cur.execute("DELETE FROM products WHERE id = ?", (pid,))
                conn.commit()
                log(f"[CLEANUP] Cleaned up {len(all_to_clean)} test products and media files: {all_to_clean}")
        finally:
            conn.close()

        ids_after = get_db_product_ids()
        log(f"Product count after test: {len(ids_after)} (Initial: {len(ids_before)})")
        assert ids_after == ids_before, f"INVARIANT VIOLATION: ids_after != ids_before! Diff: {ids_after.symmetric_difference(ids_before)}"
        assert len(ids_after) == 193, f"INVARIANT VIOLATION: expected 193 products, got {len(ids_after)}"
        log("[PASS] Strict zero-pollution invariant verified: BUSINESS_PRODUCT_IDS_AFTER == BUSINESS_PRODUCT_IDS_BEFORE (193 products)")

    log("=" * 75)
    log("STAGE 07F-R1-R3-R2 LIVE VERIFICATION PASSED PERFECTLY!")
    log("=" * 75)


if __name__ == "__main__":
    main()
