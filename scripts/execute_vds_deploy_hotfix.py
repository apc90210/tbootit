import subprocess
import sys
import json
import zipfile
import io

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

print("=== [1/3] Running deploy/production/update_code_only.sh origin/main on VDS ===")
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

print("\n=== [2/3] Inspecting VDS status and extension ZIP ===")
verify_script = """
import subprocess, json, sqlite3, zipfile

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

git_head = run_cmd("git -C /srv/technoreboot/app rev-parse HEAD")
git_branch = run_cmd("git -C /srv/technoreboot/app rev-parse --abbrev-ref HEAD")
ps_out = run_cmd("docker ps --format '{{.Names}} {{.Status}}'")

# Check extension ZIP in admin-shell
zip_path = "/srv/technoreboot/app/admin-shell/app/technoreboot-avito-extension.zip"
with zipfile.ZipFile(zip_path, 'r') as zf:
    namelist = zf.namelist()
    content_js = zf.read("content.js").decode("utf-8")
    has_fixed_brace = "waitForConfirmedInactiveState" in content_js and "return { confirmed: true, type: inactive.indicator };\\n        }\\n        await new Promise(r => setTimeout(r, 500));\\n    }\\n    return null;" in content_js

# Check DB counts
conn = sqlite3.connect('/srv/technoreboot/data/db/technoreboot.db')
cur = conn.cursor()
counts = {}
for tbl in ["products", "sales", "product_photos", "product_external_listings", "repair_orders", "repairs", "avito_post_sale_tasks"]:
    try:
        counts[tbl] = cur.execute(f"SELECT count(*) FROM {tbl};").fetchone()[0]
    except Exception:
        counts[tbl] = "ERROR"
conn.close()

# Test download endpoint locally on VDS host
curl_res = run_cmd("curl -k -s -w '%{http_code}' -o /tmp/vds_downloaded_ext.zip https://127.0.0.1/avito/extension/download")

downloaded_ok = False
if curl_res == "200":
    try:
        with zipfile.ZipFile("/tmp/vds_downloaded_ext.zip", 'r') as dzf:
            d_content = dzf.read("content.js").decode("utf-8")
            if "getExtensionVersion" in d_content:
                downloaded_ok = True
    except Exception:
        pass

print(json.dumps({
    "git_head": git_head,
    "git_branch": git_branch,
    "ps_out": ps_out.splitlines(),
    "zip_namelist_len": len(namelist),
    "has_fixed_brace": has_fixed_brace,
    "curl_download_status": curl_res,
    "downloaded_content_verified": downloaded_ok,
    "counts": counts
}, indent=2))
"""

proc2 = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=verify_script,
    capture_output=True,
    text=True
)

if proc2.returncode != 0:
    print("Verification failed on VDS!")
    print("STDERR:", proc2.stderr)
    sys.exit(proc2.returncode)

print("VDS Verification Result:")
print(proc2.stdout)

print("\n=== [3/3] Deployment & Verification Completed Successfully ===")
