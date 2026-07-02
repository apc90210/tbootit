import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_product_filter_options():
    # we don't need fixtures since the DB is managed by the app in these tests
    response = client.get("/api/products/filter-options")
    assert response.status_code == 200
    data = response.json()
    
    assert "brands" in data
    assert "models" in data
    assert "statuses" in data
    assert "categories" in data
    assert "storage_locations" in data
    assert "avito_ready" in data
    assert "site_ready" in data
    
    # Check that counts are numeric
    for brand in data["brands"]:
        assert "value" in brand
        assert "count" in brand
        assert isinstance(brand["count"], int)
        
    for model in data["models"]:
        assert "value" in model
        assert "count" in model
        assert isinstance(model["count"], int)
        
    for status in data["statuses"]:
        assert "value" in status
        assert "label" in status
        assert "count" in status
        assert isinstance(status["count"], int)
        
    for cat in data["categories"]:
        assert "id" in cat
        assert "name" in cat
        assert "count" in cat
        assert isinstance(cat["count"], int)
