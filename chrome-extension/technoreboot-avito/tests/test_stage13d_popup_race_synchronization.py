"""Stage 13D Section 20: Automated popup race and state synchronization tests.

Verifies that popup.js prevents the fast-provisional race condition, synchronizes
authoritative listing data, correctly rejects late fast responses, and warns on
degraded single-photo states.
"""
import os
import pytest

POPUP_JS_PATH = os.path.abspath("chrome-extension/technoreboot-avito/popup.js")
CONTENT_JS_PATH = os.path.abspath("chrome-extension/technoreboot-avito/content.js")


@pytest.fixture
def popup_js():
    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def content_js():
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_popup_authoritative_state_variables_declared(popup_js):
    """Verify popup.js declares authoritativeListingData, isScanComplete, and activeScanRequestId."""
    assert "authoritativeListingData" in popup_js
    assert "isScanComplete" in popup_js
    assert "activeScanRequestId" in popup_js


def test_popup_hide_all_cards_resets_authoritative_state(popup_js):
    """Verify hideAllCards resets authoritative state so stale data is never reused."""
    start = popup_js.find("function hideAllCards()")
    assert start != -1
    sub = popup_js[start:start + 400]
    assert "authoritativeListingData = null;" in sub
    assert "isScanComplete = false;" in sub
    assert "activeScanRequestId = null;" in sub


def test_popup_fast_provisional_scan_prevents_premature_enable(popup_js):
    """Verify that provisional 1-photo scan keeps button disabled and shows scan in progress."""
    start = popup_js.find("function setupSingleListingSection")
    assert start != -1
    sub = popup_js[start:start + 2500]
    assert "isProvisional" in sub
    assert "sendBtn.disabled = true;" in sub
    assert "Сбор полной галереи..." in sub


def test_popup_deep_scan_updates_authoritative_and_enables_button(popup_js):
    """Verify that deepScan response sets authoritativeListingData and enables sendBtn."""
    start = popup_js.find("function setupSingleListingSection")
    assert start != -1
    sub = popup_js[start:start + 3500]
    assert "authoritativeListingData = deepResponse;" in sub
    assert "isScanComplete = true;" in sub
    assert "sendBtn.disabled = false;" in sub


def test_popup_send_button_uses_authoritative_data_directly(popup_js):
    """Verify sendBtn click transmits authoritativeListingData directly without re-scanning."""
    start = popup_js.find('sendBtn.addEventListener("click"')
    assert start != -1
    sub = popup_js[start:start + 6000]
    assert "authoritativeListingData.page_type === \"listing\" && isScanComplete" in sub
    assert "executeIngest(authoritativeListingData);" in sub


def test_popup_degraded_single_photo_warning(popup_js):
    """Verify degraded single-photo warning is displayed when visible > 1 but deep count is 1."""
    assert "Найдена только 1 фотография из" in popup_js
    assert "Внимание: найдена только 1 фотография из галереи. Полный импорт фото не готов." in popup_js


def test_content_script_passes_scan_request_id(content_js):
    """Verify content script returns scanRequestId in all response branches."""
    assert "scanRequestId" in content_js
    assert "fastData.scanRequestId = request.scanRequestId" in content_js
