from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_details_endpoint_schema():
    """Verify /health/details contains all component keys."""
    res = client.get("/health/details")
    assert res.status_code == 200
    data = res.json()
    assert "module" in data
    assert "browser_runtime" in data
    assert "xvfb" in data
    assert "vnc" in data
    assert "novnc" in data
    assert "chromium" in data
    assert "profile_storage" in data
