import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import subprocess

cmd = "tcpdump -nn -r /tmp/stage10c_r2_owner_nonvpn.pcap 'host 217.151.227.96'"
out = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

lines = out.splitlines()
print(f"Total packets for 217.151.227.96: {len(lines)}")

# Group by client port
by_port = {}
for line in lines:
    parts = line.split()
    if len(parts) < 5:
        continue
    # identify port
    src = parts[2]
    dst = parts[4].rstrip(':')
    port = None
    if "217.151.227.96." in src:
        port = src.split("217.151.227.96.")[1]
    elif "217.151.227.96." in dst:
        port = dst.split("217.151.227.96.")[1]
    
    if port:
        by_port.setdefault(port, []).append(line)

for port, pkts in sorted(by_port.items()):
    print(f"\\n--- PORT {port} ({len(pkts)} packets) ---")
    for pkt in pkts[:15]:
        print(pkt)
    if len(pkts) > 15:
        print(f"... and {len(pkts) - 15} more")
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr)
