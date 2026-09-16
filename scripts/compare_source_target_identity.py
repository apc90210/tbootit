import subprocess
import json

def run_ssh(host, code):
    res = subprocess.run(
        ["ssh", f"root@{host}", "python3 -"],
        input=code,
        capture_output=True,
        text=True
    )
    if res.returncode != 0:
        raise RuntimeError(f"SSH {host} failed: {res.stderr}")
    return res.stdout.strip()

source_ip = "144.31.50.134"
target_ip = "144.31.15.88"

inspect_cmd = '''
import sqlite3, os, hashlib, json

def sha256_file(p):
    if not os.path.exists(p): return None
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while c := f.read(65536): h.update(c)
    return h.hexdigest()

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

ext_zip = '/srv/technoreboot/app/admin-shell/app/technoreboot-avito-extension.zip'
manual_pdf = '/srv/technoreboot/app/admin-shell/app/static/docs/TECHNOREBOOT_USER_MANUAL_RU.pdf'

res = {
    'head': os.popen('git -C /srv/technoreboot/app rev-parse HEAD').read().strip(),
    'counts': counts,
    'db_schema_sha': schema_sha,
    'quick_check': qc,
    'storage_count': len(storage_files),
    'ca_sha256': sha256_file('/srv/technoreboot/data/auth/ca/ca.crt'),
    'ext_zip_sha256': sha256_file(ext_zip),
    'manual_pdf_sha256': sha256_file(manual_pdf)
}
print(json.dumps(res))
'''

print("Fetching SOURCE data...")
src_data = json.loads(run_ssh(source_ip, inspect_cmd))
print("Fetching TARGET data...")
tgt_data = json.loads(run_ssh(target_ip, inspect_cmd))

comparisons = [
    ("CODE_HEAD", src_data['head'], tgt_data['head']),
    ("DB_SCHEMA_SHA", src_data['db_schema_sha'], tgt_data['db_schema_sha']),
    ("DB_QUICK_CHECK", src_data['quick_check'], tgt_data['quick_check']),
    ("PRODUCTS", src_data['counts']['products'], tgt_data['counts']['products']),
    ("SALES", src_data['counts']['sales'], tgt_data['counts']['sales']),
    ("REPAIRS", src_data['counts']['repair_orders'], tgt_data['counts']['repair_orders']),
    ("PHOTOS", src_data['counts']['product_photos'], tgt_data['counts']['product_photos']),
    ("EXTERNAL_LISTINGS", src_data['counts']['product_external_listings'], tgt_data['counts']['product_external_listings']),
    ("AVITO_POST_SALE_TASKS", src_data['counts']['avito_post_sale_tasks'], tgt_data['counts']['avito_post_sale_tasks']),
    ("STORAGE_FILE_COUNT", src_data['storage_count'], tgt_data['storage_count']),
    ("AUTH_CA_SHA256", src_data['ca_sha256'], tgt_data['ca_sha256']),
    ("EXTENSION_ZIP_SHA256", src_data['ext_zip_sha256'], tgt_data['ext_zip_sha256']),
    ("MANUAL_PDF_SHA256", src_data['manual_pdf_sha256'], tgt_data['manual_pdf_sha256']),
]

print("\n" + "="*80)
print(f"{'METRIC':<24} | {'SOURCE (' + source_ip + ')':<26} | {'TARGET (' + target_ip + ')':<26} | MATCH")
print("="*80)
all_match = True
for name, s_val, t_val in comparisons:
    m = (s_val == t_val)
    if not m: all_match = False
    s_disp = str(s_val)[:24] + ".." if len(str(s_val)) > 26 else str(s_val)
    t_disp = str(t_val)[:24] + ".." if len(str(t_val)) > 26 else str(t_val)
    print(f"{name:<24} | {s_disp:<26} | {t_disp:<26} | {'YES' if m else 'NO'}")
print("="*80)
print(f"OVERALL IDENTITY MATCH: {all_match}\n")
