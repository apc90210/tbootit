import subprocess
import sys
import json
from pathlib import Path

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

print("--- [1/2] Running deploy/production/update_code_only.sh origin/main on VDS ---")
proc = subprocess.run(
    [
        "ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST,
        "bash /srv/technoreboot/app/deploy/production/update_code_only.sh origin/main"
    ],
    capture_output=True,
    text=True
)

print("STDOUT:")
print(proc.stdout)
if proc.stderr:
    print("STDERR:")
    print(proc.stderr)

if proc.returncode != 0:
    print(f"Deployment failed with exit code {proc.returncode}!")
    sys.exit(proc.returncode)

print("--- [2/2] Inspecting post-deployment state on VDS ---")
inspect_script = """
import subprocess, json, sqlite3, hashlib

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

git_head = run_cmd("git -C /srv/technoreboot/app rev-parse HEAD")
git_branch = run_cmd("git -C /srv/technoreboot/app rev-parse --abbrev-ref HEAD")
git_status = run_cmd("git -C /srv/technoreboot/app status -s")

ps_out = run_cmd("docker ps --format '{{.ID}} {{.Names}} {{.Status}} {{.Image}}'")
images_out = run_cmd("docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}'")

# Read deployment_compatibility.json
compat_raw = run_cmd("cat /srv/technoreboot/app/deploy/production/deployment_compatibility.json 2>/dev/null || echo '{}'")
try:
    compat = json.loads(compat_raw)
except Exception:
    compat = {}

# DB checks
db_sha = run_cmd("sha256sum /srv/technoreboot/data/db/technoreboot.db | awk '{print $1}'")

conn = sqlite3.connect('/srv/technoreboot/data/db/technoreboot.db')
cur = conn.cursor()
quick_check = cur.execute("PRAGMA quick_check;").fetchone()[0]

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall()]
counts = {}
for tbl in ["products", "sales", "product_photos", "product_external_listings", "repair_orders", "repairs", "avito_post_sale_tasks"]:
    if tbl in tables:
        counts[tbl] = cur.execute(f"SELECT count(*) FROM {tbl};").fetchone()[0]
    else:
        counts[tbl] = "TABLE_ABSENT"

schema_rows = cur.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name;").fetchall()
schema_str = "\\n".join(r[0] for r in schema_rows)
schema_sha = hashlib.sha256(schema_str.encode('utf-8')).hexdigest()

conn.close()

storage_count = int(run_cmd("find /srv/technoreboot/data/storage -type f | wc -l") or 0)
auth_ca = run_cmd("sha256sum /srv/technoreboot/data/auth/ca/ca.crt 2>/dev/null | awk '{print $1}' || echo ABSENT")

# Check manual PDF on VDS
pdf_sha = run_cmd("sha256sum /srv/technoreboot/app/admin-shell/app/static/docs/TECHNOREBOOT_USER_MANUAL_RU.pdf 2>/dev/null | awk '{print $1}' || echo ABSENT")
pdf_size = run_cmd("wc -c < /srv/technoreboot/app/admin-shell/app/static/docs/TECHNOREBOOT_USER_MANUAL_RU.pdf 2>/dev/null || echo 0")

print(json.dumps({
    "git_head": git_head,
    "git_branch": git_branch,
    "git_status": git_status,
    "compat": compat,
    "containers": ps_out.splitlines(),
    "images": images_out.splitlines(),
    "db_sha": db_sha,
    "quick_check": quick_check,
    "counts": counts,
    "schema_sha": schema_sha,
    "storage_count": storage_count,
    "auth_ca": auth_ca,
    "pdf_sha": pdf_sha,
    "pdf_size": pdf_size
}, indent=2))
"""

proc2 = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=inspect_script,
    capture_output=True,
    text=True
)

if proc2.returncode != 0:
    print("Post-deployment inspection failed!")
    print("STDERR:", proc2.stderr)
    sys.exit(proc2.returncode)

data = json.loads(proc2.stdout)
print("=== POST-DEPLOYMENT VDS STATE ===")
print(json.dumps(data, indent=2))

out_file = Path(__file__).resolve().parent / "vds_post_deploy_10b.json"
out_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"Saved post-deployment inspection to {out_file}")
