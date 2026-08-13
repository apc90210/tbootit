import os
import json
import pytest

def test_extension_manifest_v3_validity():
    """Verify extension manifest.json is valid Manifest V3 with minimal safe permissions."""
    manifest_path = os.path.abspath("chrome-extension/technoreboot-avito/manifest.json")
    assert os.path.exists(manifest_path)
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["manifest_version"] == 3
    assert data["name"].startswith("Техноребут Avito")
    assert "version" in data
    
    permissions = data.get("permissions", [])
    # Verify NO forbidden permissions
    assert "cookies" not in permissions
    assert "debugger" not in permissions
    assert "proxy" not in permissions
    assert "nativeMessaging" not in permissions

def test_extension_files_exist():
    """Verify all extension core files exist."""
    base_dir = os.path.abspath("chrome-extension/technoreboot-avito")
    for fname in ["service_worker.js", "content.js", "popup.html", "popup.js", "popup.css", "README.md"]:
        assert os.path.exists(os.path.join(base_dir, fname))
