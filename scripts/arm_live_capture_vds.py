import subprocess
import time
import json

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

# Start background tcpdump on VDS capturing into /tmp/stage10c_r2_owner_nonvpn.pcap
remote_code = """
import subprocess
import os
import time

# Kill any previous stale tcpdump
subprocess.run("pkill -f stage10c_r2_owner_nonvpn 2>/dev/null || true", shell=True)

pcap_file = "/tmp/stage10c_r2_owner_nonvpn.pcap"
if os.path.exists(pcap_file):
    os.remove(pcap_file)

# Start 5-minute bounded capture in background
cmd = "nohup tcpdump -ni any -nn -s 0 -w /tmp/stage10c_r2_owner_nonvpn.pcap 'host 144.31.50.134 and (tcp port 80 or tcp port 443 or icmp)' > /tmp/tcpdump_armed.log 2>&1 &"
subprocess.run(cmd, shell=True)

time.sleep(1)

# Check if running
ps_out = subprocess.run("pgrep -a tcpdump", shell=True, capture_output=True, text=True).stdout.strip()
print("ARMED_TCPDUMP_PS:")
print(ps_out)

print("START_TIMESTAMP:", time.strftime('%Y-%m-%dT%H:%M:%S%z'))
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
