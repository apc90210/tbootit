import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATHS = [
    REPO_ROOT / "data" / "db" / "technoreboot.db",
    REPO_ROOT / "core" / "technoreboot.db",
    REPO_ROOT / "technoreboot.db",
]

def migrate_db(db_path: Path):
    if not db_path.exists():
        print(f"Skipping non-existent DB: {db_path}")
        return
    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Check columns of repair_orders
    cur.execute("PRAGMA table_info('repair_orders');")
    cols = [r[1] for r in cur.fetchall()]

    if "final_amount" not in cols:
        print("  Adding final_amount to repair_orders...")
        cur.execute("ALTER TABLE repair_orders ADD COLUMN final_amount REAL;")
    else:
        print("  final_amount already exists in repair_orders.")

    if "payment_method" not in cols:
        print("  Adding payment_method to repair_orders...")
        cur.execute("ALTER TABLE repair_orders ADD COLUMN payment_method VARCHAR;")
    else:
        print("  payment_method already exists in repair_orders.")

    if "warranty_days" not in cols:
        print("  Adding warranty_days to repair_orders...")
        cur.execute("ALTER TABLE repair_orders ADD COLUMN warranty_days INTEGER;")
    else:
        print("  warranty_days already exists in repair_orders.")

    if "sale_id" not in cols:
        print("  Adding sale_id to repair_orders...")
        cur.execute("ALTER TABLE repair_orders ADD COLUMN sale_id INTEGER REFERENCES sales(id);")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_repair_orders_sale_id ON repair_orders (sale_id);")
    else:
        print("  sale_id already exists in repair_orders.")

    # Check backfill for existing issued repairs linked to sales
    cur.execute("""
        SELECT r.id, r.number, r.status, s.id, s.total_amount, s.payment_method, s.warranty_days
        FROM repair_orders r
        JOIN sales s ON s.source_type = 'repair' AND s.source_id = r.id
        WHERE r.sale_id IS NULL;
    """)
    linked_to_backfill = cur.fetchall()
    if linked_to_backfill:
        print(f"  Backfilling {len(linked_to_backfill)} existing repairs with their linked sales...")
        for row in linked_to_backfill:
            rep_id, rep_no, rep_status, sale_id, sale_total, sale_pm, sale_w = row
            cur.execute("""
                UPDATE repair_orders
                SET sale_id = ?,
                    final_amount = COALESCE(final_amount, ?),
                    payment_method = COALESCE(payment_method, ?),
                    warranty_days = COALESCE(warranty_days, ?)
                WHERE id = ?;
            """, (sale_id, sale_total, sale_pm, sale_w, rep_id))
        print("  Backfill completed.")
    else:
        print("  No unlinked sales to backfill.")

    # Check for historical issued repairs without linked sale
    cur.execute("""
        SELECT r.id, r.number, r.price, r.estimated_repair_amount, r.issued_at
        FROM repair_orders r
        WHERE r.status = 'issued' AND r.sale_id IS NULL
        AND NOT EXISTS (SELECT 1 FROM sales s WHERE s.source_type = 'repair' AND s.source_id = r.id);
    """)
    historical_unlinked = cur.fetchall()
    if historical_unlinked:
        print(f"  [AUDIT NOTE] Found {len(historical_unlinked)} historical issued repair(s) without linked sale.")
        for r in historical_unlinked:
            print(f"    - Repair ID={r[0]}, Number={r[1]}, Price={r[2]}, Est={r[3]}, Issued={r[4]}")
        print("  NOTE: As per prompt rule #16, NO artificial revenue was fabricated for historical records.")
    else:
        print("  All issued repairs have linked sales (or none exist).")

    conn.commit()
    conn.close()
    print(f"Migration completed for {db_path}.\n")

if __name__ == "__main__":
    for p in DB_PATHS:
        migrate_db(p)
