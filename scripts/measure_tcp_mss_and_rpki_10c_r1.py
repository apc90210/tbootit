import subprocess
import time
import json
import urllib.request

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

# 1. Query RPKI status via RIPEstat
rpki_url = "https://stat.ripe.net/data/rpki-validation/data.json?resource=144.31.50.0/24&prefix=144.31.50.0/24"
req = urllib.request.Request(rpki_url, headers={"User-Agent": "Mozilla/5.0"})
try:
    rpki_data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())["data"]
except Exception as e:
    rpki_data = {"status": f"error: {e}"}

print("=== RPKI VALIDATION ===")
print(json.dumps(rpki_data, indent=2))

# 2. Verbose TCP MSS capture during check-host connect from Russian node ru2 (Moscow)
cmd = [
    "ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST,
    "timeout 12 tcpdump -ni ens3 -vv -c 10 'tcp[tcpflags] & (tcp-syn) != 0 and (host 194.26.229.20 or host 185.221.199.82)'"
]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
time.sleep(2)

# Trigger check-host HTTP request
check_url = "https://check-host.net/check-http?host=http://144.31.50.134/&node=ru2.node.check-host.net&node=ru3.node.check-host.net"
req = urllib.request.Request(check_url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"})
urllib.request.urlopen(req, timeout=10)

stdout, stderr = p.communicate(timeout=15)
print("\n=== VERBOSE SYN / MSS CAPTURE ===")
print(stdout)
