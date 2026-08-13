import os
import pytest

def test_content_js_srcset_quality_parsing():
    """Verify content.js contains srcset parsing helper to select highest quality resolution."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    assert os.path.exists(content_js_path)
    
    with open(content_js_path, "r", encoding="utf-8") as f:
        content_js = f.read()

    assert "extractBestUrlFromSrcset" in content_js
    assert "data-srcset" in content_js
    assert "srcset" in content_js
