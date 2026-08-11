from app.main import app

def test_websocket_proxy_route_exists():
    """Verify route handles novnc websockify WebSocket traffic."""
    routes = [r.path for r in app.routes]
    assert "/avito/novnc/websockify" in routes
