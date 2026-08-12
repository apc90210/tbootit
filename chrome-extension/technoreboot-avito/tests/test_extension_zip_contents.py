import os
import sys
import zipfile

sys.path.insert(0, os.path.abspath("scripts"))
from build_extension_zip import build_zip

def test_extension_zip_contents_structure():
    """Verify built ZIP places manifest.json and icons directly at root without excessive folder nesting."""
    zip_path = build_zip()
    assert os.path.exists(zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        assert "manifest.json" in names
        assert "icons/icon16.png" in names
        assert "icons/icon32.png" in names
        assert "icons/icon48.png" in names
        assert "icons/icon128.png" in names
        assert "service_worker.js" in names
        assert "content.js" in names
        assert "popup.html" in names
