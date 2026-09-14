import os
import time
from playwright.sync_api import sync_playwright

CERT_PATH = os.path.abspath('data/auth/certificates/owner.crt')
KEY_PATH = os.path.abspath('data/auth/certificates/owner.key')
ASSETS_DIR = os.path.abspath('docs/user_manual/assets')

os.makedirs(ASSETS_DIR, exist_ok=True)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            ignore_https_errors=True,
            viewport={'width': 1280, 'height': 800},
            device_scale_factor=1.5,
            client_certificates=[{
                'origin': 'https://localhost:8443',
                'certPath': CERT_PATH,
                'keyPath': KEY_PATH
            }]
        )
        page = context.new_page()

        print("Capturing 01_dashboard.png...")
        page.goto('https://localhost:8443/', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '01_dashboard.png'))

        print("Capturing 02_products_list.png...")
        page.goto('https://localhost:8443/inventory/products', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '02_products_list.png'))

        print("Capturing 03_product_add.png...")
        page.goto('https://localhost:8443/inventory/products/new', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '03_product_add.png'))

        print("Capturing 04_product_detail.png...")
        page.goto('https://localhost:8443/inventory/products/1', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '04_product_detail.png'))

        print("Capturing 05_avito_extension.png...")
        page.goto('https://localhost:8443/avito/extension', wait_until='networkidle')
        try:
            page.click('#genCodeBtn')
            page.wait_for_timeout(500)
        except Exception as e:
            print("Notice:", e)
        page.screenshot(path=os.path.join(ASSETS_DIR, '05_avito_extension.png'))

        print("Capturing 06_avito_popup.png...")
        popup_path = os.path.abspath('chrome-extension/technoreboot-avito/popup.html')
        page.goto(f'file:///{popup_path.replace(chr(92), "/")}', wait_until='load')
        page.set_viewport_size({'width': 450, 'height': 580})
        page.screenshot(path=os.path.join(ASSETS_DIR, '06_avito_popup.png'))

        # Reset viewport
        page.set_viewport_size({'width': 1280, 'height': 800})

        print("Capturing 07_cart.png...")
        page.goto('https://localhost:8443/inventory/cart', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '07_cart.png'))

        print("Capturing 08_sales_new.png...")
        page.goto('https://localhost:8443/inventory/sales/new?product_id=1', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '08_sales_new.png'))

        print("Capturing 09_sales_list.png...")
        page.goto('https://localhost:8443/inventory/sales', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '09_sales_list.png'))

        print("Capturing 10_sales_detail.png...")
        page.goto('https://localhost:8443/inventory/sales/1', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '10_sales_detail.png'))

        print("Capturing 11_repair_new.png...")
        page.goto('https://localhost:8443/repairs/repairs/new', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '11_repair_new.png'))

        # Fill in a demonstration repair to have realistic detail and list
        try:
            page.fill('input[name="customer_name"]', 'Иванов Алексей Петрович')
            page.fill('input[name="customer_phone"]', '+7 912 345-67-89')
            page.fill('input[name="brand"]', 'Lenovo')
            page.fill('input[name="model"]', 'ThinkPad T480')
            page.fill('input[name="serial_number"]', 'PF-1ABCD8')
            page.fill('textarea[name="reported_issue"]', 'Не работает клавиатура после залития водой, требуется замена и диагностика материнской платы')
            page.fill('input[name="completeness"]', 'Ноутбук, оригинальное зарядное устройство 65W')
            page.fill('input[name="appearance"]', 'Следы нормальной эксплуатации, мелкие потертости на крышке')
            page.click('button[type="submit"]')
            page.wait_for_timeout(1000)
            print("Demonstration repair created successfully.")
            
            # Now we are on the repair detail page
            print("Capturing 12_repair_detail.png...")
            page.screenshot(path=os.path.join(ASSETS_DIR, '12_repair_detail.png'))
        except Exception as e:
            print("Notice on repair creation:", e)
            page.goto('https://localhost:8443/repairs/repairs', wait_until='networkidle')

        print("Capturing 13_repairs_list.png...")
        page.goto('https://localhost:8443/repairs/repairs', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '13_repairs_list.png'))

        print("Capturing 14_reports_sales.png...")
        page.goto('https://localhost:8443/inventory/reports/sales', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '14_reports_sales.png'))

        print("Capturing 15_owner_operations.png...")
        page.goto('https://localhost:8443/system/operations', wait_until='networkidle')
        page.screenshot(path=os.path.join(ASSETS_DIR, '15_owner_operations.png'))

        browser.close()
        print("All screenshots successfully captured in docs/user_manual/assets/")

if __name__ == '__main__':
    main()
