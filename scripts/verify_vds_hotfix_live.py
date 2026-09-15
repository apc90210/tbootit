import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

verify_script = """
import urllib.request, zipfile, io, hashlib

# Test endpoint directly on admin-shell container port 8010
url = 'http://127.0.0.1:8010/avito/extension/download'
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as resp:
    data = resp.read()
    status = resp.status
    headers = dict(resp.getheaders())

print('HTTP Status:', status)
print('Downloaded Size:', len(data))
print('SHA256:', hashlib.sha256(data).hexdigest())
print('Content-Disposition:', headers.get('content-disposition'))

zf = zipfile.ZipFile(io.BytesIO(data))
content_js = zf.read('content.js').decode('utf-8')
print('content.js has getExtensionVersion:', 'getExtensionVersion' in content_js)
print('content.js has fixed while brace:', 'waitForConfirmedInactiveState' in content_js and 'return { confirmed: true, type: inactive.indicator };' in content_js)
"""

# Run verify_script inside docker container technoreboot-prod-admin-shell
res = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "docker exec -i technoreboot-prod-admin-shell python"],
    input=verify_script,
    capture_output=True,
    text=True
)

print("STDOUT:\n", res.stdout)
if res.stderr:
    print("STDERR:\n", res.stderr)
