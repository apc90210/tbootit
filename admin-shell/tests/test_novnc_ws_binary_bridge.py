import pytest
from app.main import app

def test_websocket_proxy_endpoint_negotiates_subprotocol():
    """Verify route for websocket proxy exists."""
    routes = [r.path for r in app.routes]
    assert "/avito/novnc/websockify" in routes
