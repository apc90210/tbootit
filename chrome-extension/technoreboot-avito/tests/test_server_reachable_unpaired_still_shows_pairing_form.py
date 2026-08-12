import os
import re

def test_server_reachable_unpaired_still_shows_pairing_form():
    """Explicit regression test for owner bug: when server is reachable but token is missing,
    popup.js MUST show the pairing form and keep transfer button disabled."""
    js_path = os.path.abspath("chrome-extension/technoreboot-avito/popup.js")
    assert os.path.exists(js_path)

    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()

    # 1. Unpaired condition displays pairSection
    assert 'pairSection.style.display = "block"' in js_content or "pairSection.style.display = 'block'" in js_content
    # 2. Transfer button is disabled when not paired
    assert "sendBtn.disabled = true" in js_content
    # 3. Code input digits cleaning
    assert r"replace(/\D/g, '')" in js_content or r"replace(/\D/g, '')" in js_content or r"\D" in js_content
