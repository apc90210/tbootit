import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_code = """
import subprocess
out = subprocess.run("tcpdump -nn -r /tmp/stage10c_r2_owner_nonvpn.pcap 'host 217.151.227.96' -vv", shell=True, capture_output=True, text=True).stdout
print(out)
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_code,
    capture_output=True,
    text=True
)

print(proc.stdout)
