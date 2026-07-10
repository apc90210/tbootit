from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_create_sale_warranty_fields():
    sku = f"TEST-WTY-{uuid.uuid4().hex[:8]}"
    payload = {
        "source": "test", "schema_version": "1.0", "operation": "create_or_update",
        "product": {"sku": sku, "title": "Test Wty", "category_path": ["Test"]}
    }
    import_resp = client.post("/api/product-cards/import-json", json=payload)
    pid = import_resp.json()["product_id"]
    
    # Status to in_stock
    client.post(f"/api/products/{pid}/status", json={"status": "in_stock"})
    client.patch(f"/api/products/{pid}", json={"quantity": 10, "storage_location": "store"})

    # Sell it
    sale_data = {
        "total_amount": 1000,
        "payment_method": "cash",
        "warranty_days": 30,
        "warranty_enabled": True,
        "items": [
            {
                "product_id": pid,
                "title": "Test Wty",
                "price": 1000,
                "quantity": 1
            }
        ]
    }
    sale_resp = client.post("/api/sales/", json=sale_data)
    assert sale_resp.status_code == 200
    
    # Check details
    sale_id = sale_resp.json()["id"]
    get_resp = client.get(f"/api/sales/{sale_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["warranty_days"] == 30
    assert data["warranty_enabled"] == True

def test_create_sale_no_warranty():
    sku = f"TEST-NOWTY-{uuid.uuid4().hex[:8]}"
    payload = {
        "source": "test", "schema_version": "1.0", "operation": "create_or_update",
        "product": {"sku": sku, "title": "Test NoWty", "category_path": ["Test"]}
    }
    import_resp = client.post("/api/product-cards/import-json", json=payload)
    pid = import_resp.json()["product_id"]
    
    client.post(f"/api/products/{pid}/status", json={"status": "in_stock"})
    client.patch(f"/api/products/{pid}", json={"quantity": 10, "storage_location": "store"})

    sale_data = {
        "total_amount": 1000,
        "payment_method": "cash",
        "warranty_days": None,
        "warranty_enabled": False,
        "items": [
            {
                "product_id": pid,
                "title": "Test NoWty",
                "price": 1000,
                "quantity": 1
            }
        ]
    }
    sale_resp = client.post("/api/sales/", json=sale_data)
    assert sale_resp.status_code == 200, sale_resp.text
    assert sale_resp.json()["warranty_days"] is None
    assert sale_resp.json()["warranty_enabled"] == False
