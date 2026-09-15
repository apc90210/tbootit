import subprocess
import json
import sys

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import subprocess
import json

def run(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return {
        "stdout": res.stdout.strip(),
        "stderr": res.stderr.strip(),
        "code": res.returncode
    }

# Collect Step 4: Firewall & PMTU
step4 = {
    "nft_input": run("nft list chain inet filter input"),
    "nft_forward": run("nft list chain inet filter forward"),
    "tcp_mtu_probing": run("sysctl -n net.ipv4.tcp_mtu_probing"),
    "ip_no_pmtu_disc": run("sysctl -n net.ipv4.ip_no_pmtu_disc"),
    "tcp_ecn": run("sysctl -n net.ipv4.tcp_ecn"),
    "tcp_sack": run("sysctl -n net.ipv4.tcp_sack"),
    "tcp_window_scaling": run("sysctl -n net.ipv4.tcp_window_scaling"),
    "nftables_conf": run("cat /etc/nftables.conf"),
    "sysctl_conf": run("cat /etc/sysctl.d/99-technoreboot-pmtu.conf 2>/dev/null || true")
}

# Collect Step 5: Real Path MTU tests
# Standard IP header = 20 bytes, ICMP header = 8 bytes. Total = size + 28.
# For MTU 1500, size = 1472. For MTU 1492, size = 1464. For MTU 1460, size = 1432. For MTU 1420, size = 1392.
targets = {
    "ru_moscow": "194.26.229.20",
    "ru_spb": "185.221.199.82",
    "cloudflare_dns": "1.1.1.1",
    "google_dns": "8.8.8.8",
    "gateway": "100.65.65.65"
}

mtu_results = {}
for name, ip in targets.items():
    res_1472 = run(f"ping -c 2 -M do -s 1472 {ip}")
    res_1464 = run(f"ping -c 2 -M do -s 1464 {ip}")
    res_1432 = run(f"ping -c 2 -M do -s 1432 {ip}")
    res_1392 = run(f"ping -c 2 -M do -s 1392 {ip}")
    res_normal = run(f"ping -c 2 {ip}")
    mtu_results[name] = {
        "ip": ip,
        "ping_ok": res_normal["code"] == 0,
        "size_1472_mtu1500": res_1472["code"] == 0,
        "size_1464_mtu1492": res_1464["code"] == 0,
        "size_1432_mtu1460": res_1432["code"] == 0,
        "size_1392_mtu1420": res_1392["code"] == 0,
        "detail_1472": res_1472["stdout"] if res_1472["code"] == 0 else res_1472["stderr"] or res_1472["stdout"]
    }

# Collect Step 9: Asymmetric Routing & rp_filter
step9 = {
    "route_to_ru_moscow": run("ip route get 194.26.229.20"),
    "route_to_ru_spb": run("ip route get 185.221.199.82"),
    "route_to_vpn": run("ip route get 2.27.131.44"),
    "rp_filter_all": run("sysctl -n net.ipv4.conf.all.rp_filter"),
    "rp_filter_default": run("sysctl -n net.ipv4.conf.default.rp_filter"),
    "rp_filter_ens3": run("sysctl -n net.ipv4.conf.ens3.rp_filter"),
}

# Collect Step 10: Live effective Nginx config
step10 = {
    "nginx_t": run("docker exec technoreboot-prod-gateway nginx -T 2>&1")
}

output = {
    "step4_firewall_pmtu": step4,
    "step5_path_mtu": mtu_results,
    "step9_routing_rp_filter": step9,
    "step10_nginx": step10
}

print(json.dumps(output))
"""

print("Executing deep diagnostic script on VDS...")
proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

if proc.returncode != 0:
    print("Remote execution failed!")
    print("STDERR:", proc.stderr)
    sys.exit(proc.returncode)

with open("scripts/vds_deep_diagnostic_10c_r1.json", "w", encoding="utf-8") as f:
    f.write(proc.stdout)

data = json.loads(proc.stdout)
print("=== STEP 4: FIREWALL & PMTU SETTINGS ===")
print("tcp_mtu_probing:", data["step4_firewall_pmtu"]["tcp_mtu_probing"])
print("nft_input:\n", data["step4_firewall_pmtu"]["nft_input"]["stdout"])
print("nft_forward:\n", data["step4_firewall_pmtu"]["nft_forward"]["stdout"])

print("\n=== STEP 5: MEASURED PATH MTU ===")
for k, v in data["step5_path_mtu"].items():
    print(f"{k} ({v['ip']}): ping={v['ping_ok']}, MTU 1500 (payload 1472)={v['size_1472_mtu1500']}, MTU 1492={v['size_1464_mtu1492']}")

print("\n=== STEP 9: ROUTING & RP_FILTER ===")
print("route to Moscow:", data["step9_routing_rp_filter"]["route_to_ru_moscow"]["stdout"])
print("route to SPb:", data["step9_routing_rp_filter"]["route_to_ru_spb"]["stdout"])
print("route to VPN:", data["step9_routing_rp_filter"]["route_to_vpn"]["stdout"])
print("rp_filter all/default/ens3:", 
      data["step9_routing_rp_filter"]["rp_filter_all"],
      data["step9_routing_rp_filter"]["rp_filter_default"],
      data["step9_routing_rp_filter"]["rp_filter_ens3"])
