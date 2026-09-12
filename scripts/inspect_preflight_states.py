import sqlite3
import hashlib
import os
import subprocess
import json

def get_hash(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_dir_stats(dirpath):
    if not os.path.exists(dirpath):
        return 0, None
    files = []
    for root, _, filenames in os.walk(dirpath):
        for f in filenames:
            rel = os.path.relpath(os.path.join(root, f), dirpath).replace('\\', '/')
            files.append((rel, os.path.join(root, f)))
    files.sort(key=lambda x: x[0])
    h = hashlib.sha256()
    for rel, full in files:
        h.update(rel.encode('utf-8'))
        with open(full, 'rb') as f:
            while chunk := f.read(65536):
                h.update(chunk)
    return len(files), h.hexdigest()

def get_db_stats(db_path):
    if not os.path.exists(db_path):
        return {}
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    counts = {}
    for tbl, key in [('products', 'PRODUCTS'), ('sales', 'SALES'), ('repair_orders', 'REPAIRS'), ('product_photos', 'PHOTOS'), ('product_external_listings', 'LISTINGS')]:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            counts[key] = cur.fetchone()[0]
        except Exception as e:
            counts[key] = str(e)
    conn.close()
    return counts

if __name__ == "__main__":
    local_db = r"C:\tbootit\data\db\technoreboot.db"
    local_ca = r"C:\tbootit\data\auth\ca\ca.crt"
    local_storage = r"C:\tbootit\data\storage"
    
    local_db_hash = get_hash(local_db)
    local_ca_hash = get_hash(local_ca)
    local_storage_count, local_storage_hash = get_dir_stats(local_storage)
    local_counts = get_db_stats(local_db)
    
    # Query VDS
    vds_cmd = (
        "python3 -c \""
        "import sqlite3, hashlib, os, json; "
        "def gh(p): "
        "  if not os.path.exists(p): return None; "
        "  h = hashlib.sha256(); "
        "  with open(p, 'rb') as f: "
        "    while c := f.read(65536): h.update(c); "
        "  return h.hexdigest(); "
        "def gds(dp): "
        "  if not os.path.exists(dp): return 0, None; "
        "  fs = []; "
        "  for r, _, fns in os.walk(dp): "
        "    for f in fns: fs.append((os.path.relpath(os.path.join(r, f), dp), os.path.join(r, f))); "
        "  fs.sort(key=lambda x: x[0]); "
        "  h = hashlib.sha256(); "
        "  for rel, full in fs: "
        "    h.update(rel.encode('utf-8')); "
        "    with open(full, 'rb') as f: "
        "      while c := f.read(65536): h.update(c); "
        "  return len(fs), h.hexdigest(); "
        "conn = sqlite3.connect('/srv/technoreboot/data/db/technoreboot.db'); "
        "cur = conn.cursor(); "
        "counts = {}; "
        "for tbl, key in [('products', 'PRODUCTS'), ('sales', 'SALES'), ('repair_orders', 'REPAIRS'), ('product_photos', 'PHOTOS'), ('product_external_listings', 'LISTINGS')]: "
        "  try: counts[key] = cur.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]; "
        "  except Exception as e: counts[key] = str(e); "
        "conn.close(); "
        "sc, sh = gds('/srv/technoreboot/data/storage'); "
        "res = {'counts': counts, 'db_sha256': gh('/srv/technoreboot/data/db/technoreboot.db'), 'ca_sha256': gh('/srv/technoreboot/data/auth/ca/ca.crt'), 'storage_file_count': sc, 'storage_tree_sha256': sh}; "
        "print(json.dumps(res))\""
    )
    
    ssh_cmd = [
        "ssh", "-i", r"C:\Users\Apc\.ssh\id_ed25519", "root@144.31.50.134",
        vds_cmd
    ]
    try:
        proc = subprocess.run(ssh_cmd, capture_output=True, text=True, check=True)
        vds_data = json.loads(proc.stdout.strip())
    except Exception as e:
        vds_data = {"error": str(e)}

    result = {
        "LOCAL": {
            "counts": local_counts,
            "db_sha256": local_db_hash,
            "ca_sha256": local_ca_hash,
            "storage_file_count": local_storage_count,
            "storage_tree_sha256": local_storage_hash
        },
        "VDS": vds_data
    }
    print(json.dumps(result, indent=2))
