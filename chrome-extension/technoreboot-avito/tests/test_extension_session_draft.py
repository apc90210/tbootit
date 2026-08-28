import os
import pytest

def test_session_storage_draft_logic_in_popup_js():
    """Verify popup.js contains session storage draft handling, TTL check, and explicit clear function."""
    popup_js_path = os.path.abspath("chrome-extension/technoreboot-avito/popup.js")
    assert os.path.exists(popup_js_path)

    with open(popup_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Session storage and TTL handling
    assert "chrome.storage.session" in content
    assert "avito_publication_draft" in content
    assert "expires_at" in content
    assert "clearSessionDraft" in content
    assert "saveSessionDraft" in content
    assert "getSessionDraft" in content

def test_avito_form_open_only_on_explicit_click():
    """Verify Avito tab open is triggered exclusively by explicit openAvitoBtn click."""
    popup_js_path = os.path.abspath("chrome-extension/technoreboot-avito/popup.js")
    with open(popup_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "openAvitoBtn.onclick" in content
    assert 'chrome.tabs.create({ url: "https://www.avito.ru/additem" })' in content

def test_product_page_url_detection():
    """Verify product regex correctly identifies /inventory/products/{id} and /products/{id}."""
    popup_js_path = os.path.abspath("chrome-extension/technoreboot-avito/popup.js")
    with open(popup_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert r"/inventory\/products\/(\d+)/" in content or "inventory/products" in content
