import subprocess
import sys
import json

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
import subprocess, json, sqlite3

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

git_head = run_cmd("git -C /srv/technoreboot/app rev-parse HEAD")
git_status = run_cmd("git -C /srv/technoreboot/app status -s")

ps_out = run_cmd("docker ps --format '{{.ID}} {{.Names}} {{.Status}} {{.Image}}'")
images_out = run_cmd("docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}'")

conn = sqlite3.connect('/srv/technoreboot/data/db/technoreboot.db')
cur = conn.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
counts = {}
for tbl in ["products", "sales", "product_photos", "product_external_listings", "repair_orders", "repairs", "avito_post_sale_tasks"]:
    if tbl in tables:
        counts[tbl] = cur.execute(f"SELECT count(*) FROM {tbl};").fetchone()[0]
    else:
        counts[tbl] = "TABLE_ABSENT"
conn.close()

storage_count = run_cmd("find /srv/technoreboot/data/storage -type f | wc -l")
auth_ca = run_cmd("sha256sum /srv/technoreboot/data/auth/ca.crt 2>/dev/null || echo ABSENT")

print(json.dumps({
    "git_head": git_head,
    "git_status": git_status,
    "containers": ps_out.splitlines(),
    "counts": counts,
    "storage_count": storage_count,
    "auth_ca": auth_ca
}, indent=2))
"""

proc2 = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=inspect_script,
    capture_output=True,
    text=True
)

print(proc2.stdout)
