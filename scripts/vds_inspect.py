import sqlite3
import hashlib
import os
import json

def gh(p):
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while c := f.read(65536):
            h.update(c)
    return h.hexdigest()

def gds(dp):
    if not os.path.exists(dp):
        return 0, None
    fs = []
    for r, _, fns in os.walk(dp):
        for f in fns:
            fs.append((os.path.relpath(os.path.join(r, f), dp), os.path.join(r, f)))
    fs.sort(key=lambda x: x[0])
    h = hashlib.sha256()
    for rel, full in fs:
        h.update(rel.encode('utf-8'))
        with open(full, 'rb') as f:
            while c := f.read(65536):
                h.update(c)
    return len(fs), h.hexdigest()

conn = sqlite3.connect('/srv/technoreboot/data/db/technoreboot.db')
cur = conn.cursor()
counts = {}
for tbl, key in [('products', 'PRODUCTS'), ('sales', 'SALES'), ('repair_orders', 'REPAIRS'), ('product_photos', 'PHOTOS'), ('product_external_listings', 'LISTINGS')]:
    try:
        counts[key] = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    except Exception as e:
        counts[key] = str(e)
conn.close()

sc, sh = gds('/srv/technoreboot/data/storage')
res = {
    'counts': counts,
    'db_sha256': gh('/srv/technoreboot/data/db/technoreboot.db'),
    'ca_sha256': gh('/srv/technoreboot/data/auth/ca/ca.crt'),
    'storage_file_count': sc,
    'storage_tree_sha256': sh
}
print(json.dumps(res, indent=2))
