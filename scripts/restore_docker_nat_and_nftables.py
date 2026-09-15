import subprocess
import json

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_code = """
import subprocess
import shutil

def run(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

print("=== [1/4] Updating /etc/nftables.conf to isolate table inet filter ===")
nft_content = '''table inet filter
delete table inet filter
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
with open("/etc/nftables.conf", "w") as f:
    f.write(nft_content)

code, out, err = run("nft -f /etc/nftables.conf")
print("nft -f /etc/nftables.conf code:", code, err if code != 0 else "OK")

print("=== [2/4] Restarting docker to regenerate kernel iptables NAT chains ===")
code, out, err = run("systemctl restart docker")
print("systemctl restart docker code:", code)

print("=== [3/4] Verifying iptables NAT rules ===")
code, out, err = run("iptables -t nat -S")
print("iptables -t nat -S (first 10 lines):")
for line in out.splitlines()[:15]:
    print(line)

print("=== [4/4] Verifying all nftables tables ===")
code, out, err = run("nft list tables")
print("nft list tables:")
print(out)

code, out, err = run("docker ps --format '{{.Names}} {{.Status}}'")
print("\\nDocker containers status:")
print(out)
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_code,
    capture_output=True,
    text=True
)

print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr)
