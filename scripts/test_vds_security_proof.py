import subprocess

ssh_key = r"C:\Users\Apc\.ssh\id_ed25519"
host = "root@144.31.50.134"

remote_script = """
import urllib.request, ssl, json, sqlite3

ca_file = '/srv/technoreboot/data/auth/ca/ca.crt'
owner_cert = '/srv/technoreboot/data/auth/certificates/owner.crt'
owner_key = '/srv/technoreboot/data/auth/certificates/owner.key'
user_cert = '/srv/technoreboot/data/auth/certificates/75c53f564285.crt'
user_key = '/srv/technoreboot/data/auth/certificates/75c53f564285.key'

# Create SSL contexts
def get_context(cert, key):
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_file)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.load_cert_chain(certfile=cert, keyfile=key)
    return ctx

user_ctx = get_context(user_cert, user_key)
owner_ctx = get_context(owner_cert, owner_key)

base_url = 'https://127.0.0.1:443'

def do_req(ctx, path, method='GET', data=None):
    url = base_url + path
    headers = {'Host': '144.31.50.134'}
    body = None
    if data is not None:
        body = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            return resp.status, resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return -1, str(e)

print('=== 1. Non-Destructive Security Proof for USER ===')
# USER /admin-api/dev-reset
st, body = do_req(user_ctx, '/admin-api/dev-reset', method='POST', data={})
print(f'USER POST /admin-api/dev-reset: Status={st}')
assert st == 403, f'Expected 403, got {st}'

# USER /admin-api/seed
st, body = do_req(user_ctx, '/admin-api/seed', method='POST', data={'count': 5})
print(f'USER POST /admin-api/seed: Status={st}')
assert st == 403, f'Expected 403, got {st}'

# USER /certificates
st, body = do_req(user_ctx, '/certificates', method='GET')
print(f'USER GET /certificates: Status={st}')
assert st == 403, f'Expected 403, got {st}'

# USER /backups
st, body = do_req(user_ctx, '/backups', method='GET')
print(f'USER GET /backups: Status={st}')
assert st == 403, f'Expected 403, got {st}'

# USER /admin-api/avito/profiles/{key}
st, body = do_req(user_ctx, '/admin-api/avito/profiles/audit_test_probe_key', method='DELETE')
print(f'USER DELETE /admin-api/avito/profiles/audit_test_probe_key: Status={st}')
assert st == 403, f'Expected 403, got {st}'

print('=== 2. Non-Destructive Security Proof for OWNER on Production ===')
# OWNER /admin-api/dev-reset on production (must be 403 due to production guard)
st, body = do_req(owner_ctx, '/admin-api/dev-reset', method='POST', data={})
print(f'OWNER POST /admin-api/dev-reset (production guard): Status={st}')
assert st == 403, f'Expected 403, got {st}'

print('=== 3. Verification of Business Data Invariant ===')
conn = sqlite3.connect('/srv/technoreboot/data/db/technoreboot.db')
c = conn.cursor()
p = c.execute('SELECT COUNT(*) FROM products').fetchone()[0]
s = c.execute('SELECT COUNT(*) FROM sales').fetchone()[0]
r = c.execute('SELECT COUNT(*) FROM repair_orders').fetchone()[0]
ph = c.execute('SELECT COUNT(*) FROM product_photos').fetchone()[0]
l = c.execute('SELECT COUNT(*) FROM product_external_listings').fetchone()[0]
print(f'POST-TEST COUNTS: PRODUCTS={p} SALES={s} REPAIRS={r} PHOTOS={ph} LISTINGS={l}')
assert p == 149 and s == 0 and r == 0 and ph == 149 and l == 149, 'Data changed!'

print('ALL VDS SECURITY AND DATA INVARIANTS VERIFIED SUCCESSFULLY!')
"""

cmd = ["ssh", "-i", ssh_key, host, f"python3 -c \"{remote_script}\""]
p = subprocess.run(cmd, capture_output=True, text=True)
print(p.stdout)
if p.stderr:
    print("STDERR:", p.stderr)
