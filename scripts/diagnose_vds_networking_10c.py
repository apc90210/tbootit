import subprocess
import json
from pathlib import Path

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import subprocess, json

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return {
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip(),
            "code": res.returncode
        }
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "code": -1}

commands = {
    "ss_lntup": "ss -lntup",
    "docker_ps": "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'",
    "gateway_logs": "docker logs --tail 100 technoreboot-prod-gateway",
    "ip_addr": "ip addr",
    "ip_route": "ip route",
    "ip_rule": "ip rule",
    "sysctl_ip_forward": "sysctl net.ipv4.ip_forward",
    "nft_ruleset": "nft list ruleset",
    "iptables_save": "iptables-save",
    "ip6tables_save": "ip6tables-save",
    "ufw_status": "ufw status verbose",
    "firewalld": "firewall-cmd --list-all",
    "fail2ban_status": "fail2ban-client status",
    "ipset_list": "ipset list",
    "nginx_t": "docker exec technoreboot-prod-gateway nginx -T",
}

results = {}
for name, cmd in commands.items():
    results[name] = run_cmd(cmd)

print(json.dumps(results))
"""

print("Running baseline network diagnostic on VDS...")
proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

if proc.returncode != 0:
    print("Failed to run remote script!")
    print("STDERR:", proc.stderr)
    exit(1)

try:
    data = json.loads(proc.stdout)
except Exception as e:
    print("Failed to parse JSON output:", e)
    print("Raw stdout:\n", proc.stdout[:2000])
    exit(1)

out_file = Path(__file__).resolve().parent / "vds_network_baseline_10c.json"
out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Network baseline saved to {out_file}")

# Print summary
print("\n--- Listening Ports (ss -lntup) ---")
print(data["ss_lntup"]["stdout"])

print("\n--- Docker PS ---")
print(data["docker_ps"]["stdout"])

print("\n--- UFW Status ---")
print(data["ufw_status"]["stdout"] if data["ufw_status"]["stdout"] else data["ufw_status"]["stderr"])

print("\n--- Fail2ban Status ---")
print(data["fail2ban_status"]["stdout"] if data["fail2ban_status"]["stdout"] else data["fail2ban_status"]["stderr"])

print("\n--- Ipset List ---")
print(data["ipset_list"]["stdout"] if data["ipset_list"]["stdout"] else data["ipset_list"]["stderr"])

print("\n--- iptables-save (First 40 lines or grep) ---")
iptables = data["iptables_save"]["stdout"]
print("\n".join(iptables.splitlines()[:50]))
