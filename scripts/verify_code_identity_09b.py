import os
import sys
import hashlib
import subprocess
import json

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

files = [
    "admin-shell/app/templates/avito_extension.html",
    "admin-shell/app/technoreboot-avito-extension.zip",
    "chrome-extension/technoreboot-avito/manifest.json",
    "chrome-extension/technoreboot-avito/popup.html",
    "chrome-extension/technoreboot-avito/popup.js",
    "chrome-extension/technoreboot-avito/service_worker.js"
]

local_hashes = {}
for rel in files:
    with open(rel, "rb") as f:
        local_hashes[rel] = hashlib.sha256(f.read()).hexdigest()

remote_script = f"""
import os, hashlib, json
files = {json.dumps(files)}
h = {{}}
for rel in files:
    p = os.path.join('/srv/technoreboot-sync-test/e022180/app', rel)
    with open(p, 'rb') as f:
        h[rel] = hashlib.sha256(f.read()).hexdigest()
print(json.dumps(h))
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

remote_hashes = json.loads(proc.stdout)

all_match = True
for rel in files:
    lh = local_hashes[rel]
    rh = remote_hashes[rel]
    match = (lh == rh)
    if not match:
        all_match = False
    print(f"{rel}:")
    print(f"  LOCAL:  {lh}")
    print(f"  REMOTE: {rh}")
    print(f"  MATCH:  {match}")

zip_match = (local_hashes["admin-shell/app/technoreboot-avito-extension.zip"] == remote_hashes["admin-shell/app/technoreboot-avito-extension.zip"])

print("--------------------------------------------------")
print("CODE_IDENTITY_MATCH:", all_match)
print("EXTENSION_ZIP_HASH_MATCH:", zip_match)
