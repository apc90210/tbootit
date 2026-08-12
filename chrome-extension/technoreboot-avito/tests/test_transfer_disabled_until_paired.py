import os

def test_transfer_disabled_until_paired_in_popup_js():
    """Verify popup.js keeps sendBtn disabled until isPaired is true."""
    js_path = os.path.abspath("chrome-extension/technoreboot-avito/popup.js")
    with open(js_path, "r", encoding="utf-8") as f:
        js = f.read()

    assert "if (!isPaired)" in js
    assert "sendBtn.disabled = true" in js
    assert "Передача станет доступна после привязки" in js
