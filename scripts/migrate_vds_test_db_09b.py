import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import sqlite3, hashlib, json

LIVE_DB_PATH = '/srv/technoreboot/data/db/technoreboot.db'
TEST_DB_PATH = '/srv/technoreboot-sync-test/e022180/test-data/db/technoreboot.db'

with open(LIVE_DB_PATH, 'rb') as f:
    live_sha_before = hashlib.sha256(f.read()).hexdigest()

test_conn = sqlite3.connect(TEST_DB_PATH)
cur = test_conn.cursor()

# Check before
tables_before = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]

sql = '''
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
cur.executescript(sql)
test_conn.commit()

tables_after = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
test_conn.close()

with open(LIVE_DB_PATH, 'rb') as f:
    live_sha_after = hashlib.sha256(f.read()).hexdigest()

with open(TEST_DB_PATH, 'rb') as f:
    test_sha_after = hashlib.sha256(f.read()).hexdigest()

res = {
    'TABLES_BEFORE': tables_before,
    'TABLES_AFTER': tables_after,
    'AVITO_TASKS_CREATED': ('avito_post_sale_tasks' in tables_after and 'avito_post_sale_tasks' not in tables_before),
    'LIVE_DB_SHA_BEFORE': live_sha_before,
    'LIVE_DB_SHA_AFTER': live_sha_after,
    'LIVE_DB_STILL_INTACT': (live_sha_before == live_sha_after),
    'TEST_DB_SHA_AFTER_MIGRATION': test_sha_after
}
print(json.dumps(res, indent=2))
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

print(proc.stdout)
if proc.stderr:
    print("ERR:", proc.stderr)
