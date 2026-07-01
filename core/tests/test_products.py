from fastapi.testclient import TestClient
from app.main import app
import uuid

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
    # Use JSON import to reliably create a product with a unique SKU
    sku = f"TEST001-ADJ-{uuid.uuid4().hex[:8]}"
    payload = {
        "source": "test", "schema_version": "1.0", "operation": "create_or_update",
        "product": {"sku": sku, "title": "Test Prod", "category_path": ["Test"], "quantity": 5}
    }
    import_resp = client.post("/api/product-cards/import-json", json=payload)
    assert import_resp.status_code == 200
    product_id = import_resp.json()["product_id"]

    # Check initial quantity
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
    # Movements are ordered desc; most recent (-2) should be first
    assert movements[0]["quantity_delta"] == -2

def test_publication_flags():
    sku = f"TEST002-{uuid.uuid4().hex[:8]}"
    product_data = {
        "sku": sku,
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
