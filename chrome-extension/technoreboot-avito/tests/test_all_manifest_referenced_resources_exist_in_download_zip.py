import os
import sys

sys.path.insert(0, os.path.abspath("scripts"))
from build_extension_zip import build_zip
from validate_extension_package import validate_extension_zip

def test_all_manifest_referenced_resources_exist_in_download_zip():
    """Explicit regression test for reported bug: fails if manifest references icons/icon16.png but missing in zip."""
    zip_path = build_zip()
    assert validate_extension_zip(zip_path) is True
