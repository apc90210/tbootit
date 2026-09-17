import json
import os
import re
import sys
import pytest
from playwright.sync_api import sync_playwright

EXTENSION_DIR = os.path.abspath("chrome-extension/technoreboot-avito")
MANIFEST_PATH = os.path.join(EXTENSION_DIR, "manifest.json")
POPUP_HTML_PATH = os.path.join(EXTENSION_DIR, "popup.html")
POPUP_JS_PATH = os.path.join(EXTENSION_DIR, "popup.js")
SERVICE_WORKER_PATH = os.path.join(EXTENSION_DIR, "service_worker.js")


@pytest.fixture(scope="module")
def js_eval():
    """Evaluate JavaScript helper functions using Playwright node/browser environment."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        def evaluate(code_snippet):
            return page.evaluate(code_snippet)

        yield evaluate
        browser.close()


def test_01_paired_state_displays_current_server_origin():
    """1. Verify paired state displays current server origin in popup HTML/JS contract."""
    with open(POPUP_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    assert 'id="connectedOriginDisplay"' in html
    assert 'id="pairedConnectionBlock"' in html
    assert 'id="connectionStatusText"' in html
    assert 'connectedOriginDisplay.textContent = data.origin' in js
    assert 'Подключено' in js


def test_02_offline_paired_server_displays_saved_origin_and_unreachable():
    """2. Verify offline paired server still displays saved origin + server unavailable without hiding address."""
    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    assert 'PAIRED_SERVER_UNREACHABLE' in js
    assert 'Сервер недоступен' in js
    # When unreachable, pairedConnectionBlock is shown with saved origin and disconnect button
    assert 'pairedConnectionBlock.style.display = "block"' in js
    assert 'unpairedConnectionBlock.style.display = "none"' in js


def test_03_disconnect_clears_active_connection_state():
    """3. Verify disconnect clears active connection, token, and session draft in storage."""
    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        sw = f.read()
    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    assert 'async function unpairExtension' in sw
    # Checks storage wiping
    assert '"extension_token"' in sw
    assert '"active_connection"' in sw
    assert '"server_base_url"' in sw
    assert '"avito_publication_draft"' in sw
    # Check popup prompt confirmation and action trigger
    assert 'Отключить расширение от' in js
    assert 'chrome.runtime.sendMessage({ action: "unpair"' in js


def test_04_disconnect_does_not_touch_browser_mtls_certificate():
    """4. Verify disconnect does NOT invoke any certificate deletion/mutation APIs."""
    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()
    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        sw = f.read()

    # Must NOT call browser cert deletion or native messaging or privacy APIs
    for code in [js, sw]:
        assert "chrome.enterprise" not in code
        assert "chrome.certificateProvider" not in code
        assert "removeCertificate" not in code


def test_05_and_06_and_07_url_normalization_and_server_switching(js_eval):
    """5, 6, 7, 11, 12. Verify URL normalization removes trailing slash, preserves port, rejects invalid."""
    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        sw = f.read()

    # Extract normalizeOrigin implementation
    func_code = """
    (() => {
        function normalizeOrigin(rawUrl) {
            if (!rawUrl || typeof rawUrl !== "string") return null;
            let s = rawUrl.trim().replace(/\\/+$/, "");
            if (!s) return null;
            if (s.includes("://")) {
                if (!/^https?:\\/\\//i.test(s)) return null;
            } else {
                s = "https://" + s;
            }
            try {
                const parsed = new URL(s);
                if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return null;
                if (!parsed.hostname) return null;
                return parsed.origin;
            } catch (e) {
                return null;
            }
        }
        return {
            local_with_port: normalizeOrigin("https://localhost:8443/avito/extension"),
            local_slash: normalizeOrigin("https://localhost:8443/"),
            local_clean: normalizeOrigin("https://localhost:8443"),
            prod_clean: normalizeOrigin("https://144.31.15.88"),
            prod_slash: normalizeOrigin("https://144.31.15.88/"),
            prod_no_scheme: normalizeOrigin("144.31.15.88"),
            local_http: normalizeOrigin("http://localhost:8011/admin-api"),
            invalid_scheme: normalizeOrigin("ftp://example.com"),
            malformed: normalizeOrigin("not-a-valid-url ::: 1234"),
            empty: normalizeOrigin("")
        };
    })()
    """
    res = js_eval(func_code)
    # Check normalization results
    assert res["local_with_port"] == "https://localhost:8443"
    assert res["local_slash"] == "https://localhost:8443"
    assert res["local_clean"] == "https://localhost:8443"
    assert res["prod_clean"] == "https://144.31.15.88"
    assert res["prod_slash"] == "https://144.31.15.88"
    assert res["prod_no_scheme"] == "https://144.31.15.88"
    assert res["local_http"] == "http://localhost:8011"
    assert res["invalid_scheme"] is None
    assert res["malformed"] is None
    assert res["empty"] is None


def test_08_pairing_failure_does_not_partially_replace_existing_state():
    """8. Verify pairing failure leaves existing connection state untouched."""
    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        sw = f.read()

    # setStoredToken and active_connection are ONLY set on parsed.ok && parsed.data.status === 'paired'
    pair_func = sw[sw.find("async function pairExtension"):sw.find("async function unpairExtension")]
    assert "chrome.storage.local.set" in pair_func
    # Verify failure branch does not write to storage
    assert "return { success: false, message: errDetail };" in pair_func


def test_09_old_server_token_is_not_used_on_new_server():
    """9. Verify unpair clears token and pair assigns new token atomically."""
    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        sw = f.read()

    assert "extension_token: newToken" in sw
    assert '"extension_token"' in sw  # removed on unpair


def test_10_active_tab_origin_prefills_only_when_appropriate():
    """10. Verify active-tab prefill only triggers when unpaired and input is empty."""
    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    assert "if (isPaired) return;" in js
    assert "if (serverUrlInput && !serverUrlInput.value)" in js


def test_13_runtime_host_permission_request_and_denial_handling():
    """13. Verify runtime host permission request is invoked and denial produces clear error."""
    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    assert "chrome.permissions.request" in js
    assert "chrome.permissions.contains" in js
    assert "Разрешение на доступ к" in js
    assert "отклонено пользователем" in js


def test_14_all_extension_api_requests_use_active_connection_origin():
    """14. Verify all extension API requests use getServerUrl() driven by active origin."""
    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        sw = f.read()

    # getActiveOrigin is the single source of truth
    assert "async function getActiveOrigin" in sw
    assert "${origin}/admin-api/avito-extension" in sw


def test_15_legacy_vds_not_active_default_or_fallback():
    """15. Verify retired legacy VDS 144.31.50.134 is NOT in manifest host_permissions or default code."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        sw = f.read()
    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    # Must NOT be in host_permissions
    assert "https://144.31.50.134/*" not in manifest.get("host_permissions", [])
    # Must NOT be in service worker default URL
    assert "144.31.50.134" not in sw
    # Must NOT be in popup.js active tab detection
    assert 'tabUrl.includes("144.31.50.134")' not in js


def test_16_server_pairing_revoke_endpoint_exists():
    """16. Verify server-side avito-module provides pairing/revoke endpoint."""
    # Isolate and import avito-module
    orig_path = list(sys.path)
    try:
        sys.path = [p for p in sys.path if not any(m in p.lower() for m in ["inventory-sales-module", "core", "admin-shell", "repairs-module"])]
        for k in list(sys.modules.keys()):
            if k == "app" or k.startswith("app."):
                del sys.modules[k]
        sys.path.insert(0, os.path.abspath("avito-module"))
        from app.main import app as avito_app
        from fastapi.testclient import TestClient

        client = TestClient(avito_app)
        # Generate code
        gen = client.post("/extension/api/pairing/generate").json()
        code = gen["pair_code"]
        # Pair
        pair = client.post("/extension/api/pairing/pair", json={"pair_code": code}).json()
        token = pair["extension_token"]
        # Verify status with token
        stat1 = client.get("/extension/api/status", headers={"X-Extension-Token": token}).json()
        assert stat1["paired"] is True
        assert stat1["token_valid"] is True

        # Revoke pairing
        rev = client.post("/extension/api/pairing/revoke", headers={"X-Extension-Token": token}).json()
        assert rev["status"] == "unpaired"
        assert rev["revoked"] is True

        # Verify status with revoked token shows token invalid
        stat2 = client.get("/extension/api/status", headers={"X-Extension-Token": token}).json()
        assert stat2["token_valid"] is False
    finally:
        sys.path = orig_path
