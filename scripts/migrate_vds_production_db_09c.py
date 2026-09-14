import subprocess
import json

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_migration_script = """
import sqlite3, hashlib, json

LIVE_DB_PATH = '/srv/technoreboot/data/db/technoreboot.db'

conn = sqlite3.connect(LIVE_DB_PATH)
cur = conn.cursor()

# 1. Pre-migration check
tables_before = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
products_before = cur.execute("SELECT count(*) FROM products;").fetchone()[0] if "products" in tables_before else 0
sales_before = cur.execute("SELECT count(*) FROM sales;").fetchone()[0] if "sales" in tables_before else 0
photos_before = cur.execute("SELECT count(*) FROM product_photos;").fetchone()[0] if "product_photos" in tables_before else 0

# 2. Migration DDL
migration_sql = '''
CREATE TABLE IF NOT EXISTS avito_post_sale_tasks (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    external_listing_id INTEGER,
    avito_listing_id VARCHAR NOT NULL,
    listing_url VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'suggested',
    action VARCHAR NOT NULL DEFAULT 'deactivate',
    requested_by VARCHAR,
    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    finished_at DATETIME,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    execution_mode VARCHAR NOT NULL DEFAULT 'extension',
    result_metadata TEXT,
    CONSTRAINT uix_sale_prod_avito_deact UNIQUE (sale_id, product_id, avito_listing_id, action),
    FOREIGN KEY(sale_id) REFERENCES sales (id),
    FOREIGN KEY(product_id) REFERENCES products (id),
    FOREIGN KEY(external_listing_id) REFERENCES product_external_listings (id)
);
CREATE INDEX IF NOT EXISTS ix_avito_post_sale_tasks_id ON avito_post_sale_tasks (id);
CREATE INDEX IF NOT EXISTS ix_avito_post_sale_tasks_sale_id ON avito_post_sale_tasks (sale_id);
CREATE INDEX IF NOT EXISTS ix_avito_post_sale_tasks_product_id ON avito_post_sale_tasks (product_id);
CREATE INDEX IF NOT EXISTS ix_avito_post_sale_tasks_external_listing_id ON avito_post_sale_tasks (external_listing_id);
CREATE INDEX IF NOT EXISTS ix_avito_post_sale_tasks_avito_listing_id ON avito_post_sale_tasks (avito_listing_id);
CREATE INDEX IF NOT EXISTS ix_avito_post_sale_tasks_status ON avito_post_sale_tasks (status);
'''

cur.executescript(migration_sql)
conn.commit()

# 3. Quick check
quick_check = cur.execute("PRAGMA quick_check;").fetchone()[0]

# 4. Post-migration introspection
tables_after = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
avito_tasks_exists = ("avito_post_sale_tasks" in tables_after)
avito_tasks_rows = cur.execute("SELECT count(*) FROM avito_post_sale_tasks;").fetchone()[0] if avito_tasks_exists else -1

products_after = cur.execute("SELECT count(*) FROM products;").fetchone()[0] if "products" in tables_after else 0
sales_after = cur.execute("SELECT count(*) FROM sales;").fetchone()[0] if "sales" in tables_after else 0
photos_after = cur.execute("SELECT count(*) FROM product_photos;").fetchone()[0] if "product_photos" in tables_after else 0

schema_rows = cur.execute("SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name;").fetchall()
schema_text = '\\n'.join([f'{r[0]}|{r[1]}|{r[2]}' for r in schema_rows])
schema_sha = hashlib.sha256(schema_text.encode('utf-8')).hexdigest()

conn.close()

result = {
    "MIGRATION_APPLIED": True,
    "AVITO_POST_SALE_TASKS_EXISTS": avito_tasks_exists,
    "AVITO_POST_SALE_TASKS_ROWS": avito_tasks_rows,
    "LIVE_DB_SCHEMA_SHA_AFTER_MIGRATION": schema_sha,
    "LIVE_DB_QUICK_CHECK_AFTER_MIGRATION": quick_check,
    "PRODUCTS_BEFORE": products_before,
    "PRODUCTS_AFTER": products_after,
    "SALES_BEFORE": sales_before,
    "SALES_AFTER": sales_after,
    "PHOTOS_BEFORE": photos_before,
    "PHOTOS_AFTER": photos_after,
    "BUSINESS_COUNTS_UNCHANGED_AFTER_MIGRATION": (
        products_before == products_after and
        sales_before == sales_after and
        photos_before == photos_after
    )
}
print(json.dumps(result, indent=2))
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_migration_script,
    capture_output=True,
    text=True
)

if proc.returncode != 0:
    print("SSH error:", proc.stderr)
    exit(1)

print(proc.stdout)
