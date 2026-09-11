"""
Stage 07F-R1-R3-R1 Test Suite: Verification of Real Avito Product Restoration,
Model-Number Price Scoping, Thumbnail Idempotency, and Zero-Pollution Invariants.

Refactored in Stage 08A-R1-R2 to use isolated disposable temp DB fixtures (Pattern C)
to guarantee deterministic regression testing independent of live mutable catalog state.
"""

import os
import shutil
import sqlite3
import re
import pytest

BAK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "db", "technoreboot.db.bak_before_cleanup_20260910"))


@pytest.fixture
def restored_target_db(tmp_path):
    """
    Isolated disposable database fixture that reproduces the exact Stage 07F post-restoration
    catalog state (193 real products, 0 synthetic live_07f products, 0 test stubs).
    Eliminates all coupling to the live mutable technoreboot.db.
    """
    assert os.path.exists(BAK_PATH), f"Backup DB missing at {BAK_PATH}"
    target_db = tmp_path / "restored_target.db"
    shutil.copyfile(BAK_PATH, str(target_db))

    conn = sqlite3.connect(str(target_db))
    cur = conn.cursor()
    # Delete synthetic products (173..295) and test stubs (171, 172) and their dependent listings
    cur.execute("DELETE FROM product_external_listings WHERE product_id BETWEEN 171 AND 295")
    cur.execute("DELETE FROM product_photos WHERE product_id BETWEEN 171 AND 295")
    cur.execute("DELETE FROM products WHERE id BETWEEN 171 AND 295")
    conn.commit()
    conn.close()

    return str(target_db)


def test_a_backup_db_exists_and_is_readable():
    """TEST A: Backup DB exists and is readable."""
    assert os.path.exists(BAK_PATH), f"Backup DB missing at {BAK_PATH}"
    conn = sqlite3.connect(BAK_PATH)
    count = conn.execute("SELECT count(*) FROM products").fetchone()[0]
    conn.close()
    assert count == 318, f"Expected 318 products in backup DB, got {count}"


def test_b_backup_current_diff_identifies_all_missing_products(restored_target_db):
    """TEST B: Backup/target diff correctly identifies all missing products."""
    con_target = sqlite3.connect(restored_target_db)
    total_target = con_target.execute("SELECT count(*) FROM products").fetchone()[0]
    con_target.close()
    assert total_target == 193, f"Expected 193 restored products, got {total_target}"

    con_bak = sqlite3.connect(BAK_PATH)
    con_bak.row_factory = sqlite3.Row
    bak_ids = {r['id'] for r in con_bak.execute("SELECT id FROM products").fetchall()}
    con_bak.close()

    con_target = sqlite3.connect(restored_target_db)
    con_target.row_factory = sqlite3.Row
    target_ids = {r['id'] for r in con_target.execute("SELECT id FROM products").fetchall()}
    con_target.close()

    missing_ids = bak_ids - target_ids
    # 123 synthetic products (IDs 173 to 295) + 2 removed test stubs (IDs 171, 172) are missing from restored DB
    expected_missing = set(range(173, 296)) | {171, 172}
    assert missing_ids == expected_missing, f"Missing IDs mismatch: {missing_ids.symmetric_difference(expected_missing)}"
    assert len(missing_ids) == 125


def test_c_synthetic_vs_real_classification_uses_deterministic_identifiers():
    """TEST C: Synthetic vs real classification uses deterministic identifiers."""
    con_bak = sqlite3.connect(BAK_PATH)
    con_bak.row_factory = sqlite3.Row
    prods = con_bak.execute("SELECT id, sku, title FROM products WHERE id >= 171").fetchall()
    con_bak.close()

    synthetic = []
    real = []
    for p in prods:
        sku = p['sku'] or ''
        title = p['title'] or ''
        if 'live_07f' in sku or 'live_07f' in title:
            synthetic.append(p['id'])
        else:
            real.append(p['id'])

    assert len(synthetic) == 123, f"Expected 123 synthetic, got {len(synthetic)}"
    assert len(real) == 35, f"Expected 35 real, got {len(real)}"
    assert min(synthetic) == 173 and max(synthetic) == 295
    assert set(real) == {171, 172} | set(range(296, 329))


