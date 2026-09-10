import os
import pytest

def test_novnc_internal_bind_config():
    """Verify internal bind configuration for noVNC websockify (port 6080)."""
    entrypoint_path = "entrypoint.sh" if os.path.exists("entrypoint.sh") else os.path.join(os.path.dirname(__file__), "..", "entrypoint.sh")
    with open(entrypoint_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "0.0.0.0:6080" in content
    assert "/usr/share/novnc" in content
    assert "localhost:5900" in content
