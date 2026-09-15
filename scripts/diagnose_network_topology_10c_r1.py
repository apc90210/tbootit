import subprocess
import json

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_code = """
import subprocess
import json

def run(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return {
        "stdout": res.stdout.strip(),
        "stderr": res.stderr.strip(),
        "code": res.returncode
    }

cmds = {
    "ip_br_addr": "ip -br addr",
    "ip_addr_show": "ip addr show",
    "ip_route_show_table_all": "ip route show table all",
    "ip_rule_show": "ip rule show",
    "ip_neigh_show": "ip neigh show",
    "ip_link_show": "ip link show",
    "ip_d_link_show": "ip -d link show ens3",
    "network_interfaces_file": "cat /etc/network/interfaces 2>/dev/null || true",
    "netplan_files": "cat /etc/netplan/*.yaml 2>/dev/null || true",
    "systemd_networkd": "cat /etc/systemd/network/*.network 2>/dev/null || true"
}

results = {k: run(v) for k, v in cmds.items()}
print(json.dumps(results, indent=2))
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_code,
    capture_output=True,
    text=True
)

if proc.returncode != 0:
    print("SSH failed:", proc.stderr)
    exit(1)

with open("scripts/vds_topology_10c_r1.json", "w", encoding="utf-8") as f:
    f.write(proc.stdout)

data = json.loads(proc.stdout)
print("=== IP -BR ADDR ===")
print(data["ip_br_addr"]["stdout"])
print("\n=== IP ROUTE SHOW TABLE ALL ===")
print(data["ip_route_show_table_all"]["stdout"])
print("\n=== IP NEIGH SHOW ===")
print(data["ip_neigh_show"]["stdout"])
print("\n=== IP -D LINK SHOW ENS3 ===")
print(data["ip_d_link_show"]["stdout"])
print("\n=== /etc/network/interfaces ===")
print(data["network_interfaces_file"]["stdout"])
