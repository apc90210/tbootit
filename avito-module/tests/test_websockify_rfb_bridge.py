import os
import pytest

def test_entrypoint_websockify_bridge_config():
    """Verify entrypoint.sh configures websockify --web /usr/share/novnc 0.0.0.0:6080 localhost:5900."""
    entrypoint_path = "entrypoint.sh" if os.path.exists("entrypoint.sh") else os.path.join(os.path.dirname(__file__), "..", "entrypoint.sh")
    with open(entrypoint_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "websockify" in content
    assert "0.0.0.0:6080" in content
    assert "localhost:5900" in content
