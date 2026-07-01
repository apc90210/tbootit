from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_admin_schema():
    response = client.get("/api/admin/db/schema")
    assert response.status_code == 200
    assert "products" in response.json()
