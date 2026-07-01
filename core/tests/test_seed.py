import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_seed_is_idempotent():
    # First seed
    response1 = client.post("/api/admin/seed")
    assert response1.status_code == 200
    
    # Second seed should not crash
    response2 = client.post("/api/admin/seed")
    assert response2.status_code == 200
    
    # Check that categories exist
    stats_response = client.get("/api/admin/stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["products"] >= 5
    assert stats["customers"] >= 3
    assert stats["repairs"] >= 2
