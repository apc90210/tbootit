from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_health_endpoint_schema():
    """Verify /avito/health proxy route exists and returns status dictionary."""
    response = client.get("/avito/health")
    assert response.status_code == 200
    data = response.json()
    assert "browser_runtime" in data
    assert "module" in data
