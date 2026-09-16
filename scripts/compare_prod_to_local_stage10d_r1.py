import os
import sys
import json
import sqlite3
import hashlib
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOCAL_DB = os.path.join(REPO_ROOT, "data", "db", "technoreboot.db")
LOCAL_STORAGE = os.path.join(REPO_ROOT, "data", "storage")
TARGET_IP = "144.31.15.88"

def run_ssh_code(host, code):
    res = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", f"root@{host}", "python3 -"],
        input=code,
        capture_output=True,
        text=True
    )
    if res.returncode != 0:
        raise RuntimeError(f"SSH {host} failed: {res.stderr}")
    return res.stdout.strip()

inspect_cmd = '''
import sqlite3, os, hashlib, json

db_path = '/srv/technoreboot/data/db/technoreboot.db'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cur = conn.cursor()
qc = cur.execute("PRAGMA quick_check;").fetchone()[0]
schema_rows = cur.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name;").fetchall()
schema_text = "\\n".join([r[0] for r in schema_rows])
schema_sha = hashlib.sha256(schema_text.encode('utf-8')).hexdigest()

counts = {}
for t in ['products', 'sales', 'repair_orders', 'product_photos', 'product_external_listings', 'avito_post_sale_tasks']:
    try:
        counts[t] = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    except Exception as e:
        counts[t] = str(e)
conn.close()

storage_files = []
for r, _, files in os.walk('/srv/technoreboot/data/storage'):
    for f in files: storage_files.append(os.path.join(r, f))

res = {
    'db_schema_sha': schema_sha,
    'quick_check': qc,
    'counts': counts,
    'storage_count': len(storage_files),
}
print(json.dumps(res))
'''

def main():
    print("=== Stage 10D-R1 Data Identity Check: PROD (144.31.15.88) vs LOCAL ===")

    # Remote inspect
    remote_data = json.loads(run_ssh_code(TARGET_IP, inspect_cmd))

    # Local inspect
    assert os.path.exists(LOCAL_DB), f"Local DB not found: {LOCAL_DB}"
    conn = sqlite3.connect(f"file:{LOCAL_DB}?mode=ro", uri=True)
    cur = conn.cursor()
    local_qc = cur.execute("PRAGMA quick_check;").fetchone()[0]
    schema_rows = cur.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name;").fetchall()
    schema_text = "\n".join([r[0] for r in schema_rows])
    local_schema_sha = hashlib.sha256(schema_text.encode('utf-8')).hexdigest()

    local_counts = {}
    for t in ['products', 'sales', 'repair_orders', 'product_photos', 'product_external_listings', 'avito_post_sale_tasks']:
        try:
            local_counts[t] = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception as e:
            local_counts[t] = str(e)
    conn.close()

    local_storage_files = []
    if os.path.exists(LOCAL_STORAGE):
        for r, _, files in os.walk(LOCAL_STORAGE):
            for f in files:
                local_storage_files.append(os.path.join(r, f))
    local_storage_count = len(local_storage_files)

    checks = [
        ("PROD_PRODUCTS == LOCAL_PRODUCTS", remote_data['counts']['products'], local_counts['products']),
        ("PROD_SALES == LOCAL_SALES", remote_data['counts']['sales'], local_counts['sales']),
        ("PROD_REPAIRS == LOCAL_REPAIRS", remote_data['counts']['repair_orders'], local_counts['repair_orders']),
        ("PROD_PRODUCT_PHOTOS == LOCAL_PRODUCT_PHOTOS", remote_data['counts']['product_photos'], local_counts['product_photos']),
        ("PROD_EXTERNAL_LISTINGS == LOCAL_EXTERNAL_LISTINGS", remote_data['counts']['product_external_listings'], local_counts['product_external_listings']),
        ("PROD_AVITO_POST_SALE_TASKS == LOCAL_AVITO_POST_SALE_TASKS", remote_data['counts']['avito_post_sale_tasks'], local_counts['avito_post_sale_tasks']),
        ("PROD_STORAGE_FILE_COUNT == LOCAL_STORAGE_FILE_COUNT", remote_data['storage_count'], local_storage_count),
        ("PROD_SCHEMA_SHA == LOCAL_SCHEMA_SHA", remote_data['db_schema_sha'], local_schema_sha),
        ("LOCAL_DB_QUICK_CHECK == ok", "ok", local_qc),
    ]

    print("\n" + "=" * 80)
    print(f"{'METRIC':<35} | {'PROD (144.31.15.88)':<22} | {'LOCAL':<22} | MATCH")
    print("=" * 80)
    all_match = True
    for name, p_val, l_val in checks:
        m = (p_val == l_val)
        if not m:
            all_match = False
        p_disp = str(p_val)[:20] + ".." if len(str(p_val)) > 22 else str(p_val)
        l_disp = str(l_val)[:20] + ".." if len(str(l_val)) > 22 else str(l_val)
        print(f"{name:<35} | {p_disp:<22} | {l_disp:<22} | {'YES' if m else 'NO'}")
    print("=" * 80)
    print(f"DATA IDENTITY CHECK RESULT: {'PASS' if all_match else 'FAIL'}")
    print("=" * 80)

    if not all_match:
        sys.exit(1)

if __name__ == "__main__":
    main()
