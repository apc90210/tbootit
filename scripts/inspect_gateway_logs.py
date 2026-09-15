import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import subprocess

cmd = "docker logs technoreboot-prod-gateway 2>&1"
out = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

for line in out.splitlines()[-200:]:
    if "217.151.227.96" in line or "error" in line.lower() or "ssl" in line.lower():
        print(line)
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

print("--- MATCHING NGINX LOGS ---")
print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr)
