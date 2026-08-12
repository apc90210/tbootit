import os

def test_popup_pairing_states_contract():
    """Verify popup.html contains all required elements for pairing state machine."""
    html_path = os.path.abspath("chrome-extension/technoreboot-avito/popup.html")
    assert os.path.exists(html_path)

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="connBadge"' in html
    assert 'id="statusMsg"' in html
    assert 'id="pairSection"' in html
    assert 'id="pairCodeInput"' in html
    assert 'id="pairBtn"' in html
    assert 'inputmode="numeric"' in html
    assert 'maxlength="6"' in html
    assert 'id="sendBtn"' in html
