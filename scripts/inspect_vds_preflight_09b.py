import os
import sys
import json
import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_code = """
import os, sys, sqlite3, hashlib, json, subprocess

res = {}

# 1. Repo HEAD
try:
    head = subprocess.check_output(['git', '-C', '/srv/technoreboot/app', 'rev-parse', 'HEAD'], text=True).strip()
    res['VDS_LIVE_HEAD'] = head
except Exception as e:
    res['VDS_LIVE_HEAD'] = f'ERROR: {e}'

# 2. Containers & Images
try:
    ps_raw = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}|{{.ID}}|{{.Image}}|{{.Status}}'], text=True).strip().splitlines()
    res['LIVE_CONTAINERS'] = {}
    for line in ps_raw:
        if '|' in line:
            parts = line.split('|')
            name = parts[0].strip()
            cid = parts[1].strip()
            img = parts[2].strip()
            status = parts[3].strip()
            res['LIVE_CONTAINERS'][name] = {'id': cid, 'image': img, 'status': status}
except Exception as e:
    res['LIVE_CONTAINERS_ERROR'] = str(e)

# 3. Live DB Fingerprint
db_path = '/srv/technoreboot/data/db/technoreboot.db'
res['LIVE_DB_PATH'] = db_path
if os.path.exists(db_path):
    res['LIVE_DB_SIZE_BEFORE'] = os.path.getsize(db_path)
    with open(db_path, 'rb') as f:
        res['LIVE_DB_SHA256_BEFORE'] = hashlib.sha256(f.read()).hexdigest()

    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    cur = conn.cursor()
    res['LIVE_DB_QUICK_CHECK_BEFORE'] = cur.execute('PRAGMA quick_check;').fetchone()[0]

    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    res['PRODUCTS_BEFORE'] = cur.execute('SELECT count(*) FROM products;').fetchone()[0] if 'products' in tables else 'TABLE_ABSENT'
    res['SALES_BEFORE'] = cur.execute('SELECT count(*) FROM sales;').fetchone()[0] if 'sales' in tables else 'TABLE_ABSENT'
    res['REPAIRS_BEFORE'] = cur.execute('SELECT count(*) FROM repairs;').fetchone()[0] if 'repairs' in tables else 'TABLE_ABSENT'
    res['PHOTOS_BEFORE'] = cur.execute('SELECT count(*) FROM product_photos;').fetchone()[0] if 'product_photos' in tables else 'TABLE_ABSENT'
    res['EXTERNAL_LISTINGS_BEFORE'] = cur.execute('SELECT count(*) FROM external_listings;').fetchone()[0] if 'external_listings' in tables else 'TABLE_ABSENT'
    res['AVITO_POST_SALE_TASKS_BEFORE'] = cur.execute('SELECT count(*) FROM avito_post_sale_tasks;').fetchone()[0] if 'avito_post_sale_tasks' in tables else 'TABLE_ABSENT'

    schema_rows = cur.execute("SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name;").fetchall()
    schema_text = '\\n'.join([f'{r[0]}|{r[1]}|{r[2]}' for r in schema_rows])
    res['LIVE_DB_SCHEMA_SHA_BEFORE'] = hashlib.sha256(schema_text.encode('utf-8')).hexdigest()
    conn.close()
else:
    res['LIVE_DB_ERROR'] = 'DB_FILE_NOT_FOUND'

# 4. Storage file count
storage_count = 0
storage_dir = '/srv/technoreboot/data/storage'
if os.path.exists(storage_dir):
    for root, dirs, files in os.walk(storage_dir):
        storage_count += len(files)
res['PROD_STORAGE_FILE_COUNT_BEFORE'] = storage_count

# 5. Auth CA SHA
ca_path = '/srv/technoreboot/data/auth/ca.crt'
ca_sha = 'ABSENT'
if os.path.exists(ca_path):
    with open(ca_path, 'rb') as f:
        ca_sha = hashlib.sha256(f.read()).hexdigest()
res['PROD_AUTH_CA_SHA256_BEFORE'] = ca_sha

print(json.dumps(res, indent=2))
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_code,
    capture_output=True,
    text=True
)

if proc.returncode != 0:
    print("SSH error:", proc.stderr)
    sys.exit(1)

print(proc.stdout)
