#!/usr/bin/env python3
"""
VDS Database Barcode Population & Integrity Migration Script
Stage 05B - Mobile POS Barcode Hotfix
"""

import os
import sys
import shutil
import sqlite3
import hashlib
from datetime import datetime, timezone

DB_PATH = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DB_PATH", "/srv/technoreboot/data/db/technoreboot.db")
BACKUPS_DIR = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("BACKUPS_DIR", "/srv/technoreboot/data/backups")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def check_integrity(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA quick_check;")
    qc = cur.fetchone()[0]
    if qc != "ok":
        raise RuntimeError(f"Integrity check failed: {qc}")
    cur.execute("PRAGMA foreign_key_check;")
    fk = cur.fetchall()
    if fk:
        raise RuntimeError(f"Foreign key violations found: {fk}")
    return qc, fk

def get_table_counts(conn):
    cur = conn.cursor()
    counts = {}
    for table in ["products", "sales", "repair_orders", "product_photos", "product_external_listings"]:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
        except sqlite3.OperationalError:
            counts[table] = -1
    return counts

def main():
    print("=" * 65)
    print("TECHNOREBOOT VDS: Stage 05B Barcode Population & Invariant Guard")
    print(f"Target DB: {DB_PATH}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 65)

    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    # 1. Baseline inspection
    pre_sha256 = compute_sha256(DB_PATH)
    pre_size = os.path.getsize(DB_PATH)
    print(f"[1/6] Live DB Size: {pre_size} bytes, SHA256: {pre_sha256}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    qc, fk = check_integrity(conn)
    pre_counts = get_table_counts(conn)
    print(f"[2/6] Live DB Integrity: quick_check={qc}, foreign_key_check=OK")
    print(f"      Pre-counts: {pre_counts}")

    if pre_counts["sales"] != 70:
        print(f"WARNING: Sales count is {pre_counts['sales']}, expected 70", file=sys.stderr)
    if pre_counts["repair_orders"] != 2:
        print(f"WARNING: Repair orders count is {pre_counts['repair_orders']}, expected 2", file=sys.stderr)

    # 2. Create Pre-deploy Backup
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_subdir = os.path.join(BACKUPS_DIR, f"pre_stage05b_{timestamp_str}")
    os.makedirs(backup_subdir, exist_ok=True)
    backup_db_path = os.path.join(backup_subdir, "technoreboot.db")
    shutil.copy2(DB_PATH, backup_db_path)
    
    backup_sha256 = compute_sha256(backup_db_path)
    if backup_sha256 != pre_sha256:
        print(f"ERROR: Backup SHA256 mismatch! {backup_sha256} vs {pre_sha256}", file=sys.stderr)
        sys.exit(1)

    # Verify backup integrity
    b_conn = sqlite3.connect(backup_db_path)
    check_integrity(b_conn)
    b_conn.close()
    print(f"[3/6] Pre-deploy backup created successfully at: {backup_db_path}")

    # 3. Apply Barcode Population
    print("[4/6] Updating product barcodes...")
    cur = conn.cursor()
    cur.execute("SELECT id, sku, title, barcode, status FROM products ORDER BY id")
    all_products = cur.fetchall()
    print(f"      Total products found: {len(all_products)}")

    # Update in transaction
    conn.execute("BEGIN TRANSACTION;")
    try:
        # Clear existing barcodes first to prevent intermediate collisions (e.g. product 327 had 200000000330)
        cur.execute("UPDATE products SET barcode = NULL")
        updated_count = 0
        for pid, sku, title, current_barcode, status in all_products:
            # Canonical 12-digit barcode formula matching physical price tags
            expected_barcode = str(200000000230 + (pid - 1))
            cur.execute(
                "UPDATE products SET barcode = ? WHERE id = ?",
                (expected_barcode, pid)
            )
            updated_count += 1

        print(f"      Updated {updated_count} products with canonical barcodes.")

        # Verify uniqueness and completeness
        cur.execute("SELECT COUNT(*) FROM products WHERE barcode IS NULL OR barcode = ''")
        null_count = cur.fetchone()[0]
        if null_count > 0:
            raise RuntimeError(f"Found {null_count} products with NULL/empty barcode after update!")

        cur.execute("SELECT COUNT(DISTINCT barcode) FROM products")
        distinct_count = cur.fetchone()[0]
        if distinct_count != len(all_products):
            raise RuntimeError(f"Barcode uniqueness violation: {distinct_count} distinct vs {len(all_products)} total!")

        # Verify specific key products
        cur.execute("SELECT id, barcode, title FROM products WHERE id IN (1, 101, 229, 230, 327, 423)")
        samples = cur.fetchall()
        print("      Verification samples:")
        for spid, sbarcode, stitle in samples:
            print(f"        Product {spid}: barcode={sbarcode} title={stitle[:35]}")

        # Invariant checks
        post_counts = get_table_counts(conn)
        print(f"[5/6] Post-update counts: {post_counts}")
        if post_counts["sales"] != pre_counts["sales"]:
            raise RuntimeError(f"Sales count mutated! {pre_counts['sales']} -> {post_counts['sales']}")
        if post_counts["repair_orders"] != pre_counts["repair_orders"]:
            raise RuntimeError(f"Repair orders mutated! {pre_counts['repair_orders']} -> {post_counts['repair_orders']}")
        if post_counts["products"] != pre_counts["products"]:
            raise RuntimeError(f"Products count mutated! {pre_counts['products']} -> {post_counts['products']}")

        # SQLite integrity check
        check_integrity(conn)

        conn.commit()
        print("[6/6] Transaction committed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: Transaction failed and was rolled back: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    post_sha256 = compute_sha256(DB_PATH)
    print("=" * 65)
    print("STAGE 05B BARCODE MIGRATION FINISHED SUCCESSFULLY")
    print(f"Post DB SHA256: {post_sha256}")
    print(f"Backup location: {backup_db_path}")
    print("=" * 65)

if __name__ == "__main__":
    main()
