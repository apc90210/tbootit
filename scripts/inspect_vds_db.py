import subprocess

script = """
import sqlite3
conn = sqlite3.connect('/srv/technoreboot/data/db/technoreboot.db')
cur = conn.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
print(f"Total tables: {len(tables)}")
for t in tables:
    cnt = cur.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
    print(f"{t}: {cnt} rows")
conn.close()
"""

res = subprocess.run(
    ["ssh", "-i", r"C:\Users\Apc\.ssh\id_ed25519", "root@144.31.50.134", "python3"],
    input=script,
    text=True,
    capture_output=True,
)
print(res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)
