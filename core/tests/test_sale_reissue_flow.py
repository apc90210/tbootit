import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_test_product(sku_prefix="REISSUE", qty=5, price=1000.0):
    sku = f"{sku_prefix}-{uuid.uuid4().hex[:8]}"
    resp = client.post("/api/products/", json={
        "sku": sku,
        "title": f"Test Product {sku}",
        "sale_price": price,
        "quantity": qty,
        "storage_location": "store",
        "status": "in_stock"
    })
    assert resp.status_code == 200, resp.text
    return resp.json()

def create_test_sale(product_id, qty=1, price=1000.0):
    resp = client.post("/api/sales/", json={
        "total_amount": price * qty,
        "payment_method": "cash",
        "items": [{"product_id": product_id, "title": "Test Product", "price": price, "quantity": qty}]
    })
    assert resp.status_code == 200, resp.text
    return resp.json()

def test_reissue_canceled_sale():
    prod = create_test_product(qty=10, price=1000.0)
    old_sale = create_test_sale(prod["id"], qty=2, price=1000.0)

    # Cancel old sale first
    cancel_res = client.post(f"/api/sales/{old_sale['id']}/cancel", json={"reason": "Для переоформления"})
    assert cancel_res.status_code == 200

    # Reissue sale
    reissue_res = client.post(f"/api/sales/{old_sale['id']}/reissue", json={
        "reason": "Переоформление с изменением цены",
        "payment_method": "card",
        "items": [{"product_id": prod["id"], "title": "Test Product", "price": 1200.0, "quantity": 2}]
    })
    assert reissue_res.status_code == 200, reissue_res.text
    new_sale = reissue_res.json()

    assert new_sale["status"] == "reissued"
    assert new_sale["total_amount"] == 2400.0
    assert new_sale["payment_method"] == "card"
    assert new_sale["source_sale_id"] == old_sale["id"]

    # Verify old sale status became superseded
    old_sale_updated = client.get(f"/api/sales/{old_sale['id']}").json()
    assert old_sale_updated["status"] == "superseded"
    assert old_sale_updated["superseded_by_sale_id"] == new_sale["id"]

def test_reissue_completed_sale_blocked():
    prod = create_test_product(qty=5)
    sale = create_test_sale(prod["id"], qty=1)

    # Directly reissuing a completed sale without canceling it first should return 400
    res = client.post(f"/api/sales/{sale['id']}/reissue", json={
        "reason": "Прямое переоформление",
        "payment_method": "cash",
        "items": [{"product_id": prod["id"], "title": "Test Product", "price": 1000.0, "quantity": 1}]
    })
    assert res.status_code == 400

def test_second_reissue_blocked():
    prod = create_test_product(qty=10)
    old_sale = create_test_sale(prod["id"], qty=1)

    client.post(f"/api/sales/{old_sale['id']}/cancel", json={"reason": "Отмена"})

    res1 = client.post(f"/api/sales/{old_sale['id']}/reissue", json={
        "reason": "Первое переоформление",
        "payment_method": "cash",
        "items": [{"product_id": prod["id"], "title": "Test Product", "price": 1000.0, "quantity": 1}]
    })
    assert res1.status_code == 200

    # Second reissue attempt on superseded sale should return 409
    res2 = client.post(f"/api/sales/{old_sale['id']}/reissue", json={
        "reason": "Второе переоформление",
        "payment_method": "cash",
        "items": [{"product_id": prod["id"], "title": "Test Product", "price": 1000.0, "quantity": 1}]
    })
    assert res2.status_code == 409

def test_reissue_deducts_stock():
    prod = create_test_product(qty=5)
    old_sale = create_test_sale(prod["id"], qty=2)

    # Cancel old sale -> stock returns to 5
    client.post(f"/api/sales/{old_sale['id']}/cancel", json={"reason": "Отмена"})
    prod_after_cancel = client.get(f"/api/products/{prod['id']}").json()
    assert prod_after_cancel["quantity"] == 5

    # Reissue for 3 items -> stock becomes 2
    client.post(f"/api/sales/{old_sale['id']}/reissue", json={
        "reason": "Переоформление на 3 шт",
        "payment_method": "cash",
        "items": [{"product_id": prod["id"], "title": "Test Product", "price": 1000.0, "quantity": 3}]
    })
    prod_after_reissue = client.get(f"/api/products/{prod['id']}").json()
    assert prod_after_reissue["quantity"] == 2
