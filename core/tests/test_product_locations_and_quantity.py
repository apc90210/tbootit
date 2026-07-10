from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app import models
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # No teardown here since we use a shared test DB across tests or rely on rollback

def test_create_product_default_location():
    response = client.post("/api/products/", json={
        "sku": "LOC-01",
        "title": "Loc Product",
        "sale_price": 100,
        "quantity": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert data["storage_location"] == "store"
    assert data["quantity"] == 5

def test_update_product_location():
    response = client.post("/api/products/", json={"sku": "LOC-02", "title": "P2", "sale_price": 100, "quantity": 5})
    pid = response.json()["id"]
    
    response = client.patch(f"/api/products/{pid}", json={"storage_location": "workshop"})
    assert response.status_code == 200
    assert response.json()["storage_location"] == "workshop"
