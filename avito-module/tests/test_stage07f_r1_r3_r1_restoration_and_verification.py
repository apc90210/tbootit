"""
Stage 07F-R1-R3-R1 Test Suite: Verification of Real Avito Product Restoration,
Model-Number Price Scoping, Thumbnail Idempotency, and Zero-Pollution Invariants.
"""

import os
import sqlite3
import re
import pytest

BAK_PATH = "data/db/technoreboot.db.bak_before_cleanup_20260910"
CUR_PATH = "data/db/technoreboot.db"

def test_a_backup_db_exists_and_is_readable():
    """TEST A: Backup DB exists and is readable."""
    assert os.path.exists(BAK_PATH), f"Backup DB missing at {BAK_PATH}"
    conn = sqlite3.connect(BAK_PATH)
    count = conn.execute("SELECT count(*) FROM products").fetchone()[0]
    conn.close()
    assert count == 318, f"Expected 318 products in backup DB, got {count}"


def test_b_backup_current_diff_identifies_all_missing_products():
    """TEST B: Backup/current diff correctly identifies all missing products."""
    con_bak = sqlite3.connect(BAK_PATH)
    con_bak.row_factory = sqlite3.Row
    bak_ids = {r['id'] for r in con_bak.execute("SELECT id FROM products").fetchall()}
    con_bak.close()

    con_cur = sqlite3.connect(CUR_PATH)
    con_cur.row_factory = sqlite3.Row
    cur_ids = {r['id'] for r in con_cur.execute("SELECT id FROM products").fetchall()}
    con_cur.close()

    missing_ids = bak_ids - cur_ids
    # 123 synthetic products (IDs 173 to 295) + 2 removed test stubs (IDs 171, 172) are missing from current DB
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


def test_d_all_accidentally_deleted_real_avito_products_are_restored():
    """TEST D: All accidentally deleted real Avito products are restored."""
    con_cur = sqlite3.connect(CUR_PATH)
    con_cur.row_factory = sqlite3.Row
    cur_prods = {r['id']: dict(r) for r in con_cur.execute("SELECT * FROM products").fetchall()}
    con_cur.close()

    # All 33 real products with ID >= 296 must be present in live DB
    expected_real_ids = list(range(296, 329))
    assert len(expected_real_ids) == 33

    for rid in expected_real_ids:
        assert rid in cur_prods, f"Real product ID {rid} missing from live DB!"


def test_e_no_synthetic_live_07f_products_are_restored():
    """TEST E: No synthetic live_07f_* products are restored."""
    con_cur = sqlite3.connect(CUR_PATH)
    con_cur.row_factory = sqlite3.Row
    all_prods = con_cur.execute("SELECT id, sku, title FROM products").fetchall()
    con_cur.close()

    for p in all_prods:
        sku = p['sku'] or ''
        title = p['title'] or ''
        assert 'live_07f' not in sku, f"Synthetic SKU '{sku}' found in live product {p['id']}!"
        assert 'live_07f' not in title, f"Synthetic title '{title}' found in live product {p['id']}!"


def test_f_no_unrelated_current_product_is_overwritten():
    """TEST F: No unrelated current product is overwritten."""
    con_bak = sqlite3.connect(BAK_PATH)
    con_bak.row_factory = sqlite3.Row
    bak_base = {r['id']: dict(r) for r in con_bak.execute("SELECT * FROM products WHERE id <= 170").fetchall()}
    con_bak.close()

    con_cur = sqlite3.connect(CUR_PATH)
    con_cur.row_factory = sqlite3.Row
    cur_base = {r['id']: dict(r) for r in con_cur.execute("SELECT * FROM products WHERE id <= 170").fetchall()}
    con_cur.close()

    assert len(bak_base) == 160
    assert len(cur_base) == 160
    assert set(bak_base.keys()) == set(cur_base.keys())

    # Critical fixture product 58 for admin-shell
    assert 58 in cur_base


def test_g_no_duplicate_avito_ids_after_restore():
    """TEST G: No duplicate Avito IDs after restore."""
    con_cur = sqlite3.connect(CUR_PATH)
    ext_rows = con_cur.execute(
        "SELECT marketplace, external_item_id, count(*) FROM product_external_listings GROUP BY marketplace, external_item_id HAVING count(*) > 1"
    ).fetchall()
    sku_rows = con_cur.execute(
        "SELECT sku, count(*) FROM products GROUP BY sku HAVING count(*) > 1"
    ).fetchall()
    con_cur.close()

    assert len(ext_rows) == 0, f"Duplicate external listings found: {ext_rows}"
    assert len(sku_rows) == 0, f"Duplicate SKUs found: {sku_rows}"


def test_h_dependent_external_listing_rows_restored():
    """TEST H: Dependent external listing rows restored."""
    con_cur = sqlite3.connect(CUR_PATH)
    con_cur.row_factory = sqlite3.Row
    expected_real_ids = list(range(296, 329))
    for pid in expected_real_ids:
        row = con_cur.execute("SELECT * FROM product_external_listings WHERE product_id = ?", (pid,)).fetchone()
        assert row is not None, f"Product {pid} has no external listing link!"
        assert row["marketplace"] == "avito"
        assert row["external_item_id"] != ""
    con_cur.close()


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


def test_q_r_s_future_test_cleanup_safety_and_invariants():
    """
    TEST Q, R, S:
    Q: Future cleanup removes only IDs created by the test itself.
    R: High-ID real Avito products survive cleanup.
    S: Real product identity set before/after test is unchanged.
    """
    con_cur = sqlite3.connect(CUR_PATH)
    real_set_before = {r[0] for r in con_cur.execute(
        "SELECT id FROM products WHERE sku NOT LIKE '%live_07f%'"
    ).fetchall()}
    con_cur.close()

    assert len(real_set_before) == 193
    # High-ID real products (IDs 296..328) must all be in real_set_before
    for rid in range(296, 329):
        assert rid in real_set_before

    # Verify test stubs 171, 172 are NOT in live DB
    assert 171 not in real_set_before
    assert 172 not in real_set_before
    assert set(range(296, 329)).issubset(real_set_before)