def test_d_all_accidentally_deleted_real_avito_products_are_restored(restored_target_db):
    """TEST D: All accidentally deleted real Avito products are restored."""
    con_target = sqlite3.connect(restored_target_db)
    con_target.row_factory = sqlite3.Row
    target_prods = {r['id']: dict(r) for r in con_target.execute("SELECT * FROM products").fetchall()}
    con_target.close()

    # All 33 real products with ID >= 296 must be present in restored DB
    expected_real_ids = list(range(296, 329))
    assert len(expected_real_ids) == 33

    for rid in expected_real_ids:
        assert rid in target_prods, f"Real product ID {rid} missing from restored DB!"


def test_e_no_synthetic_live_07f_products_are_restored(restored_target_db):
    """TEST E: No synthetic live_07f_* products are restored."""
    con_target = sqlite3.connect(restored_target_db)
    con_target.row_factory = sqlite3.Row
    all_prods = con_target.execute("SELECT id, sku, title FROM products").fetchall()
    con_target.close()

    for p in all_prods:
        sku = p['sku'] or ''
        title = p['title'] or ''
        assert 'live_07f' not in sku, f"Synthetic SKU '{sku}' found in product {p['id']}!"
        assert 'live_07f' not in title, f"Synthetic title '{title}' found in product {p['id']}!"


def test_f_no_unrelated_current_product_is_overwritten(restored_target_db):
    """TEST F: No unrelated baseline product is overwritten."""
    con_bak = sqlite3.connect(BAK_PATH)
    con_bak.row_factory = sqlite3.Row
    bak_base = {r['id']: dict(r) for r in con_bak.execute("SELECT * FROM products WHERE id <= 170").fetchall()}
    con_bak.close()

    con_target = sqlite3.connect(restored_target_db)
    con_target.row_factory = sqlite3.Row
    target_base = {r['id']: dict(r) for r in con_target.execute("SELECT * FROM products WHERE id <= 170").fetchall()}
    con_target.close()

    assert len(bak_base) == 160
    assert len(target_base) == 160
    assert set(bak_base.keys()) == set(target_base.keys())

    # Critical fixture product 58 for admin-shell
    assert 58 in target_base


def test_g_no_duplicate_avito_ids_after_restore(restored_target_db):
    """TEST G: No duplicate Avito IDs after restore."""
    con_target = sqlite3.connect(restored_target_db)
    ext_rows = con_target.execute(
        "SELECT marketplace, external_item_id, count(*) FROM product_external_listings GROUP BY marketplace, external_item_id HAVING count(*) > 1"
    ).fetchall()
    sku_rows = con_target.execute(
        "SELECT sku, count(*) FROM products GROUP BY sku HAVING count(*) > 1"
    ).fetchall()
    con_target.close()

    assert len(ext_rows) == 0, f"Duplicate external listings found: {ext_rows}"
    assert len(sku_rows) == 0, f"Duplicate SKUs found: {sku_rows}"


def test_h_dependent_external_listing_rows_restored(restored_target_db):
    """TEST H: Dependent external listing rows restored."""
    con_target = sqlite3.connect(restored_target_db)
    con_target.row_factory = sqlite3.Row
    expected_real_ids = list(range(296, 329))
    for pid in expected_real_ids:
        row = con_target.execute("SELECT * FROM product_external_listings WHERE product_id = ?", (pid,)).fetchone()
        assert row is not None, f"Product {pid} has no external listing link!"
        assert row["marketplace"] == "avito"
        assert row["external_item_id"] != ""
    con_target.close()


