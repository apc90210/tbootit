import subprocess
import json
import sys

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_code = """
import subprocess
import shutil
import os

def run(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

print("=== [1/5] Backing up /etc/nftables.conf ===")
shutil.copy2("/etc/nftables.conf", "/etc/nftables.conf.bak.20260915")
print("Backup created at /etc/nftables.conf.bak.20260915")

print("=== [2/5] Preparing updated nftables.conf with ICMP rules ===")
with open("/etc/nftables.conf", "r") as f:
    old_content = f.read()

# Add icmp rules if not already present
new_lines = []
for line in old_content.splitlines():
    new_lines.append(line)
    if "ct state established,related accept" in line:
        new_lines.append("        ip protocol icmp accept")
        new_lines.append("        ip6 nexthdr ipv6-icmp accept")

new_content = "\\n".join(new_lines) + "\\n"
with open("/tmp/new_nft.conf", "w") as f:
    f.write(new_content)

print("Validating syntax of /tmp/new_nft.conf...")
code, out, err = run("nft -c -f /tmp/new_nft.conf")
if code != 0:
    print("Syntax error in new nftables config:", err)
    sys.exit(1)
print("Syntax valid!")

print("=== [3/5] Applying updated nftables ===")
shutil.copy2("/tmp/new_nft.conf", "/etc/nftables.conf")
code, out, err = run("nft -f /etc/nftables.conf")
if code != 0:
    print("Failed to apply nftables:", err)
    shutil.copy2("/etc/nftables.conf.bak.20260915", "/etc/nftables.conf")
    run("nft -f /etc/nftables.conf")
    sys.exit(1)
print("nftables applied successfully!")

print("=== [4/5] Enabling TCP MTU probing (PLPMTUD) and MSS clamping ===")
code, out, err = run("sysctl -w net.ipv4.tcp_mtu_probing=1")
print("sysctl tcp_mtu_probing:", out)
with open("/etc/sysctl.d/99-technoreboot-pmtu.conf", "w") as f:
    f.write("net.ipv4.tcp_mtu_probing = 1\\n")

# Check if nft forward chain can do rt mtu clamping
test_nft = '''flush ruleset
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        iif lo accept
        ct state established,related accept
        ip protocol icmp accept
        ip6 nexthdr ipv6-icmp accept
        iifname "docker0" accept
        iifname "br-*" accept
        iifname "veth*" accept
        tcp dport 22 accept
        tcp dport 80 accept
        tcp dport 443 accept
    }
    chain forward {
        type filter hook forward priority 0; policy accept;
        tcp flags syn tcp option maxseg size set rt mtu
    }
    chain output {
        type filter hook output priority 0; policy accept;
    }
}
'''
with open('/tmp/test_maxseg.conf', 'w') as f:
    f.write(test_nft)
code, out, err = run("nft -c -f /tmp/test_maxseg.conf")
if code == 0:
    print("nftables supports rt mtu clamping, writing to /etc/nftables.conf")
    with open('/etc/nftables.conf', 'w') as f:
        f.write(test_nft)
    run("nft -f /etc/nftables.conf")
else:
    print("nftables rt mtu not supported (err: %s), falling back to iptables TCPMSS" % err)
    # Check if TCPMSS rule is in iptables
    code, out, err = run("iptables -t mangle -C FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu 2>/dev/null")
    if code != 0:
        run("iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu")
        print("Added TCPMSS clamping to iptables mangle FORWARD")
    # Make iptables rule persistent via systemd service
    service_content = '''[Unit]
Description=TechnoReboot TCPMSS Clamping
After=network.target docker.service

[Service]
Type=oneshot
ExecStart=/sbin/iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
'''
    with open('/etc/systemd/system/technoreboot-tcpmss.service', 'w') as f:
        f.write(service_content)
    run("systemctl daemon-reload && systemctl enable technoreboot-tcpmss.service")


print("=== [5/5] Verification on VDS ===")
code, out, err = run("nft list chain inet filter input")
print("nft input chain:")
print(out)
"""

print("Running apply script on VDS...")
proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_code,
    capture_output=True,
    text=True
)

print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr)

if proc.returncode != 0:
    print(f"Apply failed with code {proc.returncode}!")
    sys.exit(proc.returncode)
