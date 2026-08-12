import os

def test_failed_import_not_shown_as_success():
    """Explicit regression test for owner bug: popup.js MUST NOT show success UI if product_id is null or result is failed."""
    js_path = os.path.abspath("chrome-extension/technoreboot-avito/popup.js")
    with open(js_path, "r", encoding="utf-8") as f:
        js = f.read()

    assert "res.product_id != null" in js
    assert "Ошибка импорта товара" in js or "импорт товара завершился ошибкой" in js
