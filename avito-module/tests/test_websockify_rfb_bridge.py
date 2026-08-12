import pytest

def test_entrypoint_websockify_bridge_config():
    """Verify entrypoint.sh configures websockify --web /usr/share/novnc 0.0.0.0:6080 localhost:5900."""
    with open("entrypoint.sh", "r", encoding="utf-8") as f:
        content = f.read()
    assert "websockify" in content
    assert "0.0.0.0:6080" in content
    assert "localhost:5900" in content
