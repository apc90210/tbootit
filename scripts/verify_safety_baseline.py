#!/usr/bin/env python3
"""
scripts/verify_safety_baseline.py
Captures checksums and values of business fields before/after reference catalog expansion:
- prices (sale_price, purchase_price, min_price, market_price)
- stock (quantity, reserved_quantity)
- statuses (status)
- storage_location
- product_photos table
- serial numbers (serial_number)
- condition (condition)
- individual notes (notes, description)
- sales table
- repairs table
- reservations table
"""

import sqlite3
import hashlib
import json
import os

DB_PATH = r"C:\tbootit\data\db\technoreboot.db"

def capture_baseline(out_file=r"C:\tbootit\data\safety_baseline.json"):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Product business fields (strictly immutable across reference expansion)
    c.execute("""
        SELECT id, sale_price, purchase_price, quantity, reserved_quantity,
               status, serial_number, condition, notes, description, storage_location,
               min_price, market_price
        FROM products
        ORDER BY id
    """)
    products_data = [dict(row) for row in c.fetchall()]

    # Photos table
    c.execute("SELECT id, product_id, filename, storage_path, media_url, sort_order, content_hash FROM product_photos ORDER BY id")
    photos_data = [dict(row) for row in c.fetchall()]

    # Sales & Sale Items
    c.execute("SELECT * FROM sales ORDER BY id")
    sales_data = [dict(row) for row in c.fetchall()]
    c.execute("SELECT * FROM sale_items ORDER BY id")
    sale_items_data = [dict(row) for row in c.fetchall()]

    # Repair orders
    c.execute("SELECT * FROM repair_orders ORDER BY id")
    repairs_data = [dict(row) for row in c.fetchall()]

    # Reservation requests
    c.execute("SELECT * FROM reservation_requests ORDER BY id")
    reservations_data = [dict(row) for row in c.fetchall()]

    payload = {
        "products_count": len(products_data),
        "products_hash": hashlib.sha256(json.dumps(products_data, sort_keys=True, default=str).encode()).hexdigest(),
        "photos_count": len(photos_data),
        "photos_hash": hashlib.sha256(json.dumps(photos_data, sort_keys=True, default=str).encode()).hexdigest(),
        "sales_count": len(sales_data),
        "sales_hash": hashlib.sha256(json.dumps(sales_data, sort_keys=True, default=str).encode()).hexdigest(),
        "sale_items_count": len(sale_items_data),
        "sale_items_hash": hashlib.sha256(json.dumps(sale_items_data, sort_keys=True, default=str).encode()).hexdigest(),
        "repair_orders_count": len(repairs_data),
        "repair_orders_hash": hashlib.sha256(json.dumps(repairs_data, sort_keys=True, default=str).encode()).hexdigest(),
        "reservation_requests_count": len(reservations_data),
        "reservation_requests_hash": hashlib.sha256(json.dumps(reservations_data, sort_keys=True, default=str).encode()).hexdigest(),
        "products_data": products_data,
        "repairs_data": repairs_data
    }

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Safety baseline captured successfully:")
    print(f"  Products:     {payload['products_count']} items, SHA256: {payload['products_hash'][:16]}...")
    print(f"  Photos:       {payload['photos_count']} items, SHA256: {payload['photos_hash'][:16]}...")
    print(f"  Sales:        {payload['sales_count']} items, SHA256: {payload['sales_hash'][:16]}...")
    print(f"  Sale items:   {payload['sale_items_count']} items, SHA256: {payload['sale_items_hash'][:16]}...")
    print(f"  Repairs:      {payload['repair_orders_count']} items, SHA256: {payload['repair_orders_hash'][:16]}...")
    print(f"  Reservations: {payload['reservation_requests_count']} items, SHA256: {payload['reservation_requests_hash'][:16]}...")
    conn.close()
    return payload

