import subprocess
import hashlib
import json

ssh_key = r"C:\Users\Apc\.ssh\id_ed25519"
vds_host = "root@144.31.50.134"

remote_code = """
import sqlite3, hashlib, json

conn = sqlite3.connect("file:/srv/technoreboot/data/db/technoreboot.db?mode=ro", uri=True)
cur = conn.cursor()
counts = {}
for tbl in ["products", "sales", "repair_orders", "product_photos", "product_external_listings"]:
    cur.execute(f"SELECT COUNT(*) FROM {tbl}")
    counts[tbl] = cur.fetchone()[0]

with open("/srv/technoreboot/data/db/technoreboot.db", "rb") as f:
    h = hashlib.sha256(f.read()).hexdigest()

print(json.dumps({"counts": counts, "db_sha256": h}))
"""

res = subprocess.run(["ssh", "-i", ssh_key, "-o", "ConnectTimeout=15", vds_host, "python3 -"], input=remote_code, capture_output=True, text=True)
print("STDOUT:", res.stdout.strip())
if res.stderr:
    print("STDERR:", res.stderr.strip())
