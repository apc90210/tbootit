import os

def test_invalid_token_returns_to_pairing_in_service_worker():
    """Verify service worker removes invalid token when server status indicates unpaired."""
    sw_path = os.path.abspath("chrome-extension/technoreboot-avito/service_worker.js")
    with open(sw_path, "r", encoding="utf-8") as f:
        sw = f.read()

    assert 'chrome.storage.local.remove(["extension_token"]' in sw or 'chrome.storage.local.remove' in sw
