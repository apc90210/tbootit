import subprocess
import time
import json
import urllib.request

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

# Launch tcpdump in background on VDS
cmd = [
    "ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST,
    "timeout 15 tcpdump -ni ens3 -n 'tcp port 80 and (host 194.26.229.20 or host 185.221.199.82)'"
]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

time.sleep(2)

# Trigger check-host HTTP request from ru2 and ru3
url = "https://check-host.net/check-http?host=http://144.31.50.134/&node=ru2.node.check-host.net&node=ru3.node.check-host.net"
req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"})
data = json.loads(urllib.request.urlopen(req).read().decode())
print("Check-host triggered, request_id:", data.get("request_id"))

stdout, stderr = p.communicate(timeout=25)
print("TCPDUMP OUTPUT:")
print(stdout)
if stderr:
    print("STDERR:", stderr)
