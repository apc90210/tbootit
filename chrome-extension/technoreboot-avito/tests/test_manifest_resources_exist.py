import os
import sys

sys.path.insert(0, os.path.abspath("scripts"))
from validate_extension_package import validate_extension_directory

def test_manifest_resources_exist():
    """Verify all resources referenced in manifest.json exist on disk."""
    ext_dir = os.path.abspath("chrome-extension/technoreboot-avito")
    assert validate_extension_directory(ext_dir) is True
