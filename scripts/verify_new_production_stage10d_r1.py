import subprocess
import json
import os

target_ip = "144.31.15.88"

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
import sqlite3, os, hashlib, json, subprocess

def sha256_file(p):
    if not os.path.exists(p): return None
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while c := f.read(65536): h.update(c)
    return h.hexdigest()

# OS
os_release = ""
if os.path.exists("/etc/os-release"):
    with open("/etc/os-release") as f:
        for line in f:
            if line.startswith("PRETTY_NAME="):
                os_release = line.split("=", 1)[1].strip().strip('"')

# GIT HEAD
git_head = subprocess.check_output(["git", "-C", "/srv/technoreboot/app", "rev-parse", "HEAD"], text=True).strip()

# Docker 6 services
ps_out = subprocess.check_output(["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"], text=True).strip()
services_status = {}
for line in ps_out.splitlines():
    if "\t" in line:
        name, status = line.split("\t", 1)
        services_status[name] = status

required_services = [
    "technoreboot-prod-core",
    "technoreboot-prod-inventory-sales",
    "technoreboot-prod-repairs",
    "technoreboot-prod-avito",
    "technoreboot-prod-admin-shell",
    "technoreboot-prod-gateway"
]
all_healthy = all(
    name in services_status and "(healthy)" in services_status[name]
    for name in required_services
)

# DB Check
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

# Extension version from manifest inside zip
ext_zip = '/srv/technoreboot/app/admin-shell/app/technoreboot-avito-extension.zip'
ext_ver = "unknown"
if os.path.exists(ext_zip):
    import zipfile
    with zipfile.ZipFile(ext_zip) as z:
        if "manifest.json" in z.namelist():
            manifest = json.loads(z.read("manifest.json").decode("utf-8"))
            ext_ver = manifest.get("version", "unknown")

manual_pdf = '/srv/technoreboot/app/admin-shell/app/static/docs/TECHNOREBOOT_USER_MANUAL_RU.pdf'

res = {
    'ssh_ok': True,
    'os': os_release,
    'git_head': git_head,
    'services_healthy': all_healthy,
    'services_status': services_status,
    'db_quick_check': qc,
    'db_schema_sha': schema_sha,
    'counts': counts,
    'storage_count': len(storage_files),
    'ext_version': ext_ver,
    'manual_pdf_sha256': sha256_file(manual_pdf)
}
print(json.dumps(res))
'''

print("Connecting to NEW production VDS (144.31.15.88)...")
raw = run_ssh_code(target_ip, inspect_cmd)
data = json.loads(raw)

print("=" * 60)
print("NEW PRODUCTION VDS STATUS (144.31.15.88):")
print(f"TARGET_SSH_OK:                {data['ssh_ok']}")
print(f"TARGET_OS:                    {data['os']}")
print(f"TARGET_GIT_HEAD:              {data['git_head']}")
print(f"TARGET_6_SERVICES_HEALTHY:    {data['services_healthy']}")
for s, st in data['services_status'].items():
    print(f"  - {s}: {st}")
print(f"TARGET_DB_QUICK_CHECK:        {data['db_quick_check']}")
print(f"TARGET_SCHEMA_SHA:            {data['db_schema_sha']}")
print(f"TARGET_PRODUCTS:              {data['counts']['products']}")
print(f"TARGET_SALES:                 {data['counts']['sales']}")
print(f"TARGET_REPAIRS:               {data['counts']['repair_orders']}")
print(f"TARGET_PRODUCT_PHOTOS:        {data['counts']['product_photos']}")
print(f"TARGET_EXTERNAL_LISTINGS:     {data['counts']['product_external_listings']}")
print(f"TARGET_AVITO_POST_SALE_TASKS: {data['counts']['avito_post_sale_tasks']}")
print(f"TARGET_STORAGE_FILE_COUNT:    {data['storage_count']}")
print(f"TARGET_EXTENSION_VERSION:     {data['ext_version']}")
print(f"TARGET_MANUAL_PDF_SHA256:     {data['manual_pdf_sha256']}")
print("=" * 60)
