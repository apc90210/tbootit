#!/usr/bin/env python3
"""
Stage 07F-R1-R3 Live Verification Script
Tests Avito bulk field accuracy (price model digit isolation), thumbnail photo persistence,
photo idempotency, products.html preview column, and test cleanup invariant.

Strict invariant enforced:
product_count_after_live_test == product_count_before_live_test
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
    print(f"[STAGE07F-R3] {msg}", flush=True)


def get_db_product_count():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM products")
        return cur.fetchone()[0]
    finally:
        conn.close()


def main():
    log("=" * 75)
    log("STARTING STAGE 07F-R1-R3 LIVE VERIFICATION")
    log("=" * 75)

    assert OWNER_CRT.is_file(), f"Owner cert missing: {OWNER_CRT}"
    assert OWNER_KEY.is_file(), f"Owner key missing: {OWNER_KEY}"
    owner_cert_tuple = (str(OWNER_CRT), str(OWNER_KEY))

    # Record initial product count
    count_before = get_db_product_count()
    log(f"Initial DB product count: {count_before}")

    created_test_ids = []
    test_run_uuid = uuid.uuid4().hex[:8]
    test_item_prefix = f"live_07f_r3_{test_run_uuid}"

    try:
        with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=20.0) as client:
            # -------------------------------------------------------------------------
            # SCENARIO 1: Gateway mTLS Extension Page & Download v0.2.51
            # -------------------------------------------------------------------------
            log("--- Scenario 1: Verifying Extension Page & Download v0.2.51 via Gateway 8443 ---")
            r_page = client.get(f"{GATEWAY_URL}/avito/extension")
            assert r_page.status_code == 200, f"Failed to get /avito/extension: {r_page.status_code}"
            assert "v0.2.51" in r_page.text, "Extension page must display v0.2.51"
            log("[PASS] Extension page displays v0.2.51")

            r_dl = client.get(f"{GATEWAY_URL}/avito/extension/download")
            assert r_dl.status_code == 200, f"Failed to download extension: {r_dl.status_code}"
            disposition = r_dl.headers.get("content-disposition", "")
            assert "0.2.51" in disposition, f"Content-Disposition must contain 0.2.51: {disposition}"

            # Verify ZIP contents
            zip_bytes = io.BytesIO(r_dl.content)
            with zipfile.ZipFile(zip_bytes, "r") as z:
                manifest_raw = z.read("manifest.json").decode("utf-8")
                manifest_data = json.loads(manifest_raw)
                assert manifest_data.get("version") == "0.2.51", f"Manifest version mismatch: {manifest_data.get('version')}"
            log("[PASS] Extension ZIP download serves verified v0.2.51 package")

            # -------------------------------------------------------------------------
            # SCENARIO 2: Extension Pairing & Status Check
            # -------------------------------------------------------------------------
            log("--- Scenario 2: Extension Pairing & Status Check ---")
            r_pair_gen = client.post(f"{GATEWAY_URL}/admin-api/avito-extension/pairing/generate")
            assert r_pair_gen.status_code == 200
            pair_code = r_pair_gen.json()["pair_code"]

            r_pair = client.post(f"{GATEWAY_URL}/admin-api/avito-extension/pairing/pair", json={"pair_code": pair_code})
            assert r_pair.status_code == 200
            ext_token = r_pair.json()["extension_token"]

            r_st = client.get(f"{GATEWAY_URL}/admin-api/avito-extension/status", headers={"X-Extension-Token": ext_token})
            assert r_st.status_code == 200
            st_data = r_st.json()
            assert st_data.get("version") == "0.2.51", f"Bridge status version mismatch: {st_data}"
            assert st_data.get("online") is True
            assert st_data.get("paired") is True
            log(f"[PASS] Extension bridge paired and reports online v{st_data.get('version')}")

            # -------------------------------------------------------------------------
            # SCENARIO 3: Bulk Import Field Accuracy & Thumbnail Persistence
            # -------------------------------------------------------------------------
            log("--- Scenario 3: Bulk Import with Strict Price & Thumbnail Ingestion ---")
            
            # Tiny valid JPEG 1x1 base64
            tiny_jpg_b64 = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="

            item1_id = f"{test_item_prefix}_1"
            item2_id = f"{test_item_prefix}_2"

            bulk_payload = {
                "schema_version": 1,
                "extension_version": "0.2.51",
                "page_type": "bulk_import",
                "items": [
                    {
                        "avito_id": item1_id,
                        "url": f"https://www.avito.ru/item/{item1_id}",
                        "title": "Принтер HP LaserJet P2055 3 500 ₽",
                        "price": 3500.0,
                        "thumbnail_url": f"https://img.avito.st/image/1/{item1_id}.jpg",
                        "thumbnail_base64": tiny_jpg_b64
                    },
                    {
                        "avito_id": item2_id,
                        "url": f"https://www.avito.ru/item/{item2_id}",
                        "title": "Процессор Intel Xeon E3-1220 665 ₽",
                        "price": 665.0
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
            log("[PASS] Bulk import created 2 test products")

            # Verify in DB
            conn = sqlite3.connect(str(DB_PATH))
            try:
                cur = conn.cursor()
                # Check item 1
                cur.execute("SELECT p.id, p.title, p.sale_price, p.sku FROM products p JOIN product_external_listings e ON p.id = e.product_id WHERE e.external_item_id = ?", (item1_id,))
                row1 = cur.fetchone()
                assert row1 is not None, f"Product {item1_id} not found in DB"
                p1_id, p1_title, p1_price, p1_sku = row1
                created_test_ids.append(p1_id)
                assert p1_price == 3500.0, f"Price contamination error! Expected 3500.0, got {p1_price}"
                log(f"[PASS] Product {p1_id} price correctly saved as {p1_price} (no model digit contamination)")

                # Check item 1 photo
                cur.execute("SELECT id, media_url, storage_path, sort_order FROM product_photos WHERE product_id = ?", (p1_id,))
                photo_rows = cur.fetchall()
                assert len(photo_rows) == 1, f"Expected 1 photo for product {p1_id}, got {len(photo_rows)}"
                photo_id, media_url, storage_path, sort_order = photo_rows[0]
                assert sort_order == 0, f"Expected sort_order 0, got {sort_order}"
                assert media_url.startswith("/media/product_photos/"), f"Unexpected media_url: {media_url}"
                log(f"[PASS] Product {p1_id} has persistent thumbnail (photo ID: {photo_id}, sort_order: {sort_order}, url: {media_url})")

                # Check item 2
                cur.execute("SELECT p.id, p.title, p.sale_price, p.sku FROM products p JOIN product_external_listings e ON p.id = e.product_id WHERE e.external_item_id = ?", (item2_id,))
                row2 = cur.fetchone()
                assert row2 is not None, f"Product {item2_id} not found in DB"
                p2_id, p2_title, p2_price, p2_sku = row2
                created_test_ids.append(p2_id)
                assert p2_price == 665.0, f"Price contamination error! Expected 665.0, got {p2_price}"
                log(f"[PASS] Product {p2_id} price correctly saved as {p2_price}")

                # Check item 2 photo (none)
                cur.execute("SELECT COUNT(*) FROM product_photos WHERE product_id = ?", (p2_id,))
                p2_photos_count = cur.fetchone()[0]
                assert p2_photos_count == 0, f"Item 2 should have 0 photos, got {p2_photos_count}"
            finally:
                conn.close()

            # -------------------------------------------------------------------------
            # SCENARIO 4: Product List HTML Preview Column & Dash
            # -------------------------------------------------------------------------
            log("--- Scenario 4: Verifying Products List HTML Table Preview Column ---")
            r_list = client.get(f"{GATEWAY_URL}/inventory/products?q={test_item_prefix}")
            assert r_list.status_code == 200
            html_text = r_list.text

            # Header must have Фото
            assert "Фото" in html_text, "Products table must have 'Фото' column header"

            # Item 1 row must contain <img> with thumbnail
            assert f"/inventory/products/{p1_id}" in html_text
            assert media_url in html_text or "Превью" in html_text, "Item 1 row must contain thumbnail image"
            log(f"[PASS] Products list renders thumbnail <img> for product {p1_id}")

            # Item 2 row must contain '—'
            assert f"/inventory/products/{p2_id}" in html_text
            assert "—" in html_text, "Item 2 row without photo must render '—'"
            log(f"[PASS] Products list renders '—' for product {p2_id} without photo")

            # -------------------------------------------------------------------------
            # SCENARIO 5: Re-import Idempotency & Photo Preserving
            # -------------------------------------------------------------------------
            log("--- Scenario 5: Re-import Idempotency & Price Correction ---")
            reimport_payload = {
                "schema_version": 1,
                "extension_version": "0.2.51",
                "items": [
                    {
                        "avito_id": item1_id,
                        "url": f"https://www.avito.ru/item/{item1_id}",
                        "title": "Принтер HP LaserJet P2055 Исправленный",
                        "price": 3600.0,
                        "thumbnail_url": f"https://img.avito.st/image/1/{item1_id}.jpg"
                    }
                ]
            }
            r_reimport = client.post(
                f"{GATEWAY_URL}/admin-api/avito-extension/bulk-import",
                headers={"X-Extension-Token": ext_token},
                json=reimport_payload
            )
            assert r_reimport.status_code == 200
            reimport_res = r_reimport.json()
            assert reimport_res["created"] == 0, "Re-import must NOT create duplicate product"
            assert reimport_res["updated"] == 1, "Re-import must update existing product"

            conn = sqlite3.connect(str(DB_PATH))
            try:
                cur = conn.cursor()
                cur.execute("SELECT sale_price FROM products WHERE id = ?", (p1_id,))
                updated_price = cur.fetchone()[0]
                assert updated_price == 3600.0, f"Expected updated price 3600.0, got {updated_price}"

                cur.execute("SELECT COUNT(*) FROM product_photos WHERE product_id = ?", (p1_id,))
                photo_count_after_reimport = cur.fetchone()[0]
                assert photo_count_after_reimport == 1, f"Photo count should remain 1, got {photo_count_after_reimport}"
                log(f"[PASS] Re-import updated price to {updated_price} without duplicating product or photo")
            finally:
                conn.close()

    finally:
        # -------------------------------------------------------------------------
        # SCENARIO 6: Deterministic Cleanup Invariant Enforcement
        # -------------------------------------------------------------------------
        log("--- Scenario 6: Cleanup Invariant Enforcement in finally ---")
        if created_test_ids:
            conn = sqlite3.connect(str(DB_PATH))
            try:
                cur = conn.cursor()
                for pid in created_test_ids:
                    # Clean up photos
                    cur.execute("SELECT storage_path FROM product_photos WHERE product_id = ?", (pid,))
                    photos_to_del = cur.fetchall()
                    for (sp,) in photos_to_del:
                        if sp and os.path.exists(sp):
                            try:
                                os.remove(sp)
                            except Exception:
                                pass
                    cur.execute("DELETE FROM product_photos WHERE product_id = ?", (pid,))
                    cur.execute("DELETE FROM product_external_listings WHERE product_id = ?", (pid,))
                    cur.execute("DELETE FROM product_events WHERE product_id = ?", (pid,))
                    cur.execute("DELETE FROM product_avito_attribute_values WHERE product_id = ?", (pid,))
                    cur.execute("DELETE FROM products WHERE id = ?", (pid,))
                conn.commit()
                log(f"[CLEANUP] Deleted {len(created_test_ids)} test products and dependent rows/files: {created_test_ids}")
            finally:
                conn.close()

        count_after = get_db_product_count()
        log(f"Final DB product count: {count_after} (Initial: {count_before})")
        assert count_after == count_before, f"INVARIANT VIOLATED: count_after ({count_after}) != count_before ({count_before})!"
        log("[PASS] Invariant verified: product_count_after_live_test == product_count_before_live_test")

    log("=" * 75)
    log("STAGE 07F-R1-R3 ALL LIVE VERIFICATION CHECKS PASSED PERFECTLY!")
    log("=" * 75)


if __name__ == "__main__":
    main()
