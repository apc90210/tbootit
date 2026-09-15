import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

SAMPLE_AVITO_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>iPhone 13 128GB в отличном состоянии купить в Москве на Avito</title>
</head>
<body>
    <div data-marker="item-view/title-info">
        <h1 data-marker="item-view/title-info" class="title-info-title-text">iPhone 13 128GB в отличном состоянии</h1>
    </div>
    <div data-marker="item-view/item-price">
        <span itemprop="price" content="45000">45 000 ₽</span>
    </div>
    <div data-marker="item-view/item-description">
        <p>Продам iPhone 13 в идеальном состоянии. Полный комплект, коробка, провод. Аккумулятор 90%.</p>
    </div>
    <div data-marker="item-view/item-params">
        <ul>
            <li><span>Память: </span><span>128 ГБ</span></li>
            <li><span>Цвет: </span><span>Синий</span></li>
            <li><span>Состояние: </span><span>Отличное</span></li>
        </ul>
    </div>
    <div class="gallery-img-frame">
        <img src="https://80.img.avito.st/image/1/1234567890.jpg" alt="фото 1">
        <img src="https://80.img.avito.st/image/1/0987654321.jpg" alt="фото 2">
    </div>
    <span data-item-id="7353766377">Объявление № 7353766377</span>
</body>
</html>
"""

def test_content_script_extraction():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://www.avito.ru/moskva/telefony/iphone_13_128gb_7353766377")
        page.set_content(SAMPLE_AVITO_HTML)

        # Mock chrome runtime for content script testing
        page.evaluate("""
            let messageListener = null;
            window.chrome = {
                runtime: {
                    onMessage: {
                        addListener: function(fn) {
                            messageListener = fn;
                        }
                    },
                    sendMessage: function() {}
                }
            };
            window.sendMessageToContent = function(msg) {
                return new Promise(resolve => {
                    if (messageListener) {
                        messageListener(msg, {}, resolve);
                    } else {
                        resolve(null);
                    }
                });
            };
        """)

        # Inject content.js
        with open("chrome-extension/technoreboot-avito/content.js", "r", encoding="utf-8") as f:
            content_code = f.read()

        page.evaluate(content_code)

        # Trigger extract_current_page message
        res = page.evaluate("() => window.sendMessageToContent({ action: 'extract_current_page', deepScan: false })")
        print("Extraction response:")
        import json
        print(json.dumps(res, ensure_ascii=False, indent=2))

        assert res is not None, "Extraction response is None!"
        assert res.get("page_type") == "listing", f"Expected listing, got {res.get('page_type')}"
        listing = res.get("listing", {})
        assert "iPhone 13" in listing.get("title", ""), f"Title mismatch: {listing.get('title')}"
        print("\nPASS: extract_current_page works perfectly on individual Avito listing!")
        browser.close()

if __name__ == "__main__":
    test_content_script_extraction()