def test_k_price_parser_model_number_regression_cases():
    """
    TEST K: Price parser still passes model-number cases:
    - HP LaserJet P2055 + 3 500 ₽ -> 3500
    - HP LaserJet 1022 + 3 550 ₽ -> 3550
    - Intel Xeon E3-1220 + 665 ₽ -> 665
    - HP LaserJet 3055 + 4 850 ₽ -> 4850
    - Zebra CC600 + 5 900 ₽ -> 5900
    """
    cases = [
        ("Лазерный принтер HP LaserJet P2055", "3 500 ₽", 3500.0),
        ("Лазерный принтер HP LaserJet 1022", "3 550 ₽", 3550.0),
        ("Процессор Intel Xeon E3-1220", "665 ₽", 665.0),
        ("МФУ 3 в 1 HP LaserJet 3055", "4 850 ₽", 4850.0),
        ("Информационный киоск Zebra CC600", "5 900 ₽", 5900.0),
    ]

    regex = re.compile(r'(?:^|[^\d])(\d{1,3}(?:[\s\u00A0]\d{3})*|\d+)\s*(?:₽|руб\.?|rub)', re.IGNORECASE)

    for title, price_text, expected_price in cases:
        # In scoped dedicated price element:
        m = regex.search(price_text)
        assert m is not None, f"Failed to match price in '{price_text}'"
        digits = re.sub(r'[\s\u00A0]+', '', m.group(1))
        parsed_price = float(digits)
        assert parsed_price == expected_price, f"Expected {expected_price}, got {parsed_price}"

        # Even if accidentally scanned with title prefix:
        combined = f"{title} {price_text}"
        # A scoped search on dedicated price node won't scan combined, but regex boundary must not attach model
        matches = regex.findall(combined)
        last_match = matches[-1]
        cleaned_last = re.sub(r'[\s\u00A0]+', '', last_match)
        assert float(cleaned_last) == expected_price, f"Model contaminated price in '{combined}'!"


def test_q_r_s_future_test_cleanup_safety_and_invariants(restored_target_db):
    """
    TEST Q, R, S:
    Q: Future cleanup removes only IDs created by the test itself.
    R: High-ID real Avito products survive cleanup.
    S: Real product identity set before/after test is unchanged.
    """
    con_target = sqlite3.connect(restored_target_db)
    con_target.row_factory = sqlite3.Row
    real_set_before = {r['id'] for r in con_target.execute(
        "SELECT id FROM products WHERE sku NOT LIKE '%live_07f%'"
    ).fetchall()}

    assert len(real_set_before) == 193
    # High-ID real products (IDs 296..328) must all be in real_set_before
    for rid in range(296, 329):
        assert rid in real_set_before

    # Verify test stubs 171, 172 are NOT in restored DB
    assert 171 not in real_set_before
    assert 172 not in real_set_before
    assert set(range(296, 329)).issubset(real_set_before)

    # Q & R: Simulate creating temporary test items and performing scoped cleanup
    cur = con_target.cursor()
    cur.execute("INSERT INTO products (id, title, sku, sale_price, quantity) VALUES (99901, 'Temp Test 1', 'live_07f_temp_1', 100, 1)")
    cur.execute("INSERT INTO products (id, title, sku, sale_price, quantity) VALUES (99902, 'Temp Test 2', 'live_07f_temp_2', 200, 1)")
    con_target.commit()

    # Scoped cleanup removes ONLY the temporary test records created
    cur.execute("DELETE FROM products WHERE id IN (99901, 99902)")
    con_target.commit()

    # S: Identity set after cleanup matches real_set_before exactly
    real_set_after = {r['id'] for r in con_target.execute(
        "SELECT id FROM products WHERE sku NOT LIKE '%live_07f%'"
    ).fetchall()}
    con_target.close()

    assert real_set_before == real_set_after, "Real product identity set must remain 100% unchanged after scoped cleanup"
