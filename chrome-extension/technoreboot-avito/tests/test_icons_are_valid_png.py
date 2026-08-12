import os

def test_icons_are_valid_png():
    """Verify icon files in extension directory exist and are valid PNG images."""
    icons_dir = os.path.abspath("chrome-extension/technoreboot-avito/icons")
    for name in ["icon16.png", "icon32.png", "icon48.png", "icon128.png"]:
        p = os.path.join(icons_dir, name)
        assert os.path.exists(p)
        assert os.path.getsize(p) > 0
        with open(p, "rb") as f:
            header = f.read(8)
            assert header == b"\x89PNG\r\n\x1a\n"
