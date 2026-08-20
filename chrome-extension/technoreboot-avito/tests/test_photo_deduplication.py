import os
import pytest

def test_content_js_photo_deduplication_and_order():
    """Verify content.js contains deduplication logic and order/position assignment."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    assert os.path.exists(content_js_path)
    
    with open(content_js_path, "r", encoding="utf-8") as f:
        content_js = f.read()

    assert "seenCanonicalKeys.has(key)" in content_js
    assert "uniquePhotos.push" in content_js
    assert "position: uniquePhotos.length" in content_js
