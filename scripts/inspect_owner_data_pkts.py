import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import subprocess

cmd = "tcpdump -nn -r /tmp/stage10c_r2_owner_nonvpn.pcap 'host 217.151.227.96' -X"
out = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

# Find all packets with data from 217.151.227.96
lines = out.splitlines()
current_hdr = ""
for line in lines:
    if " > 144.31.50.134" in line and "length " in line:
        current_hdr = line
        print("="*60)
        print(current_hdr)
    elif current_hdr and line.startswith("\t0x00"):
        print(line)
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

print(proc.stdout)