def compare_against_baseline(baseline_file=r"C:\tbootit\data\safety_baseline.json"):
    with open(baseline_file, "r", encoding="utf-8") as f:
        base = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT id, sale_price, purchase_price, quantity, reserved_quantity,
               status, serial_number, condition, notes, description, storage_location,
               min_price, market_price
        FROM products
        ORDER BY id
    """)
    current_products = [dict(row) for row in c.fetchall()]

    c.execute("SELECT id, product_id, filename, storage_path, media_url, sort_order, content_hash FROM product_photos ORDER BY id")
    current_photos = [dict(row) for row in c.fetchall()]

    c.execute("SELECT * FROM sales ORDER BY id")
    current_sales = [dict(row) for row in c.fetchall()]

    c.execute("SELECT * FROM sale_items ORDER BY id")
    current_sale_items = [dict(row) for row in c.fetchall()]

    c.execute("SELECT * FROM repair_orders ORDER BY id")
    current_repairs = [dict(row) for row in c.fetchall()]

    c.execute("SELECT * FROM reservation_requests ORDER BY id")
    current_reservations = [dict(row) for row in c.fetchall()]
    conn.close()

    curr_p_hash = hashlib.sha256(json.dumps(current_products, sort_keys=True, default=str).encode()).hexdigest()
    curr_ph_hash = hashlib.sha256(json.dumps(current_photos, sort_keys=True, default=str).encode()).hexdigest()
    curr_s_hash = hashlib.sha256(json.dumps(current_sales, sort_keys=True, default=str).encode()).hexdigest()
    curr_si_hash = hashlib.sha256(json.dumps(current_sale_items, sort_keys=True, default=str).encode()).hexdigest()
    curr_r_hash = hashlib.sha256(json.dumps(current_repairs, sort_keys=True, default=str).encode()).hexdigest()
    curr_res_hash = hashlib.sha256(json.dumps(current_reservations, sort_keys=True, default=str).encode()).hexdigest()

    p_match = curr_p_hash == base["products_hash"]
    ph_match = curr_ph_hash == base["photos_hash"]
    s_match = curr_s_hash == base["sales_hash"]
    si_match = curr_si_hash == base["sale_items_hash"]
    r_match = curr_r_hash == base["repair_orders_hash"]
    res_match = curr_res_hash == base["reservation_requests_hash"]

    print("\n--- SAFETY COMPARISON REPORT ---")
    print(f"Products business fields match: {p_match} ({curr_p_hash[:16]} vs {base['products_hash'][:16]})")
    print(f"Photos table match:             {ph_match} ({curr_ph_hash[:16]} vs {base['photos_hash'][:16]})")
    print(f"Sales table match:              {s_match} ({curr_s_hash[:16]} vs {base['sales_hash'][:16]})")
    print(f"Sale items table match:         {si_match} ({curr_si_hash[:16]} vs {base['sale_items_hash'][:16]})")
    print(f"Repair orders table match:      {r_match} ({curr_r_hash[:16]} vs {base['repair_orders_hash'][:16]})")
    print(f"Reservation requests match:     {res_match} ({curr_res_hash[:16]} vs {base['reservation_requests_hash'][:16]})")

    if not p_match:
        base_map = {p["id"]: p for p in base["products_data"]}
        diffs = []
        for cp in current_products:
            bp = base_map.get(cp["id"])
            if not bp:
                diffs.append(f"Product #{cp['id']} not in baseline")
                continue
            for k in cp:
                if str(cp[k]) != str(bp.get(k)):
                    diffs.append(f"Product #{cp['id']} field '{k}' changed from '{bp.get(k)}' to '{cp[k]}'")
        print(f"Product field differences ({len(diffs)}):")
        for d in diffs[:10]:
            print("  ", d)

    if not r_match and "repairs_data" in base:
        base_r_map = {r["id"]: r for r in base["repairs_data"]}
        r_diffs = []
        for cr in current_repairs:
            br = base_r_map.get(cr["id"])
            if not br:
                r_diffs.append(f"Repair order #{cr['id']} not in baseline")
                continue
            for k in cr:
                if str(cr[k]) != str(br.get(k)):
                    r_diffs.append(f"Repair order #{cr['id']} field '{k}' changed from '{br.get(k)}' to '{cr[k]}'")
        print(f"Repair order differences ({len(r_diffs)}):")
        for d in r_diffs[:10]:
            print("  ", d)

    all_passed = (p_match and ph_match and s_match and si_match and r_match and res_match)
    print(f"Overall business integrity: {'PASSED (Zero unwanted modifications)' if all_passed else 'FAILED'}")
    return {
        "products_match": p_match,
        "photos_match": ph_match,
        "sales_match": s_match,
        "sale_items_match": si_match,
        "repairs_match": r_match,
        "reservations_match": res_match,
        "all_passed": all_passed
    }

if __name__ == "__main__":
    import sys
    target_f = sys.argv[2] if len(sys.argv) > 2 else r"C:\tbootit\data\safety_baseline.json"
    if "--compare" in sys.argv:
        compare_against_baseline(target_f)
    else:
        capture_baseline(target_f)
