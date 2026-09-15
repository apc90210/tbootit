import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import subprocess

cmd = "tcpdump -nn -r /tmp/stage10c_r2_owner_nonvpn.pcap 'host 217.151.227.96'"
out = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
lines = out.splitlines()
print(f"Total: {len(lines)}")
for i, line in enumerate(lines):
    print(f"{i:02d}: {line}")
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

print(proc.stdout)
