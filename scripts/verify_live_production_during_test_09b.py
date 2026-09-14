import subprocess
import json
import httpx

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

BEFORE_IDS = {
    "technoreboot-prod-admin-shell": "826e3c5c02dc",
    "technoreboot-prod-core": "775d20febab0",
    "technoreboot-prod-avito": "1b101f768ac9",
    "technoreboot-prod-repairs": "7b264c248772",
    "technoreboot-prod-inventory-sales": "9a8704a70980",
    "technoreboot-prod-gateway": "58c543b502b6"
}

BEFORE_IMAGES = {
    "technoreboot-prod-admin-shell": "production-admin-shell",
    "technoreboot-prod-core": "e7ddb53d6267",
    "technoreboot-prod-avito": "ecfb501800e6",
    "technoreboot-prod-repairs": "44d608f40048",
    "technoreboot-prod-inventory-sales": "f08174cdf93d",
    "technoreboot-prod-gateway": "nginx:alpine"
}

# 1. Query docker ps on VDS
ps_cmd = "docker ps --format '{{.Names}}|{{.ID}}|{{.Image}}|{{.Status}}'"
res_ps = subprocess.check_output(["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, ps_cmd], text=True)

current_live = {}
for line in res_ps.strip().splitlines():
    if '|' in line:
        parts = line.split('|')
        name = parts[0].strip()
        cid = parts[1].strip()
        img = parts[2].strip()
        status = parts[3].strip()
        if name in BEFORE_IDS:
            current_live[name] = {"id": cid, "image": img, "status": status}

ids_unchanged = True
images_unchanged = True
healthy = True

for name, expected_id in BEFORE_IDS.items():
    cur = current_live.get(name)
    if not cur:
        print(f"MISSING CONTAINER: {name}")
        ids_unchanged = False
        healthy = False
        continue
    if not cur["id"].startswith(expected_id):
        print(f"ID CHANGED for {name}: expected {expected_id}, got {cur['id']}")
        ids_unchanged = False
    if not "healthy" in cur["status"].lower() and not "up" in cur["status"].lower():
        print(f"UNHEALTHY {name}: {cur['status']}")
        healthy = False

for name, expected_img in BEFORE_IMAGES.items():
    cur = current_live.get(name)
    if cur and not cur["image"].startswith(expected_img):
        print(f"IMAGE CHANGED for {name}: expected {expected_img}, got {cur['image']}")
        images_unchanged = False

# 2. Public HTTPS probe
client = httpx.Client(
    cert=("data/auth/certificates/owner.crt", "data/auth/certificates/owner.key"),
    verify=False,
    timeout=10.0,
    trust_env=False
)
pub_res = client.get("https://144.31.50.134/")
pub_ok = (pub_res.status_code == 200)

print(json.dumps({
    "LIVE_CONTAINER_IDS_UNCHANGED": ids_unchanged,
    "LIVE_IMAGE_IDS_UNCHANGED": images_unchanged,
    "LIVE_6_CONTAINERS_HEALTHY": healthy,
    "LIVE_PUBLIC_SITE_STATUS": pub_res.status_code,
    "LIVE_PUBLIC_SITE_HEALTHY": pub_ok,
    "CURRENT_LIVE_CONTAINERS": current_live
}, indent=2))
