"""
Test Suite: Stage 07F Cleanup Safety (Requirements Section 7 & 8)

Enforces:
1. Future test cleanup removes ONLY entities created by that exact test run.
2. Broad cleanup (e.g. id >= threshold) is forbidden and fails invariant checks.
3. High-ID real Avito products survive cleanup.
4. Deterministic identity guard prevents deleting rows lacking test-run identity.
5. Invariant REAL_PRODUCT_SET_BEFORE == REAL_PRODUCT_SET_AFTER is strictly enforced.
"""

import sqlite3
import pytest

def init_test_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            sku TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            sale_price REAL,
            status TEXT DEFAULT 'draft',
            source_origin TEXT DEFAULT 'avito'
        )
    """)
    cur.execute("""
        CREATE TABLE product_external_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            marketplace TEXT NOT NULL,
            external_item_id TEXT NOT NULL
        )
    """)
    return conn

def safe_cleanup_test_entities(conn, created_test_ids: list, test_prefix: str = "live_07f_"):
    """
    Deterministic test cleanup helper:
    Only deletes products whose ID is in created_test_ids AND whose SKU starts with the test_prefix.
    Guarantees no real products can be deleted even if their ID is accidentally passed.
    """
    cur = conn.cursor()
    # Find real products before cleanup
    cur.execute("SELECT id FROM products WHERE sku NOT LIKE ? AND sku NOT LIKE ?", (f"%{test_prefix}%", f"AVITO-{test_prefix}%"))
    real_before = {r[0] for r in cur.fetchall()}

    deleted_count = 0
    for pid in created_test_ids:
        cur.execute("SELECT sku FROM products WHERE id = ?", (pid,))
        row = cur.fetchone()
        if not row:
            continue
        sku = row[0]
        # Strict guard: MUST contain deterministic test prefix
        if test_prefix not in sku:
            raise ValueError(f"SECURITY VIOLATION: Attempted to delete non-test product {pid} with SKU '{sku}'!")
        cur.execute("DELETE FROM product_external_listings WHERE product_id = ?", (pid,))
        cur.execute("DELETE FROM products WHERE id = ?", (pid,))
        deleted_count += 1

    conn.commit()

    # Verify invariant
    cur.execute("SELECT id FROM products WHERE sku NOT LIKE ? AND sku NOT LIKE ?", (f"%{test_prefix}%", f"AVITO-{test_prefix}%"))
    real_after = {r[0] for r in cur.fetchall()}
    assert real_after == real_before, f"INVARIANT VIOLATED: real products changed! {real_before} -> {real_after}"
    return deleted_count


def test_safe_cleanup_removes_only_proven_synthetic_and_preserves_high_id_real():
    """
    Section 8 Requirement:
    Given:
    - 3 synthetic live_07f_* products (IDs 301, 302, 303);
    - 2 real Avito products created in same high-ID range (IDs 304, 305);
    Cleanup must:
    - remove exactly 3 synthetic;
    - preserve exactly 2 real.
    """
    conn = init_test_db()
    cur = conn.cursor()

    # 1. Base products
    for i in range(1, 6):
        cur.execute("INSERT INTO products (id, sku, title, sale_price) VALUES (?, ?, ?, ?)",
                    (i, f"BASE-{i:03d}", f"Base Item {i}", 1000.0 * i))

    # 2. Synthetic products with high IDs
    synth_ids = [301, 302, 303]
    for sid in synth_ids:
        cur.execute("INSERT INTO products (id, sku, title, sale_price) VALUES (?, ?, ?, ?)",
                    (sid, f"AVITO-live_07f_test_{sid}", f"Synthetic Test {sid}", 5000.0))

    # 3. Real Avito products in SAME high-ID range
    real_ids = [304, 305]
    cur.execute("INSERT INTO products (id, sku, title, sale_price) VALUES (?, ?, ?, ?)",
                (304, "AVITO-8250874053", "Лазерный принтер HP LaserJet P2055", 3500.0))
    cur.execute("INSERT INTO products (id, sku, title, sale_price) VALUES (?, ?, ?, ?)",
                (305, "AVITO-4889848898", "Процессор Intel Xeon E3-1220", 665.0))
    conn.commit()

    # Pre-check
    all_pids_before = {r[0] for r in cur.execute("SELECT id FROM products").fetchall()}
    assert all_pids_before == {1, 2, 3, 4, 5, 301, 302, 303, 304, 305}

    # Perform safe cleanup
    deleted = safe_cleanup_test_entities(conn, created_test_ids=synth_ids, test_prefix="live_07f_")
    assert deleted == 3

    # Post-check
    all_pids_after = {r[0] for r in cur.execute("SELECT id FROM products").fetchall()}
    assert all_pids_after == {1, 2, 3, 4, 5, 304, 305}

    # Verify real products 304 and 305 are 100% intact
    p304 = cur.execute("SELECT * FROM products WHERE id = 304").fetchone()
    assert p304["sku"] == "AVITO-8250874053"
    assert p304["sale_price"] == 3500.0

    p305 = cur.execute("SELECT * FROM products WHERE id = 305").fetchone()
    assert p305["sku"] == "AVITO-4889848898"
    assert p305["sale_price"] == 665.0


def test_broad_id_range_cleanup_fails_invariant():
    """
    Proves that cleanup based on 'id >= threshold' violates the business invariant:
    REAL_PRODUCT_SET_BEFORE == REAL_PRODUCT_SET_AFTER.
    """
    conn = init_test_db()
    cur = conn.cursor()

    cur.execute("INSERT INTO products (id, sku, title) VALUES (1, 'BASE-001', 'Base 1')")
    cur.execute("INSERT INTO products (id, sku, title) VALUES (301, 'AVITO-live_07f_01', 'Synthetic 1')")
    cur.execute("INSERT INTO products (id, sku, title) VALUES (302, 'AVITO-8250874053', 'Real HP 2055')")
    conn.commit()

    real_before = {r[0] for r in cur.execute("SELECT id FROM products WHERE sku NOT LIKE '%live_07f%'").fetchall()}
    assert real_before == {1, 302}

    # Naive broad cleanup: DELETE FROM products WHERE id >= 300
    cur.execute("DELETE FROM products WHERE id >= 300")
    conn.commit()

    real_after = {r[0] for r in cur.execute("SELECT id FROM products WHERE sku NOT LIKE '%live_07f%'").fetchall()}
    assert real_after == {1}

    # Invariant assertion MUST fail
    with pytest.raises(AssertionError):
        assert real_after == real_before, "Invariant check must detect accidental deletion of real product 302!"


def test_safe_cleanup_rejects_deleting_real_product_without_test_identity():
    """
    Ensures that even if a caller accidentally passes a real product ID in created_test_ids,
    the deterministic identity guard blocks deletion.
    """
    conn = init_test_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (id, sku, title) VALUES (297, 'AVITO-8250874053', 'Real HP 2055')")
    conn.commit()

    # Attempting to delete product 297 with test_prefix='live_07f_' must raise ValueError
    with pytest.raises(ValueError) as excinfo:
        safe_cleanup_test_entities(conn, created_test_ids=[297], test_prefix="live_07f_")
    assert "SECURITY VIOLATION" in str(excinfo.value)

    # Confirm product was NOT deleted
    row = cur.execute("SELECT id FROM products WHERE id = 297").fetchone()
    assert row is not None
