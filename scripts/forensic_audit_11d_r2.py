import zipfile
import sqlite3
import os
import json
from datetime import datetime

BACKUP_PATH = '/srv/technoreboot/data/backups/TECHNOREBOOT_BACKUP_2026-09-17_110805.zip'
CURRENT_DB_PATH = '/srv/technoreboot/data/db/technoreboot.db'
TMP_BACKUP_DB = '/tmp/pre_incident_technoreboot.db'

# 1. Extract pre-incident DB
with zipfile.ZipFile(BACKUP_PATH) as z:
    for name in z.namelist():
        if name.endswith('.db'):
            with open(TMP_BACKUP_DB, 'wb') as f:
                f.write(z.read(name))
            break

pre_conn = sqlite3.connect(TMP_BACKUP_DB)
pre_conn.row_factory = sqlite3.Row
cur_conn = sqlite3.connect(CURRENT_DB_PATH)
cur_conn.row_factory = sqlite3.Row

print("=== 1. AUDIT LOG INSPECTION ===")
audit_rows = cur_conn.execute("SELECT * FROM audit_log WHERE entity_type='repair_order' OR entity_id=1 OR action='permanent_delete'").fetchall()
print(f"Found {len(audit_rows)} relevant audit log entries:")
for r in audit_rows:
    print(dict(r))

print("\n=== 2. REPAIR #1 ROW COMPARISON ===")
pre_rep1 = pre_conn.execute("SELECT * FROM repair_orders WHERE id=1").fetchone()
cur_rep1 = cur_conn.execute("SELECT * FROM repair_orders WHERE id=1").fetchone()

print("PRE_INCIDENT REPAIR #1:")
print(dict(pre_rep1) if pre_rep1 else "NOT FOUND")
print("CURRENT REPAIR #1:")
print(dict(cur_rep1) if cur_rep1 else "NOT FOUND")

if pre_rep1 and cur_rep1:
    diffs = {}
    for k in pre_rep1.keys():
        if pre_rep1[k] != cur_rep1[k]:
            diffs[k] = {"pre": pre_rep1[k], "cur": cur_rep1[k]}
    print("DIFFS in Repair #1:", diffs)

print("\n=== 3. REPAIR STATUS HISTORY COMPARISON ===")
pre_hists = pre_conn.execute("SELECT * FROM repair_status_history WHERE repair_id=1 ORDER BY id").fetchall()
cur_hists = cur_conn.execute("SELECT * FROM repair_status_history WHERE repair_id=1 ORDER BY id").fetchall()

print(f"Pre-incident history count: {len(pre_hists)}")
for h in pre_hists:
    print("  PRE:", dict(h))

print(f"Current history count: {len(cur_hists)}")
for h in cur_hists:
    print("  CUR:", dict(h))

print("\n=== 4. ALL REPAIR ORDERS & HISTORY (COLLATERAL AUDIT) ===")
all_pre_reps = pre_conn.execute("SELECT * FROM repair_orders ORDER BY id").fetchall()
all_cur_reps = cur_conn.execute("SELECT * FROM repair_orders ORDER BY id").fetchall()
print(f"Total repair_orders: pre={len(all_pre_reps)}, cur={len(all_cur_reps)}")

all_pre_hists = pre_conn.execute("SELECT * FROM repair_status_history ORDER BY id").fetchall()
all_cur_hists = cur_conn.execute("SELECT * FROM repair_status_history ORDER BY id").fetchall()
print(f"Total repair_status_history: pre={len(all_pre_hists)}, cur={len(all_cur_hists)}")

print("\n=== 5. SALES & REFERENCED SALE AUDIT ===")
pre_sale_3 = pre_conn.execute("SELECT * FROM sales WHERE id=3").fetchone()
cur_sale_3 = cur_conn.execute("SELECT * FROM sales WHERE id=3").fetchone()
print("Pre-incident Sale #3 existed in backup:", pre_sale_3 is not None, dict(pre_sale_3) if pre_sale_3 else "")
print("Current Sale #3 exists in DB:", cur_sale_3 is not None, dict(cur_sale_3) if cur_sale_3 else "")

all_pre_sales = [dict(r) for r in pre_conn.execute("SELECT id, total_amount, status, source_type, source_id FROM sales ORDER BY id").fetchall()]
all_cur_sales = [dict(r) for r in cur_conn.execute("SELECT id, total_amount, status, source_type, source_id FROM sales ORDER BY id").fetchall()]
print(f"Pre-incident sales ({len(all_pre_sales)}):", all_pre_sales)
print(f"Current sales ({len(all_cur_sales)}):", all_cur_sales)

# Check sales referencing repair 1
cur_rep_sales = cur_conn.execute("SELECT * FROM sales WHERE source_type='repair' AND source_id=1").fetchall()
print(f"Current sales with source_type='repair' and source_id=1: {len(cur_rep_sales)}")

print("\n=== 6. GLOBAL BUSINESS TABLE COUNTS ===")
tables = [
    "products", "sales", "repair_orders", "repair_status_history",
    "product_photos", "product_external_listings", "avito_post_sale_tasks",
    "sale_items", "sale_revisions", "audit_log"
]
counts_pre = {}
counts_cur = {}
for t in tables:
    try:
        counts_pre[t] = pre_conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    except Exception as e:
        counts_pre[t] = f"ERR: {e}"
    try:
        counts_cur[t] = cur_conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    except Exception as e:
        counts_cur[t] = f"ERR: {e}"
    print(f"Table '{t}': PRE={counts_pre[t]} | CURRENT={counts_cur[t]}")

print("\n=== 7. INTEGRITY CHECKS ===")
qc = cur_conn.execute("PRAGMA quick_check").fetchall()
print("PRAGMA quick_check:", [dict(r) for r in qc])
fkc = cur_conn.execute("PRAGMA foreign_key_check").fetchall()
print("PRAGMA foreign_key_check violations:", [dict(r) for r in fkc])

# Orphan checks
orphan_rep_sales = cur_conn.execute("SELECT id, number, sale_id FROM repair_orders WHERE sale_id IS NOT NULL AND sale_id NOT IN (SELECT id FROM sales)").fetchall()
print("Orphan repair_orders.sale_id:", [dict(r) for r in orphan_rep_sales])

orphan_rep_hists = cur_conn.execute("SELECT id, repair_id FROM repair_status_history WHERE repair_id NOT IN (SELECT id FROM repair_orders)").fetchall()
print("Orphan repair_status_history.repair_id:", [dict(r) for r in orphan_rep_hists])

orphan_sale_items = cur_conn.execute("SELECT id, sale_id FROM sale_items WHERE sale_id NOT IN (SELECT id FROM sales)").fetchall()
print("Orphan sale_items.sale_id:", [dict(r) for r in orphan_sale_items])

if os.path.exists(TMP_BACKUP_DB):
    os.remove(TMP_BACKUP_DB)
