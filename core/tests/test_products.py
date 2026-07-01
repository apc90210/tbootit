from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_products():
    response = client.get("/api/products/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_products_meta():
    response = client.get("/api/products/meta")
    assert response.status_code == 200
    data = response.json()
    assert "product_statuses" in data
    assert "repair_statuses" in data
    assert "brands" in data
    assert "storage_locations" in data

def test_stock_adjustment():
    # Assume product 1 exists via seed or we create one
    product_data = {
        "sku": "TEST001",
        "title": "Test Prod",
        "category_id": 1,
        "quantity": 5
    }
    create_response = client.post("/api/products/", json=product_data)
    assert create_response.status_code == 200
    product_id = create_response.json()["id"]

    # Check details
    details_response = client.get(f"/api/products/{product_id}/details")
    assert details_response.status_code == 200
    assert details_response.json()["quantity"] == 5

    # Adjust stock
    adj_data = {"quantity_delta": -2, "reason": "sale", "comment": "sold 2"}
    adj_response = client.post(f"/api/products/{product_id}/stock-adjustment", json=adj_data)
    assert adj_response.status_code == 200
    assert adj_response.json()["quantity"] == 3

    # Check details again to see movements
    details_response2 = client.get(f"/api/products/{product_id}/details")
    movements = details_response2.json()["stock_movements"]
    assert len(movements) >= 1
    assert movements[0]["quantity_delta"] == -2

def test_publication_flags():
    product_data = {
        "sku": "TEST002",
        "title": "Test Prod 2",
        "category_id": 1
    }
    create_response = client.post("/api/products/", json=product_data)
    product_id = create_response.json()["id"]

    site_data = {
        "is_published_site": 1,
        "site_title": "Cool Prod"
    }
    site_resp = client.patch(f"/api/products/{product_id}/site-publication", json=site_data)
    assert site_resp.status_code == 200
    assert site_resp.json()["is_published_site"] == 1
    assert site_resp.json()["site_title"] == "Cool Prod"
