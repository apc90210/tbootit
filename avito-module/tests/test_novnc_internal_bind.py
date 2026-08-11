import os
import pytest

def test_novnc_internal_bind_config():
    """Verify internal bind configuration for noVNC websockify (port 6080)."""
    with open("entrypoint.sh", "r", encoding="utf-8") as f:
        content = f.read()
    assert "0.0.0.0:6080" in content
    assert "/usr/share/novnc" in content
    assert "localhost:5900" in content
