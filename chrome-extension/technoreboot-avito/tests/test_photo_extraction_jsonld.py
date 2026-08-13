import os
import pytest

def test_content_js_jsonld_photo_parsing_patterns():
    """Verify content.js contains JS parser logic for string, array, object, and @graph JSON-LD image structures."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    assert os.path.exists(content_js_path)
    
    with open(content_js_path, "r", encoding="utf-8") as f:
        content_js = f.read()

    assert "parseJsonLdImages" in content_js
    assert "@graph" in content_js
    assert "contentUrl" in content_js
    assert "item.url" in content_js
    assert "position:" in content_js
