import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    for fname in ['content.js', 'popup.js', 'service_worker.js']:
        with open(f'chrome-extension/technoreboot-avito/{fname}', 'r', encoding='utf-8') as f:
            code = f.read()
        try:
            page.evaluate("code => new Function(code)", code)
            print(f"OK: {fname} Syntax valid")
        except Exception as e:
            print(f"ERROR: {fname} SYNTAX ERROR: {e}")

    browser.close()
