#!/usr/bin/env python3
"""
TECHNOREBOOT — Safe Product Catalog Cleanup
Clears only products and product-dependent records (products, photos, external listings,
attributes, cards, events, stock movements; sets sale_items.product_id to NULL).
Strictly preserves categories, customers, sales receipts, repairs, and organization settings.
"""

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "db" / "technoreboot.db"
STORAGE_DIR = PROJECT_ROOT / "data" / "storage" / "product_photos"
ARCHIVE_STORAGE_DIR = PROJECT_ROOT / "data" / "storage" / f"product_photos_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def run_cleanup():
    assert DB_PATH.exists(), f"Database not found at {DB_PATH}"

    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Tables to inspect
    all_tables = [
        "products", "product_photos", "product_external_listings",
        "product_avito_attribute_values", "product_cards", "product_events",
        "stock_movements", "sale_items", "sales", "repair_orders",
        "repair_status_history", "categories", "customers",
        "organization_settings", "audit_log", "avito_categories",
        "avito_attribute_definitions", "avito_attribute_options"
    ]

    print("\n--- BEFORE CLEANUP ROW COUNTS ---")
    before_counts = {}
    for t in all_tables:
        try:
            cur.execute(f"SELECT count(*) FROM {t}")
            cnt = cur.fetchone()[0]
            before_counts[t] = cnt
            print(f"  {t}: {cnt}")
        except sqlite3.OperationalError as e:
            print(f"  {t}: ERROR ({e})")

    # Perform cleanup inside a transaction
    try:
        cur.execute("BEGIN TRANSACTION")

        # 1. Detach sale_items
        cur.execute("UPDATE sale_items SET product_id = NULL WHERE product_id IS NOT NULL")
        detached_sales = cur.rowcount
        print(f"\nDetached product_id from {detached_sales} sale_items rows.")

        # 2. Delete product-dependent tables
        for dep_table in [
            "product_photos",
            "product_external_listings",
            "product_avito_attribute_values",
            "product_cards",
            "product_events",
            "stock_movements"
        ]:
            cur.execute(f"DELETE FROM {dep_table}")
            print(f"Cleared table: {dep_table} ({cur.rowcount} rows deleted)")

        # 3. Delete products
        cur.execute("DELETE FROM products")
        print(f"Cleared table: products ({cur.rowcount} rows deleted)")

        conn.commit()
        print("\nDatabase transaction committed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"\nERROR: Cleanup failed, transaction rolled back: {e}")
        raise

    print("\n--- AFTER CLEANUP ROW COUNTS ---")
    after_counts = {}
    for t in all_tables:
        try:
            cur.execute(f"SELECT count(*) FROM {t}")
            cnt = cur.fetchone()[0]
            after_counts[t] = cnt
            print(f"  {t}: {cnt}")
        except sqlite3.OperationalError as e:
            print(f"  {t}: ERROR ({e})")

    # Assertions
    assert after_counts["products"] == 0, "Products count must be 0"
    assert after_counts["product_photos"] == 0, "Product photos count must be 0"
    assert after_counts["product_external_listings"] == 0, "External listings count must be 0"
    assert after_counts["categories"] == before_counts["categories"], "Categories must be preserved"
    assert after_counts["customers"] == before_counts["customers"], "Customers must be preserved"
    assert after_counts["sales"] == before_counts["sales"], "Sales must be preserved"
    assert after_counts["repair_orders"] == before_counts["repair_orders"], "Repairs must be preserved"
    assert after_counts["organization_settings"] == before_counts["organization_settings"], "Org settings preserved"

    # Archive physical photo files
    if STORAGE_DIR.exists():
        files = [f for f in STORAGE_DIR.iterdir() if f.is_file()]
        if files:
            print(f"\nArchiving {len(files)} product photo files to {ARCHIVE_STORAGE_DIR}...")
            ARCHIVE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            for f in files:
                shutil.move(str(f), str(ARCHIVE_STORAGE_DIR / f.name))
            print(f"Successfully archived photos. {STORAGE_DIR} is now clean for fresh import.")
        else:
            print(f"\nPhoto storage directory {STORAGE_DIR} is already empty.")
    else:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\nCreated empty photo storage directory at {STORAGE_DIR}.")

    print("\n==================================================================")
    print("SUCCESS: Product catalog cleared cleanly! Ready for fresh Avito import.")
    print("==================================================================")

if __name__ == "__main__":
    run_cleanup()
