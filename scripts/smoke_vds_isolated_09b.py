import subprocess
import json

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import urllib.request
import ssl
import hashlib
import json
import http.client

CERT_FILE = '/srv/technoreboot-sync-test/e022180/test-data/auth/certificates/owner.crt'
KEY_FILE = '/srv/technoreboot-sync-test/e022180/test-data/auth/certificates/owner.key'
BASE_URL = 'https://127.0.0.1:18443'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

results = {}

def get_url(path):
    req = urllib.request.Request(f'{BASE_URL}{path}', headers={'Host': '144.31.50.134'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            content = resp.read()
            return {
                'status': resp.status,
                'headers': dict(resp.headers),
                'body': content.decode('utf-8', errors='replace'),
                'raw_bytes': content
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return {
            'status': e.code,
            'headers': dict(e.headers),
            'body': body,
            'raw_bytes': b''
        }
    except Exception as e:
        return {
            'error': str(e)
        }

# 1. Root /
r_root = get_url('/')
results['ROOT_STATUS'] = r_root.get('status')
results['ROOT_OK'] = (r_root.get('status') == 200)

# 2. Extension UI /avito/extension
r_ext = get_url('/avito/extension')
results['AVITO_EXTENSION_STATUS'] = r_ext.get('status')
body_ext = r_ext.get('body', '')
results['AVITO_EXTENSION_HAS_COPY_BTN'] = ('copyCodeBtn' in body_ext)
results['AVITO_EXTENSION_HAS_COPY_FN'] = ('copyPairCode' in body_ext)
results['AVITO_EXTENSION_HAS_V0262'] = ('v0.2.62' in body_ext)
results['AVITO_EXTENSION_PAGE_OK'] = (r_ext.get('status') == 200 and 'copyCodeBtn' in body_ext and 'v0.2.62' in body_ext)

# 3. Extension download /avito/extension/download
r_dl = get_url('/avito/extension/download')
results['DOWNLOAD_STATUS'] = r_dl.get('status')
cd = r_dl.get('headers', {}).get('Content-Disposition', '')
results['DOWNLOAD_CONTENT_DISPOSITION'] = cd
raw = r_dl.get('raw_bytes', b'')
results['DOWNLOAD_SIZE'] = len(raw)
dl_hash = hashlib.sha256(raw).hexdigest()
results['DOWNLOAD_SHA256'] = dl_hash
results['DOWNLOAD_HASH_MATCH_V0262'] = (dl_hash == 'c27a95bb35576f1b839e6ae4912534d6dc96231a567e120a3f14db461c0b8f84')
results['AVITO_EXTENSION_DOWNLOAD_OK'] = (r_dl.get('status') == 200 and results['DOWNLOAD_HASH_MATCH_V0262'])

# 4. Sales /sales/1
r_sales = get_url('/sales/1')
results['SALES_PAGE_STATUS'] = r_sales.get('status')
body_sales = r_sales.get('body', '')
results['SALES_PAGE_OK'] = (r_sales.get('status') == 200)

# 5. Post sale /avito/post-sale
r_ps = get_url('/avito/post-sale')
results['POST_SALE_PAGE_STATUS'] = r_ps.get('status')
body_ps = r_ps.get('body', '')
results['POST_SALE_PAGE_OK'] = (r_ps.get('status') == 200)

print(json.dumps(results, indent=2))
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

print(proc.stdout)
if proc.stderr:
    print("ERR:", proc.stderr)
