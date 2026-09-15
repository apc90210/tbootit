import subprocess

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import subprocess

cmds = [
    "ip route get 217.151.227.96",
    "sysctl net.ipv4.conf.all.rp_filter net.ipv4.conf.default.rp_filter net.ipv4.conf.ens3.rp_filter",
    "sysctl net.ipv4.tcp_mtu_probing",
    "nft list ruleset",
    "ip route",
    "docker network inspect technoreboot-network"
]

for cmd in cmds:
    print(f"=== {cmd} ===")
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(p.stdout)
    if p.stderr:
        print("ERR:", p.stderr)
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

print(proc.stdout)
