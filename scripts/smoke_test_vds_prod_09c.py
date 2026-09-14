import os
import subprocess
import httpx
import hashlib
import json
from pathlib import Path

# Clean up proxy environment variables that can interfere on Windows
for env_var in ["NO_PROXY", "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    os.environ.pop(env_var, None)

VDS_IP = "144.31.50.134"
BASE_URL = f"https://{VDS_IP}"
LOCAL_ZIP_PATH = Path("dist/technoreboot-avito-extension-0.2.62.zip")
LOCAL_ZIP_SHA256 = hashlib.sha256(LOCAL_ZIP_PATH.read_bytes()).hexdigest()

AUTH_DIR = Path("data/auth")
OWNER_CERT = AUTH_DIR / "certificates" / "owner.crt"
OWNER_KEY = AUTH_DIR / "certificates" / "owner.key"
CA_CERT = AUTH_DIR / "ca" / "ca.crt"

print(f"LOCAL_ZIP_SHA256: {LOCAL_ZIP_SHA256}")
print(f"LOCAL_ZIP_SIZE: {LOCAL_ZIP_PATH.stat().st_size}")

# Test 1: Without cert -> 403 Forbidden
try:
    with httpx.Client(verify=False, timeout=10.0) as client:
        r_no_cert = client.get(f"{BASE_URL}/")
        print(f"No cert GET / status: {r_no_cert.status_code}")
except Exception as e:
    print(f"No cert GET / error: {e}")

# Test 2: With Owner mTLS
client_kwargs = {
    "verify": False,
    "timeout": 15.0,
    "follow_redirects": True,
}
if OWNER_CERT.exists() and OWNER_KEY.exists():
    client_kwargs["cert"] = (str(OWNER_CERT), str(OWNER_KEY))

with httpx.Client(**client_kwargs) as client:
    # 1. Root /
    r_root = client.get(f"{BASE_URL}/")
    print(f"GET / : status={r_root.status_code}, len={len(r_root.text)}")
    
    # 2. /products or /inventory/products
    r_prod = client.get(f"{BASE_URL}/products")
    print(f"GET /products : status={r_prod.status_code}, len={len(r_prod.text)}")

    # 3. /sales
    r_sales = client.get(f"{BASE_URL}/sales")
    print(f"GET /sales : status={r_sales.status_code}, len={len(r_sales.text)}")

    # 4. /avito/extension
    r_ext = client.get(f"{BASE_URL}/avito/extension")
    print(f"GET /avito/extension : status={r_ext.status_code}, len={len(r_ext.text)}")
    v0262_in_ext = "0.2.62" in r_ext.text
    copy_in_ext = "Копировать токен" in r_ext.text or "copy" in r_ext.text.lower()
    print(f"  v0.2.62 in text: {v0262_in_ext}")
    print(f"  Copy token button in text: {copy_in_ext}")

    # 5. /avito/extension/download
    r_dl = client.get(f"{BASE_URL}/avito/extension/download")
    dl_sha = hashlib.sha256(r_dl.content).hexdigest()
    print(f"GET /avito/extension/download : status={r_dl.status_code}, bytes={len(r_dl.content)}")
    print(f"  Downloaded ZIP SHA256: {dl_sha}")
    print(f"  Matches LOCAL ZIP: {dl_sha == LOCAL_ZIP_SHA256}")

    # 6. /avito/post-sale
    r_ps = client.get(f"{BASE_URL}/avito/post-sale")
    print(f"GET /avito/post-sale : status={r_ps.status_code}, len={len(r_ps.text)}")

    # 7. /repairs
    r_rep = client.get(f"{BASE_URL}/repairs")
    print(f"GET /repairs : status={r_rep.status_code}, len={len(r_rep.text)}")

# Test 3: Manual Avito flow presence in sales_detail.html inside live container
ssh_res = subprocess.run(
    [
        "ssh", "-i", r"C:\Users\Apc\.ssh\id_ed25519", "-o", "BatchMode=yes",
        "root@144.31.50.134",
        "docker exec technoreboot-prod-inventory-sales python3 -c \""
        "import json; "
        "content = open('/app/app/templates/sales_detail.html', encoding='utf-8').read(); "
        "b1 = 'Снять с Avito вручную' in content; "
        "b2 = 'Не снимать' in content; "
        "b3 = 'Я снял объявление' in content; "
        "print(json.dumps({'manual_open': b1, 'dismiss': b2, 'confirm': b3}))\""
    ],
    capture_output=True,
    text=True
)

manual_flow_ok = False
if ssh_res.returncode == 0:
    try:
        mf = json.loads(ssh_res.stdout.strip())
        manual_flow_ok = mf.get("manual_open") and mf.get("dismiss") and mf.get("confirm")
        print(f"Manual flow buttons in container template: {mf}")
    except Exception as e:
        print(f"Failed to parse manual flow check: {e}")
else:
    print(f"SSH manual flow check failed: {ssh_res.stderr}")

results = {
    "ROOT_OK": r_root.status_code == 200,
    "PRODUCTS_OK": r_prod.status_code == 200,
    "SALES_OK": r_sales.status_code == 200,
    "AVITO_EXTENSION_PAGE_OK": r_ext.status_code == 200 and v0262_in_ext,
    "AVITO_EXTENSION_DOWNLOAD_OK": r_dl.status_code == 200 and (dl_sha == LOCAL_ZIP_SHA256),
    "AVITO_POST_SALE_PAGE_OK": r_ps.status_code == 200,
    "REPAIRS_OK": r_rep.status_code == 200,
    "MANUAL_AVITO_FLOW_PRESENT": manual_flow_ok,
    "EXTENSION_ZIP_HASH_MATCH": (dl_sha == LOCAL_ZIP_SHA256),
    "EXTENSION_VERSION": "0.2.62" if v0262_in_ext else "UNKNOWN",
    "DOWNLOADED_ZIP_SHA256": dl_sha,
    "LOCAL_ZIP_SHA256": LOCAL_ZIP_SHA256,
}
print("\nFINAL SMOKE TEST SUMMARY:")
print(json.dumps(results, indent=2))
