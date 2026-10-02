import sqlite3
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect('C:/tbootit/data/db/technoreboot.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute('SELECT id, name FROM categories')
cat_map = {row['id']: row['name'] for row in c.fetchall()}

c.execute('''
    SELECT p.id, p.category_id, p.reference_model_id
    FROM products p
    ORDER BY p.id
''')
products = c.fetchall()

cat_order = [
    "Принтеры",
    "МФУ",
    "Мониторы",
    "Ноутбуки",
    "Компьютеры",
    "Комплектующие",
    "Техника под восстановление",
    "Без категории"
]

cat_counts = {cat: {"total": 0, "linked": 0} for cat in cat_order}

for p in products:
    cname = cat_map.get(p["category_id"], "Без категории")
    if cname not in cat_counts:
        cname = "Без категории"
    cat_counts[cname]["total"] += 1
    if p["reference_model_id"] is not None:
        cat_counts[cname]["linked"] += 1

print("\n--- FINAL COVERAGE BY CATEGORY ---")
print(f"| {'Category':26} | {'Products':>8} | {'Linked before':>13} | {'Linked after':>12} | {'Coverage':>8} |")
print(f"|{'-'*28}|{'-'*10}:|{'-'*15}:|{'-'*14}:|{'-'*10}:|")

# Known linked before counts
linked_before_map = {
    "Принтеры": 38,
    "МФУ": 44,
    "Мониторы": 0,
    "Ноутбуки": 4,
    "Компьютеры": 0,
    "Комплектующие": 1,
    "Техника под восстановление": 2,
    "Без категории": 0
}

tot_prod = 0
tot_before = 0
tot_after = 0

for cat in cat_order:
    st = cat_counts[cat]
    before = linked_before_map.get(cat, 0)
    after = st["linked"]
    tot_prod += st["total"]
    tot_before += before
    tot_after += after
    cov_pct = (after / st["total"] * 100) if st["total"] > 0 else 0
    print(f"| {cat:26} | {st['total']:8} | {before:13} | {after:12} | {cov_pct:7.1f}% |")

tot_cov = (tot_after / tot_prod * 100) if tot_prod > 0 else 0
print(f"| {'TOTAL':26} | {tot_prod:8} | {tot_before:13} | {tot_after:12} | {tot_cov:7.1f}% |")
