import sqlite3
import httpx
import json
import sys
import re

# Set stdout to UTF-8
sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = r"C:\tbootit\data\db\technoreboot.db"
BASE_URL = "http://127.0.0.1:8090"

def run_verification():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Query products with category and reference info (only publicly visible on web)
    c.execute("""
        SELECT p.id, p.title, p.site_title, p.brand, p.model, p.sale_price, p.category_id,
               cat.name as category_name, cat.slug as category_slug, p.reference_model_id,
               ref.canonical_name, ref.device_type, p.avito_params_json
        FROM products p
        JOIN categories cat ON p.category_id = cat.id
        LEFT JOIN product_reference_models ref ON p.reference_model_id = ref.id
        WHERE p.is_published_site = 1 AND p.status = 'in_stock' AND p.quantity > 0
        ORDER BY p.id
    """)
    all_products = [dict(r) for r in c.fetchall()]
    conn.close()

    printers_mfp = [p for p in all_products if p["category_name"] in ("Принтеры", "МФУ") and p["reference_model_id"] and p["reference_model_id"] > 27][:10]
    monitors = [p for p in all_products if p["category_name"] == "Мониторы" and p["reference_model_id"] and p["reference_model_id"] > 27][:5]
    laptops_pc = [p for p in all_products if p["category_name"] in ("Ноутбуки", "Компьютеры") and p["reference_model_id"] and p["reference_model_id"] > 27][:5]
    restoration = [p for p in all_products if p["category_name"] == "Техника под восстановление" and p["reference_model_id"]][:5]

    target_groups = [
        ("Newly Linked Printers & MFP (10 items)", printers_mfp),
        ("Newly Linked Monitors (5 items)", monitors),
        ("Newly Linked Laptops & PC (5 items)", laptops_pc),
        ("Restoration Products (Preservation Check, 5 items)", restoration),
    ]

    print(f"================================================================================")
    print(f"WEB-07B STOREFRONT VERIFICATION ({BASE_URL}/catalog/...)")
    print(f"================================================================================")

    all_passed = True
    total_checked = 0

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # Check restoration category page once
        resp_rest = client.get("/catalog/category/pod-vosstanovlenie")
        rest_page_html = resp_rest.text if resp_rest.status_code == 200 else ""

        for group_name, items in target_groups:
            print(f"\n### {group_name}")
            print(f"| ID | Title (Storefront) | Category | Brand | Model | Specs? | Photo? | Price | Restoration Preserved? |")
            print(f"|---|---|---|---|---|:---:|:---:|---:|:---:|")

            for item in items:
                pid = item["id"]
                resp = client.get(f"/catalog/{pid}")
                total_checked += 1
                if resp.status_code != 200:
                    print(f"| #{pid} | FAILED HTTP {resp.status_code} | - | - | - | - | - | - | NO |")
                    all_passed = False
                    continue

                html = resp.text
                
                # Check title
                title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
                web_title = title_match.group(1).strip() if title_match else (item["site_title"] or item["title"])
                
                # Check category preservation
                cat_name = item["category_name"]
                
                # Check brand and model
                brand = item["brand"] or ""
                model = item["model"] or ""
                brand_present = brand.lower() in html.lower() if brand else True
                model_present = model.lower() in html.lower() if model else True
                
                # Check specs
                has_specs = ("Характеристики" in html or "class=\"spec" in html or "specs" in html or "product-specs-table" in html)
                
                # Check photo
                has_photo = ("<img" in html and ("/media/" in html or "placeholder" in html or "data:image" in html))
                
                # Check price
                has_price = ("₽" in html or "руб" in html.lower())
                
                # Check restoration category preservation
                if item["category_name"] == "Техника под восстановление":
                    rest_preserved = (f"/catalog/{pid}" in rest_page_html and item["category_id"] == 52)
                else:
                    rest_preserved = "N/A"

                spec_mark = "YES" if has_specs else "NO"
                photo_mark = "YES" if has_photo else "NO"
                price_mark = f"{item['sale_price']:.0f} ₽" if item['sale_price'] else "YES"
                rest_mark = "YES" if rest_preserved == "N/A" or rest_preserved else "FAIL"

                disp_title = (web_title[:32] + "...") if len(web_title) > 32 else web_title
                print(f"| #{pid} | {disp_title} | {cat_name} | {brand} | {model} | {spec_mark} | {photo_mark} | {price_mark} | {rest_mark} |")

                if not (brand_present and model_present and has_specs and has_photo and has_price and (rest_preserved == "N/A" or rest_preserved)):
                    all_passed = False

    print(f"\n================================================================================")
    print(f"Verification Summary: Total Checked = {total_checked}, Status = {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    print(f"================================================================================")
    return all_passed

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
