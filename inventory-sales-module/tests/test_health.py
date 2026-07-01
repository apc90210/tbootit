from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["module"] == "inventory-sales-module"

def test_api_version():
    response = client.get("/api/version")
    assert response.status_code == 200
    assert response.json()["version"] == "1.0.0"
