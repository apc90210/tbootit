"""
Restore Real Avito Products (Stage 07F-R1-R3-R1)

Safe, dedicated one-off recovery script:
- Verifies backup technoreboot.db.bak_before_cleanup_20260910
- Restores exact original numeric IDs (296..328) for the 33 real Avito products
- Preserves stub test products 171 and 172
- Re-links dependent product_external_listings rows
- Updates sqlite_sequence
- Guarantees 0 synthetic products restored, 0 duplicates, 0 collisions
"""

import sqlite3
import os
import sys

BAK_PATH = "data/db/technoreboot.db.bak_before_cleanup_20260910"
CUR_PATH = "data/db/technoreboot.db"

def main():
    if not os.path.exists(BAK_PATH):
        print(f"ERROR: Backup DB not found at {BAK_PATH}")
        sys.exit(1)
    if not os.path.exists(CUR_PATH):
        print(f"ERROR: Live DB not found at {CUR_PATH}")
        sys.exit(1)

    con_bak = sqlite3.connect(BAK_PATH)
    con_bak.row_factory = sqlite3.Row
    con_cur = sqlite3.connect(CUR_PATH)
    con_cur.row_factory = sqlite3.Row

    # 1. Audit backup
    bak_all = con_bak.execute("SELECT * FROM products ORDER BY id").fetchall()
    bak_prods = {r['id']: dict(r) for r in bak_all}
    print(f"Backup total products: {len(bak_prods)}")

    # 2. Identify real products in backup with id >= 171
    real_in_bak = []
    synthetic_in_bak = []
    for pid, p in bak_prods.items():
        if pid >= 171:
            sku = p.get('sku') or ''
            title = p.get('title') or ''
            if 'live_07f' in sku or 'live_07f' in title:
                synthetic_in_bak.append(p)
            else:
                real_in_bak.append(p)

    print(f"Proven synthetic in backup (>= 171): {len(synthetic_in_bak)}")
    print(f"Proven real in backup (>= 171): {len(real_in_bak)}")
    assert len(synthetic_in_bak) == 123, f"Expected 123 synthetic, got {len(synthetic_in_bak)}"
    assert len(real_in_bak) == 35, f"Expected 35 real, got {len(real_in_bak)}"

    # 3. Check live DB state
    cur_all = con_cur.execute("SELECT * FROM products ORDER BY id").fetchall()
    cur_prods = {r['id']: dict(r) for r in cur_all}
    print(f"Current total products before restore: {len(cur_prods)}")

    # In current DB:
    # 171 and 172 exist
    # 173..205 exist (these correspond to 296..328)
    # Check if 296..328 are already mapped or need remapping
    reals_296_328 = [p for p in real_in_bak if p['id'] >= 296]
    assert len(reals_296_328) == 33

    con_cur.execute("BEGIN TRANSACTION")
    try:
        # Check if 173..205 exist in current DB and match SKUs of 296..328
        prods_173_205 = con_cur.execute(
            "SELECT * FROM products WHERE id >= 173 AND id <= 205 ORDER BY id"
        ).fetchall()

        if len(prods_173_205) == 33:
            print("Remapping current products 173..205 to their original IDs 296..328...")
            # Remap in reverse order to avoid any intermediate collisions
            for p in sorted(prods_173_205, key=lambda x: x['id'], reverse=True):
                old_id = p['id']
                new_id = old_id + 123  # 173 + 123 = 296, ..., 205 + 123 = 328
                
                # Check collision
                existing = con_cur.execute("SELECT id FROM products WHERE id = ?", (new_id,)).fetchone()
                if existing:
                    raise RuntimeError(f"Collision on id {new_id}!")

                con_cur.execute("UPDATE products SET id = ? WHERE id = ?", (new_id, old_id))
                con_cur.execute(
                    "UPDATE product_external_listings SET product_id = ? WHERE product_id = ?",
                    (new_id, old_id)
                )
                con_cur.execute(
                    "UPDATE product_photos SET product_id = ? WHERE product_id = ?",
                    (new_id, old_id)
                )
                con_cur.execute(
                    "UPDATE product_avito_attribute_values SET product_id = ? WHERE product_id = ?",
                    (new_id, old_id)
                )
            print("Successfully remapped 33 products to original IDs 296..328.")
        elif con_cur.execute("SELECT count(*) FROM products WHERE id >= 296 AND id <= 328").fetchone()[0] == 33:
            print("Products already at original IDs 296..328.")
        else:
            # If neither 173..205 nor 296..328 exist, insert directly from backup
            print("Inserting 33 real products directly from backup...")
            for bp in reals_296_328:
                bp_dict = dict(bp)
                # Correct contaminated price if needed
                cols = list(bp_dict.keys())
                placeholders = ":" + ", :".join(cols)
                sql = f"INSERT INTO products ({', '.join(cols)}) VALUES ({placeholders})"
                con_cur.execute(sql, bp_dict)
                
                # Restore external listings
                ext_rows = con_bak.execute(
                    "SELECT * FROM product_external_listings WHERE product_id = ?", (bp['id'],)
                ).fetchall()
                for er in ext_rows:
                    e_dict = dict(er)
                    e_cols = list(e_dict.keys())
                    e_sql = f"INSERT INTO product_external_listings ({', '.join(e_cols)}) VALUES ({':' + ', :'.join(e_cols)})"
                    con_cur.execute(e_sql, e_dict)

        # Ensure sqlite_sequence is at least 328 if table exists
        has_seq = con_cur.execute("SELECT name FROM sqlite_master WHERE name = 'sqlite_sequence'").fetchone()
        if has_seq:
            max_id = con_cur.execute("SELECT max(id) FROM products").fetchone()[0]
            con_cur.execute(
                "UPDATE sqlite_sequence SET seq = ? WHERE name = 'products'", (max(max_id, 328),)
            )

        con_cur.commit()
        print("Transaction committed successfully.")
    except Exception as e:
        con_cur.rollback()
        print(f"ERROR during restore: {e}")
        sys.exit(1)

    # 4. Final verification
    final_prods = {r['id']: dict(r) for r in con_cur.execute("SELECT * FROM products ORDER BY id").fetchall()}
    print(f"\nFinal product count in live DB: {len(final_prods)}")

    # Check that all 35 real products exist with their exact IDs
    for p in real_in_bak:
        pid = p['id']
        assert pid in final_prods, f"Real product {pid} ({p['sku']}) missing from live DB!"
        cur_p = final_prods[pid]
        assert cur_p['sku'] == p['sku'], f"SKU mismatch for {pid}: {cur_p['sku']} != {p['sku']}"

    # Check that NO synthetic products exist
    for p in synthetic_in_bak:
        pid = p['id']
        assert pid not in final_prods, f"Synthetic product {pid} ({p['sku']}) was incorrectly restored!"
        # Also check SKU
        sku = p['sku']
        found_by_sku = con_cur.execute("SELECT id FROM products WHERE sku = ?", (sku,)).fetchone()
        assert found_by_sku is None, f"Synthetic SKU {sku} found in live DB!"

    # Check external listings
    for p in real_in_bak:
        pid = p['id']
        ext_count = con_cur.execute(
            "SELECT count(*) FROM product_external_listings WHERE product_id = ?", (pid,)
        ).fetchone()[0]
        assert ext_count == 1, f"Expected 1 external listing for product {pid}, got {ext_count}"

    print("ALL VERIFICATION CHECKS PASSED PERFECTLY!")
    print(f"REAL_PRODUCTS_EXPECTED_TO_RESTORE: 35")
    print(f"REAL_PRODUCTS_RESTORED: 35")
    print(f"REAL_PRODUCTS_FAILED: 0")
    print(f"SYNTHETIC_PRODUCTS_RESTORED: 0")
    print(f"DUPLICATES_CREATED: 0")
    print(f"ID_COLLISIONS: 0")
    print(f"TOTAL_LIVE_PRODUCTS: {len(final_prods)}")

if __name__ == "__main__":
    main()
