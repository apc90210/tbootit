from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_get_products():
    response = client.get("/api/products/")
    assert response.status_code == 200
    assert "items" in response.json()
    assert isinstance(response.json()["items"], list)

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

def test_patch_product_safe_fields():
    # create a product
    sku = f"TEST-PATCH-{uuid.uuid4().hex[:8]}"
    payload = {
        "source": "test", "schema_version": "1.0", "operation": "create_or_update",
        "product": {"sku": sku, "title": "Old Title", "category_path": ["Test"]}
    }
    import_resp = client.post("/api/product-cards/import-json", json=payload)
    pid = import_resp.json()["product_id"]
    
    # patch
    patch_resp = client.patch(f"/api/products/{pid}", json={"title": "New Title", "sale_price": 5000})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "New Title"
    assert patch_resp.json()["sale_price"] == 5000

def test_patch_product_reject_unsafe():
    # create a product
    sku = f"TEST-REJECT-{uuid.uuid4().hex[:8]}"
    payload = {
        "source": "test", "schema_version": "1.0", "operation": "create_or_update",
        "product": {"sku": sku, "title": "Test Title", "category_path": ["Test"]}
    }
    import_resp = client.post("/api/product-cards/import-json", json=payload)
    pid = import_resp.json()["product_id"]
    
    # negative price
    patch_resp = client.patch(f"/api/products/{pid}", json={"sale_price": -100})
    assert patch_resp.status_code == 400
    
    # empty title
    patch_resp2 = client.patch(f"/api/products/{pid}", json={"title": "   "})
    assert patch_resp2.status_code == 400
    
    # attempt to patch status
    patch_resp3 = client.patch(f"/api/products/{pid}", json={"status": "in_stock"})
    assert patch_resp3.status_code == 400

def test_post_status_valid_invalid():
    sku = f"TEST-STATUS-{uuid.uuid4().hex[:8]}"
    payload = {
        "source": "test", "schema_version": "1.0", "operation": "create_or_update",
        "product": {"sku": sku, "title": "Status Title", "category_path": ["Test"]}
    }
    import_resp = client.post("/api/product-cards/import-json", json=payload)
    pid = import_resp.json()["product_id"]
    
    # valid: imported/draft -> in_stock
    status_resp = client.post(f"/api/products/{pid}/status", json={"status": "in_stock"})
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "in_stock"
    
    # invalid: in_stock -> draft
    status_resp2 = client.post(f"/api/products/{pid}/status", json={"status": "draft"})
    assert status_resp2.status_code == 400
    
    # valid: in_stock -> sold
    status_resp3 = client.post(f"/api/products/{pid}/status", json={"status": "sold"})
    assert status_resp3.status_code == 200
    assert status_resp3.json()["status"] == "sold"
