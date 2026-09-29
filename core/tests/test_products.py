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
    # Helper headers
    owner_headers = {"x-auth-is-owner": "1", "x-api-token": "dev-token"}
    non_owner_headers = {"x-auth-is-owner": "0", "x-api-token": "dev-token"}

    # 1. Create a product with in_stock and quantity = 2
    sku = f"TEST002-{uuid.uuid4().hex[:8]}"
    product_data = {
        "sku": sku,
        "title": "Test Prod 2",
        "category_id": 1,
        "status": "in_stock",
        "quantity": 2
    }
    create_response = client.post("/api/products/", json=product_data)
    product_id = create_response.json()["id"]

    # 2. Non-owner cannot publish (403)
    site_data = {
        "is_published_site": 1,
        "site_title": "Cool Prod",
        "site_description": "Great description"
    }
    forbidden_resp = client.patch(f"/api/products/{product_id}/site-publication", json=site_data, headers=non_owner_headers)
    assert forbidden_resp.status_code == 403

    # Without headers at all -> 403
    unauth_resp = client.patch(f"/api/products/{product_id}/site-publication", json=site_data)
    assert unauth_resp.status_code == 403

    # 3. Owner can publish eligible product via PATCH
    site_resp = client.patch(f"/api/products/{product_id}/site-publication", json=site_data, headers=owner_headers)
    assert site_resp.status_code == 200
    assert site_resp.json()["is_published_site"] == 1
    assert site_resp.json()["site_title"] == "Cool Prod"
    assert site_resp.json()["site_description"] == "Great description"

    # Also test PUT method
    put_data = {
        "is_published_site": 1,
        "site_title": "Cool Prod PUT",
        "site_description": "Great description PUT"
    }
    put_resp = client.put(f"/api/products/{product_id}/site-publication", json=put_data, headers=owner_headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["site_title"] == "Cool Prod PUT"

    # 4. Verify audit event was logged
    details = client.get(f"/api/products/{product_id}/details").json()
    events = [e for e in details.get("events", []) if e.get("event_type") == "site_publication"]
    assert len(events) >= 1
    assert "is_published_site=1" in events[0].get("comment", "")

    # 5. Owner can unpublish
    unpub_data = {"is_published_site": 0}
    unpub_resp = client.patch(f"/api/products/{product_id}/site-publication", json=unpub_data, headers=owner_headers)
    assert unpub_resp.status_code == 200
    assert unpub_resp.json()["is_published_site"] == 0

    # 6. Cannot publish when quantity == 0
    sku_zero = f"TEST-ZERO-{uuid.uuid4().hex[:8]}"
    create_zero = client.post("/api/products/", json={
        "sku": sku_zero,
        "title": "Zero Qty Prod",
        "category_id": 1,
        "status": "in_stock",
        "quantity": 0
    })
    pid_zero = create_zero.json()["id"]
    zero_pub_resp = client.patch(f"/api/products/{pid_zero}/site-publication", json={"is_published_site": 1}, headers=owner_headers)
    assert zero_pub_resp.status_code == 400
    assert "количество должно быть больше 0" in zero_pub_resp.json()["detail"]

    # 7. Cannot publish when status is draft / sold / archived
    sku_draft = f"TEST-DRAFT-{uuid.uuid4().hex[:8]}"
    create_draft = client.post("/api/products/", json={
        "sku": sku_draft,
        "title": "Draft Prod",
        "category_id": 1,
        "status": "draft",
        "quantity": 5
    })
    pid_draft = create_draft.json()["id"]
    draft_pub_resp = client.patch(f"/api/products/{pid_draft}/site-publication", json={"is_published_site": 1}, headers=owner_headers)
    assert draft_pub_resp.status_code == 400
    assert "статус должен быть 'in_stock'" in draft_pub_resp.json()["detail"]

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
    
    # valid: in_stock -> draft (sellers can move products to draft)
    status_resp2 = client.post(f"/api/products/{pid}/status", json={"status": "draft"})
    assert status_resp2.status_code == 200
    assert status_resp2.json()["status"] == "draft"

    # valid: draft -> in_stock (restore back from draft)
    status_resp3 = client.post(f"/api/products/{pid}/status", json={"status": "in_stock"})
    assert status_resp3.status_code == 200
    assert status_resp3.json()["status"] == "in_stock"

    # valid: in_stock -> sold
    status_resp4 = client.post(f"/api/products/{pid}/status", json={"status": "sold"})
    assert status_resp4.status_code == 200
    assert status_resp4.json()["status"] == "sold"

    # invalid: sold -> in_stock (sold items can only be archived)
    status_resp5 = client.post(f"/api/products/{pid}/status", json={"status": "in_stock"})
    assert status_resp5.status_code == 400

    # invalid: sold -> draft (sold items cannot be drafted)
    status_resp6 = client.post(f"/api/products/{pid}/status", json={"status": "draft"})
    assert status_resp6.status_code == 400
