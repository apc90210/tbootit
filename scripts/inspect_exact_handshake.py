import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import subprocess

cmd = "tcpdump -nn -r /tmp/stage10c_r2_owner_nonvpn.pcap 'host 217.151.227.96' -vv"
out = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

# Filter packets around 08:10:39
for line in out.splitlines():
    if "08:10:39" in line or "08:10:40" in line or "08:10:41" in line:
        print(line)
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
