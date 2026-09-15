import subprocess
import json
import sys

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_code = """
import subprocess
import os

# 1. Stop tcpdump
subprocess.run("pkill -f stage10c_r2_owner_nonvpn 2>/dev/null || true", shell=True)

# 2. Read pcap packets
pcap_file = "/tmp/stage10c_r2_owner_nonvpn.pcap"
if not os.path.exists(pcap_file):
    print("PCAP_STATUS: NOT_FOUND")
    exit(1)

size = os.path.getsize(pcap_file)
print(f"PCAP_SIZE_BYTES: {size}")

# Dump packets excluding known crawlers / test nodes if desired, or all packets
dump_cmd = f"tcpdump -nn -r {pcap_file} -vv"
dump_out = subprocess.run(dump_cmd, shell=True, capture_output=True, text=True).stdout.strip()
print("=== DUMPED_PACKETS ===")
print(dump_out if dump_out else "(No packets captured in PCAP)")

# 3. Nginx recent access logs
print("\\n=== NGINX_RECENT_LOGS ===")
nginx_out = subprocess.run("docker logs --tail 30 technoreboot-prod-gateway 2>&1", shell=True, capture_output=True, text=True).stdout.strip()
print(nginx_out)

# 4. Conntrack entries for 80 and 443
print("\\n=== CONNTRACK_ENTRIES ===")
ct_out = subprocess.run("conntrack -L -p tcp --dport 443 2>/dev/null || ss -tuna '( dport = :443 or dport = :80 )'", shell=True, capture_output=True, text=True).stdout.strip()
print(ct_out)
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_code,
    capture_output=True,
    text=True
)

print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr)
