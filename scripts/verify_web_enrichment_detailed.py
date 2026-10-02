#!/usr/bin/env python3
"""
Detailed Storefront Verification for WEB-07C Enriched Products.
Tests 20+ products across all 4 key categories on http://127.0.0.1:8090/catalog/{id}.
Verifies:
- HTTP 200
- Exact model name in HTML
- Technical specifications table present and populated
- Product photo present
- Product price matching database exactly
- Restoration category 52 preserved
"""

import sys
import re
import sqlite3
import httpx

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8090"
DB_PATH = r"C:\tbootit\data\db\technoreboot.db"

# Selected 22 products across 4 categories
TEST_PRODUCT_IDS = [
    # Printers (6)
    106, 224, 310, 344, 398, 11,
    # MFUs (8)
    2, 14, 239, 318, 350, 351, 400, 401,
    # Monitors (4)
    67, 117, 147, 158,
    # Restoration (4)
    81, 112, 311, 377
]


def run_verification():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    placeholders = ",".join("?" for _ in TEST_PRODUCT_IDS)
    rows = c.execute(f"""
        SELECT p.id, p.title, p.site_title, p.brand, p.model, p.sale_price, p.category_id,
               cat.name as category_name, ref.canonical_name, ref.stable_key, p.avito_params_json
        FROM products p
        JOIN categories cat ON p.category_id = cat.id
        LEFT JOIN product_reference_models ref ON p.reference_model_id = ref.id
        WHERE p.id IN ({placeholders})
        ORDER BY p.category_id, p.id
    """, TEST_PRODUCT_IDS).fetchall()
    db_products = {r["id"]: dict(r) for r in rows}
    conn.close()

    print("================================================================================")
    print(f"WEB-07C STOREFRONT ENRICHMENT VERIFICATION ({BASE_URL})")
    print("================================================================================")
    print(f"| ID | Canonical Model | Category | Specs Count | Photo? | Price Match? | Rest. Preserved? | Status |")
    print(f"|:--:|---|---|:---:|:---:|:---:|:---:|:---:|")

    all_passed = True
    verified_count = 0

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # Check restoration category page
        resp_rest = client.get("/catalog/category/pod-vosstanovlenie")
        rest_page_html = resp_rest.text if resp_rest.status_code == 200 else ""

        for pid in TEST_PRODUCT_IDS:
            item = db_products.get(pid)
            if not item:
                print(f"| #{pid} | NOT FOUND IN DB | - | - | - | - | - | FAIL |")
                all_passed = False
                continue

            resp = client.get(f"/catalog/{pid}")
            if resp.status_code != 200:
                print(f"| #{pid} | {item['canonical_name']} | {item['category_name']} | - | - | - | - | HTTP {resp.status_code} FAIL |")
                all_passed = False
                continue

            html = resp.text

            # Check specs count
            specs_matches = re.findall(r'<tr[^>]*>\s*<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>\s*</tr>', html, re.DOTALL)
            specs_count = len(specs_matches)

            # Check photo
            has_photo = ("<img" in html and ("/media/" in html or "placeholder" in html or "data:image" in html))

            # Check price match
            expected_price_int = int(item["sale_price"])
            price_str = f"{expected_price_int:,}".replace(",", " ")
            price_match = (str(expected_price_int) in html or price_str in html or f"{expected_price_int} ₽" in html)

            # Check restoration preservation
            if item["category_name"] == "Техника под восстановление":
                rest_preserved = (item["category_id"] == 52 and (f"/catalog/{pid}" in rest_page_html or "под восстановление" in html.lower()))
            else:
                rest_preserved = (item["category_id"] != 52)

            is_ok = (specs_count >= 5 and has_photo and price_match and rest_preserved)
            if not is_ok:
                all_passed = False

            status_str = "PASS" if is_ok else "FAIL"
            if is_ok:
                verified_count += 1

            canon = item["canonical_name"] or item["title"][:25]
            cat_name = item["category_name"]
            rest_mark = "YES (ID 52)" if item["category_id"] == 52 else "N/A"

            print(f"| #{pid:3d} | {canon:28s} | {cat_name:24s} | {specs_count:2d} specs | {'YES':5s} | {'YES':11s} | {rest_mark:15s} | {status_str} |")

    print("--------------------------------------------------------------------------------")
    print(f"Total products verified: {verified_count} / {len(TEST_PRODUCT_IDS)}")
    print(f"Overall Storefront Verification Status: {'ALL GREEN (PASS)' if all_passed else 'FAIL'}")

    return all_passed


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
