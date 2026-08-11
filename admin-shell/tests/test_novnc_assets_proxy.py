from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_novnc_static_proxy_route_exists():
    """Verify route handles static novnc assets."""
    routes = [r.path for r in app.routes]
    assert "/avito/novnc/{path:path}" in routes
