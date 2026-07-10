from fastapi.testclient import TestClient
from app.main import app

import uuid

client = TestClient(app)

def test_sale_cancel_and_reissue():
    # 1. create product
    sku = f"SALE-REISSUE-{uuid.uuid4().hex[:8]}"
    resp = client.post("/api/products/", json={"sku": sku, "title": "P", "sale_price": 100, "quantity": 10, "storage_location": "store", "status": "in_stock"})
    pid = resp.json()["id"]
    
    # 2. create sale
    resp = client.post("/api/sales/", json={
        "total_amount": 100,
        "payment_method": "cash",
        "items": [{"product_id": pid, "title": "P", "price": 100, "quantity": 2}]
    })
    assert resp.status_code == 200, resp.text
    sale_id = resp.json()["id"]
    
    # 3. check quantity
    prod = client.get(f"/api/products/{pid}").json()
    assert prod["quantity"] == 8
    
    # 4. reissue sale
    resp = client.post(f"/api/sales/{sale_id}/reissue", json={
        "reason": "Wrong item",
        "payment_method": "card",
        "items": [{"product_id": pid, "title": "P", "price": 100, "quantity": 1}]
    })
    assert resp.status_code == 200, resp.text
    new_sale_id = resp.json()["id"]
    assert resp.json()["original_sale_id"] == sale_id
    
    # 5. check old sale
    old_sale = client.get(f"/api/sales/{sale_id}").json()
    assert old_sale["status"] == "superseded"
    assert old_sale["replaced_by_sale_id"] == new_sale_id
    
    # 6. check quantity again (10 - 2 + 2 - 1 = 9)
    prod = client.get(f"/api/products/{pid}").json()
    assert prod["quantity"] == 9
