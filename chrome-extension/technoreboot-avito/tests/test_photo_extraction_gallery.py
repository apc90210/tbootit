import os
import pytest

def test_content_js_dom_gallery_extraction_selectors():
    """Verify content.js includes semantic DOM gallery selectors and fallback selectors."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    assert os.path.exists(content_js_path)
    
    with open(content_js_path, "r", encoding="utf-8") as f:
        content_js = f.read()

    assert '[data-marker="image-frame/image-wrapper"] img' in content_js
    assert '[data-marker="gallery/image"] img' in content_js
    assert '[data-marker="slider-image/image"] img' in content_js
