from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_dashboard_has_health_gating_script():
    """Verify avito.html template contains health checking script."""
    response = client.get("/avito")
    assert response.status_code == 200
    assert "checkHealth()" in response.text
    assert "h-browser" in response.text
