import subprocess
import json

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_code = """
import sqlite3, json, subprocess

conn = sqlite3.connect('/srv/technoreboot/data/db/technoreboot.db')
cur = conn.cursor()
tables = ['products', 'sales', 'repair_orders', 'product_photos', 'product_external_listings']
counts = {t: cur.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in tables}
conn.close()

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

print(json.dumps({
    "counts": counts,
    "tcp_mtu_probing": run("sysctl -n net.ipv4.tcp_mtu_probing"),
    "nft_input": run("nft list chain inet filter input"),
    "nft_forward": run("nft list chain inet filter forward"),
    "ss_ports": run("ss -lntup | grep -E ':(22|80|443)'")
}, indent=2))
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
