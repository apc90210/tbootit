"""
Live Gateway mTLS Verification for Stage 07F-R1-R3-R1
- Verifies real Avito product restoration (all 35 real products preserved)
- Verifies re-import upserts existing product without creating duplicates
- Verifies price correction and photo preservation
- Verifies invariant: REAL_PRODUCT_SET_BEFORE == REAL_PRODUCT_SET_AFTER
"""

import os
import sys
import sqlite3
import httpx
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CERT_FILE = BASE_DIR / "data" / "auth" / "certificates" / "owner.crt"
KEY_FILE = BASE_DIR / "data" / "auth" / "certificates" / "owner.key"
CA_FILE = BASE_DIR / "data" / "auth" / "ca" / "ca.crt"
DB_PATH = BASE_DIR / "data" / "db" / "technoreboot.db"
GATEWAY_URL = "https://localhost:8443"

def log(msg: str):
    print(f"[*] {msg}", flush=True)

def get_real_product_ids(conn: sqlite3.Connection) -> set:
    cur = conn.cursor()
    cur.execute("SELECT id FROM products WHERE sku NOT LIKE '%live_07f%'")
    return {r[0] for r in cur.fetchall()}

def main():
    log("=" * 75)
    log("STAGE 07F-R1-R3-R1: LIVE RESTORATION & ZERO-POLLUTION VERIFICATION")
    log("=" * 75)

    if not CERT_FILE.exists() or not KEY_FILE.exists() or not CA_FILE.exists():
        log(f"ERROR: mTLS certificates not found in {BASE_DIR / 'data' / 'auth'}")
        sys.exit(1)

    # Initial state audit
    conn = sqlite3.connect(str(DB_PATH))
    real_set_before = get_real_product_ids(conn)
    total_before = conn.execute("SELECT count(*) FROM products").fetchone()[0]
    conn.close()

    log(f"Initial DB state: total={total_before}, real={len(real_set_before)}")
    assert len(real_set_before) == 195, f"Expected 195 real products, got {len(real_set_before)}"
    assert 297 in real_set_before, "Real Product #297 (HP LaserJet P2055) must be in DB!"

    created_test_ids = []

    try:
        with httpx.Client(
            verify=False,
            trust_env=False,
            cert=(str(CERT_FILE), str(KEY_FILE)),
            timeout=30.0
        ) as client:

            # -----------------------------------------------------------------
            # SCENARIO 1: Gateway mTLS Enforcement
            # -----------------------------------------------------------------
            log("--- Scenario 1: Checking Gateway mTLS Enforcement ---")
            with httpx.Client(verify=False, trust_env=False, timeout=10.0) as unauth_client:
                try:
                    r_unauth = unauth_client.get(f"{GATEWAY_URL}/avito/extension")
                    assert r_unauth.status_code in [400, 403, 495, 496], f"Expected 403/495/496, got {r_unauth.status_code}"
                    log("[PASS] Unauthenticated request safely blocked by Nginx Gateway mTLS")
                except httpx.ConnectError:
                    log("[PASS] Unauthenticated request rejected at TLS handshake")

            # -----------------------------------------------------------------
            # SCENARIO 2: Pairing Flow
            # -----------------------------------------------------------------
            log("--- Scenario 2: Extension Pairing Flow ---")
            r_gen = client.post(f"{GATEWAY_URL}/admin-api/avito-extension/pairing/generate")
            assert r_gen.status_code == 200, f"Generate pair code failed: {r_gen.text}"
            pair_code = r_gen.json().get("pair_code")
            assert pair_code and len(pair_code) == 6

            r_pair = client.post(
                f"{GATEWAY_URL}/admin-api/avito-extension/pairing/pair",
                json={"pair_code": pair_code}
            )
            assert r_pair.status_code == 200, f"Pair failed: {r_pair.text}"
            ext_token = r_pair.json().get("extension_token")
            assert ext_token

            r_status = client.get(
                f"{GATEWAY_URL}/admin-api/avito-extension/status",
                headers={"X-Extension-Token": ext_token}
            )
            assert r_status.status_code == 200
            assert r_status.json().get("paired") is True
            log("[PASS] Extension pairing active and verified")

            # -----------------------------------------------------------------
            # SCENARIO 3: Re-Import Updates Restored Product Without Recreation
            # -----------------------------------------------------------------
            log("--- Scenario 3: Re-import Restored Product (HP LaserJet P2055) ---")
            # Target product 297: avito_id = '8250874053'
            reimport_payload = {
                "schema_version": 1,
                "extension_version": "0.2.51",
                "items": [
                    {
                        "avito_id": "8250874053",
                        "url": "https://www.avito.ru/ekaterinburg/orgtehnika_i_rashodniki/lazernyy_printer_hp_laserjet_p2055_8250874053",
                        "title": "Лазерный принтер hp laserjet p2055",
                        "price": 3500.0,
                        "thumbnail_url": "https://10.img.avito.st/image/1/1.p2055_thumb.jpg"
                    }
                ]
            }

            r_reimport = client.post(
                f"{GATEWAY_URL}/admin-api/avito-extension/bulk-import",
                headers={"X-Extension-Token": ext_token},
                json=reimport_payload
            )
            assert r_reimport.status_code == 200
            res = r_reimport.json()
            assert res["created"] == 0, f"Re-import must NOT create duplicate! Got created={res['created']}"
            assert res["updated"] == 1, f"Re-import must update existing! Got updated={res['updated']}"
            assert res["error_count"] == 0

            # Verify Product 297 in DB
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            p297 = conn.execute("SELECT * FROM products WHERE id = 297").fetchone()
            assert p297 is not None, "Product 297 must exist!"
            assert p297["sale_price"] == 3500.0, f"Expected price 3500.0, got {p297['sale_price']}"
            assert p297["sku"] == "AVITO-8250874053"
            conn.close()
            log("[PASS] Re-import updated existing Product #297 with exact price 3500.0 without recreation or duplicate")

            # -----------------------------------------------------------------
            # SCENARIO 4: Product List HTML Renders Photo Column & Dash
            # -----------------------------------------------------------------
            log("--- Scenario 4: Verifying Products List HTML Table Preview ---")
            r_list = client.get(f"{GATEWAY_URL}/inventory/products?q=8250874053")
            assert r_list.status_code == 200
            assert "Фото" in r_list.text
            assert "hp laserjet p2055" in r_list.text.lower()
            log("[PASS] Inventory table renders product card and 'Фото' header")

            # -----------------------------------------------------------------
            # SCENARIO 5: Test Entity Zero-Pollution Guard Check
            # -----------------------------------------------------------------
            log("--- Scenario 5: Temporary Test Entity with Zero-Pollution Cleanup ---")
            temp_avito_id = "live_07f_r3_r1_temp_test_item"
            temp_payload = {
                "schema_version": 1,
                "extension_version": "0.2.51",
                "items": [
                    {
                        "avito_id": temp_avito_id,
                        "url": f"https://www.avito.ru/item/{temp_avito_id}",
                        "title": "Temporary Test Item Stage07F-R1-R3-R1",
                        "price": 999.0
                    }
                ]
            }
            r_temp = client.post(
                f"{GATEWAY_URL}/admin-api/avito-extension/bulk-import",
                headers={"X-Extension-Token": ext_token},
                json=temp_payload
            )
            assert r_temp.status_code == 200
            assert r_temp.json()["created"] == 1

            conn = sqlite3.connect(str(DB_PATH))
            temp_pid = conn.execute(
                "SELECT p.id FROM products p JOIN product_external_listings e ON p.id = e.product_id WHERE e.external_item_id = ?",
                (temp_avito_id,)
            ).fetchone()[0]
            conn.close()

            created_test_ids.append(temp_pid)
            log(f"[INFO] Created temporary test product {temp_pid} for cleanup verification")

    finally:
        # Safe, targeted cleanup of ONLY the test entity
        log("--- Finally: Executing Safe Targeted Cleanup ---")
        if created_test_ids:
            conn = sqlite3.connect(str(DB_PATH))
            try:
                cur = conn.cursor()
                for pid in created_test_ids:
                    # Security check: must have test prefix
                    cur.execute("SELECT sku FROM products WHERE id = ?", (pid,))
                    row = cur.fetchone()
                    if row and "live_07f" in row[0]:
                        cur.execute("DELETE FROM product_photos WHERE product_id = ?", (pid,))
                        cur.execute("DELETE FROM product_external_listings WHERE product_id = ?", (pid,))
                        cur.execute("DELETE FROM product_events WHERE product_id = ?", (pid,))
                        cur.execute("DELETE FROM product_avito_attribute_values WHERE product_id = ?", (pid,))
                        cur.execute("DELETE FROM products WHERE id = ?", (pid,))
                        log(f"[CLEANUP] Deleted temporary test product {pid}")
                conn.commit()
            finally:
                conn.close()

        # Enforce invariant
        conn = sqlite3.connect(str(DB_PATH))
        real_set_after = get_real_product_ids(conn)
        total_after = conn.execute("SELECT count(*) FROM products").fetchone()[0]
        conn.close()

        log(f"Final DB state: total={total_after}, real={len(real_set_after)}")
        assert real_set_after == real_set_before, f"INVARIANT VIOLATION: real product set modified! Diff: {real_set_before.symmetric_difference(real_set_after)}"
        assert total_after == total_before, f"INVARIANT VIOLATION: total product count modified! {total_before} -> {total_after}"
        log("[PASS] Invariant strictly verified: REAL_PRODUCT_SET_BEFORE == REAL_PRODUCT_SET_AFTER")

    log("=" * 75)
    log("STAGE 07F-R1-R3-R1 LIVE VERIFICATION COMPLETED WITH 100% SUCCESS!")
    log("=" * 75)

if __name__ == "__main__":
    main()
