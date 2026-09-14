import os
import sys
import json
import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import os, sys, sqlite3, hashlib, shutil, json

res = {}

LIVE_DB_PATH = '/srv/technoreboot/data/db/technoreboot.db'
TEST_ROOT = '/srv/technoreboot-sync-test/e022180'
TEST_DATA = f'{TEST_ROOT}/test-data'
TEST_DB_DIR = f'{TEST_DATA}/db'
TEST_DB_PATH = f'{TEST_DB_DIR}/technoreboot.db'

# 1. Measure live DB sha immediately before backup
with open(LIVE_DB_PATH, 'rb') as f:
    live_sha_before = hashlib.sha256(f.read()).hexdigest()
res['TEST_DB_SOURCE_SHA_REFERENCE'] = live_sha_before

# 2. Ensure test directories exist
for sub in ['db', 'auth', 'storage', 'backups', 'avito-module']:
    os.makedirs(f'{TEST_DATA}/{sub}', exist_ok=True)

# 3. Perform SQLite online backup from read-only connection
src_conn = sqlite3.connect(f'file:{LIVE_DB_PATH}?mode=ro', uri=True)
dst_conn = sqlite3.connect(TEST_DB_PATH)
src_conn.backup(dst_conn)
src_conn.close()
dst_conn.close()

# 4. Measure initial test DB sha
with open(TEST_DB_PATH, 'rb') as f:
    test_sha_initial = hashlib.sha256(f.read()).hexdigest()
res['TEST_DB_SHA256_INITIAL'] = test_sha_initial

# 5. Verify live DB sha remained unchanged
with open(LIVE_DB_PATH, 'rb') as f:
    live_sha_after = hashlib.sha256(f.read()).hexdigest()
res['LIVE_DB_SHA_STILL_INTACT'] = (live_sha_before == live_sha_after)

# 6. Copy auth data to disposable test-data/auth
if os.path.exists('/srv/technoreboot/data/auth'):
    for item in os.listdir('/srv/technoreboot/data/auth'):
        s = os.path.join('/srv/technoreboot/data/auth', item)
        d = os.path.join(f'{TEST_DATA}/auth', item)
        if os.path.isdir(s):
            if not os.path.exists(d): shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
res['AUTH_COPIED'] = True

# 7. Copy storage files to test-data/storage
if os.path.exists('/srv/technoreboot/data/storage'):
    for item in os.listdir('/srv/technoreboot/data/storage'):
        s = os.path.join('/srv/technoreboot/data/storage', item)
        d = os.path.join(f'{TEST_DATA}/storage', item)
        if os.path.isdir(s):
            if not os.path.exists(d): shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
res['STORAGE_COPIED'] = True

print(json.dumps(res, indent=2))
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

if proc.returncode != 0:
    print("SSH error:", proc.stderr)
    sys.exit(1)

print(proc.stdout)
