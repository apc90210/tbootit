import subprocess

script = """
import os, sys, sqlite3, shutil
from pathlib import Path

# 1. Reset Database
db_path = Path('/srv/technoreboot/data/db/technoreboot.db')
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

cur.execute("PRAGMA foreign_keys = OFF;")

business_tables = [
    "product_avito_attribute_values",
    "product_events",
    "product_photos",
    "product_external_listings",
    "stock_movements",
    "sale_items",
    "repair_status_history",
    "sales",
    "repair_orders",
    "product_cards",
    "products",
    "customers",
]

for t in business_tables:
    cur.execute(f'DELETE FROM "{t}";')

cur.execute("DELETE FROM audit_log WHERE entity_type != 'system';")

try:
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('products', 'sales', 'sale_items', 'repair_orders', 'repair_status_history', 'product_photos', 'product_external_listings', 'product_cards', 'product_events', 'stock_movements', 'customers', 'product_avito_attribute_values');")
except Exception as e:
    print('sqlite_sequence note:', e)

conn.commit()
cur.execute("PRAGMA foreign_keys = ON;")
cur.execute("VACUUM;")

print("=== DATABASE POST-RESET TABLE COUNTS ===")
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
counts = {}
for t in tables:
    cnt = cur.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
    counts[t] = cnt
    print(f"{t}: {cnt}")

conn.close()

# 2. Reset Live Media Storage
storage_root = Path('/srv/technoreboot/data/storage')
# Remove product_photos
photos_dir = storage_root / 'product_photos'
if photos_dir.is_dir():
    shutil.rmtree(photos_dir)
photos_dir.mkdir(parents=True, exist_ok=True)

# Remove any archive directories
for item in storage_root.iterdir():
    if item.is_dir() and item.name != 'product_photos':
        shutil.rmtree(item)
    elif item.is_file():
        item.unlink()

storage_files = [p for p in storage_root.rglob('*') if p.is_file()]
print(f"=== STORAGE POST-RESET FILES: {len(storage_files)} ===")

# 3. Reset Avito Business State
avito_root = Path('/srv/technoreboot/data/avito-module')
runs_dir = avito_root / 'runs'
if runs_dir.is_dir():
    shutil.rmtree(runs_dir)
runs_dir.mkdir(parents=True, exist_ok=True)

avito_files = [p for p in avito_root.rglob('*') if p.is_file()]
print(f"=== AVITO POST-RESET FILES: {len(avito_files)} ===")

# 4. Verify Auth/CA Unchanged
ca_path = Path('/srv/technoreboot/data/auth/ca/ca.crt')
import hashlib
ca_hash = hashlib.sha256(ca_path.read_bytes()).hexdigest()
print(f"=== CA SHA256: {ca_hash} ===")
"""

res = subprocess.run(
    ["ssh", "-i", r"C:\Users\Apc\.ssh\id_ed25519", "root@144.31.50.134", "python3"],
    input=script,
    text=True,
    capture_output=True,
)
print(res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)
