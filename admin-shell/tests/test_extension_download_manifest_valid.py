import os
import sys
import zipfile
import tempfile
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("scripts"))
from validate_extension_package import validate_extension_directory
from app.main import app

client = TestClient(app)

def test_extension_download_manifest_valid():
    """Verify downloaded ZIP file contains a valid manifest and all referenced resources."""
    res = client.get("/avito/extension/download")
    assert res.status_code == 200
    
    tmp_zip = tempfile.mktemp(suffix=".zip")
    with open(tmp_zip, "wb") as f:
        f.write(res.content)

    tmp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(tmp_zip, "r") as zf:
        zf.extractall(tmp_dir)

    assert validate_extension_directory(tmp_dir) is True
