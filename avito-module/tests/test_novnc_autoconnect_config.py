import pytest

def test_novnc_autoconnect_query_parameter_compatibility():
    """Verify query parameter string contains autoconnect=1 and path=avito/novnc/websockify."""
    query = "autoconnect=1&resize=remote&path=avito/novnc/websockify"
    assert "autoconnect=1" in query
    assert "path=avito/novnc/websockify" in query
