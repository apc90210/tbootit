import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

script = """
import subprocess

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

print('=== NGINX ACCESS LOG (TAIL 30) ===')
print(run_cmd('docker exec technoreboot-prod-gateway tail -n 30 /var/log/nginx/access.log 2>/dev/null || docker logs --tail 30 technoreboot-prod-gateway'))

print('=== NGINX ERROR LOG (TAIL 30) ===')
print(run_cmd('docker exec technoreboot-prod-gateway tail -n 30 /var/log/nginx/error.log 2>/dev/null || true'))

print('=== CONNTRACK OR ACTIVE CONNECTIONS ===')
print(run_cmd('ss -tuna | head -n 30'))

print('=== DOCKER LOGS GATEWAY (LAST 40 LINES) ===')
print(run_cmd('docker logs --tail 40 technoreboot-prod-gateway'))
"""

res = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=script,
    capture_output=True,
    text=True
)

print(res.stdout)
if res.stderr:
    print("STDERR:\n", res.stderr)
