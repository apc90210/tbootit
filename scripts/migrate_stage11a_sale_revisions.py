import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATHS = [
    REPO_ROOT / "data" / "db" / "technoreboot.db",
    REPO_ROOT / "core" / "technoreboot.db",
]

def migrate_db(db_path: Path):
    if not db_path.exists():
        print(f"Skipping non-existent DB: {db_path}")
        return
    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Check columns of sales
    cur.execute("PRAGMA table_info('sales');")
    sales_cols = [r[1] for r in cur.fetchall()]
    if "revision_count" not in sales_cols:
        print("  Adding revision_count to sales...")
        cur.execute("ALTER TABLE sales ADD COLUMN revision_count INTEGER NOT NULL DEFAULT '0';")
    else:
        print("  revision_count already exists in sales.")

    # Check sale_revisions table
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sale_revisions';")
    if not cur.fetchone():
        print("  Creating sale_revisions table...")
        cur.execute("""
            CREATE TABLE sale_revisions (
                id INTEGER NOT NULL PRIMARY KEY,
                sale_id INTEGER NOT NULL,
                revision_no INTEGER NOT NULL,
                changed_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                changed_by VARCHAR,
                comment TEXT,
                before_snapshot TEXT NOT NULL,
                after_snapshot TEXT NOT NULL,
                structured_diff TEXT NOT NULL,
                FOREIGN KEY(sale_id) REFERENCES sales (id)
            );
        """)
        cur.execute("CREATE INDEX ix_sale_revisions_id ON sale_revisions (id);")
        cur.execute("CREATE INDEX ix_sale_revisions_sale_id ON sale_revisions (sale_id);")
    else:
        print("  sale_revisions table already exists.")

    conn.commit()
    conn.close()
    print(f"Migration completed for {db_path}.")

if __name__ == "__main__":
    for p in DB_PATHS:
        migrate_db(p)
