import subprocess
import time
import sys

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30

remote_code = f"""
import subprocess, time

print("Starting live packet and log watch for {duration} seconds...")
tcpdump_cmd = "timeout {duration} tcpdump -ni ens3 -n 'tcp port 80 or tcp port 443 and not host 2.27.131.44 and not host 194.26.229.20 and not host 185.221.199.82'"
p = subprocess.Popen(tcpdump_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

out, err = p.communicate()
print("=== TCPDUMP CAPTURE (EXCLUDING KNOWN VPN / TEST NODES) ===")
print(out if out.strip() else "(No packets captured from external non-VPN sources during the window)")

print("\\n=== GATEWAY ACCESS LOG (LAST 20 ENTRIES) ===")
res = subprocess.run("docker logs --tail 20 technoreboot-prod-gateway", shell=True, capture_output=True, text=True)
print(res.stdout)
"""

print(f"Launching watch on VDS for {duration} seconds...")
proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_code,
    capture_output=True,
    text=True
)

print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr)
