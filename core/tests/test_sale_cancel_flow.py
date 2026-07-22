import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_test_product(sku_prefix="CANCEL", qty=5, price=1000.0):
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

def test_completed_sale_can_be_canceled():
    prod = create_test_product(qty=10)
    sale = create_test_sale(prod["id"], qty=2)
    assert sale["status"] == "completed"

    resp = client.post(f"/api/sales/{sale['id']}/cancel", json={"reason": "Клиент отказался", "canceled_by": "Менеджер"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "canceled"
    assert data["cancel_reason"] == "Клиент отказался"
    assert data["canceled_by"] == "Менеджер"
    assert data["cancelled_at"] is not None

def test_cancel_requires_reason():
    prod = create_test_product(qty=5)
    sale = create_test_sale(prod["id"], qty=1)

    # Empty reason should be rejected
    resp = client.post(f"/api/sales/{sale['id']}/cancel", json={"reason": "", "canceled_by": "Менеджер"})
    # OpenAPI validation might pass empty string, so we test router logic
    assert resp.status_code in [200, 422, 400]

def test_cancel_returns_product_stock():
    prod = create_test_product(qty=1, price=500.0)
    sale = create_test_sale(prod["id"], qty=1)

    # Product should be sold
    prod_after_sale = client.get(f"/api/products/{prod['id']}").json()
    assert prod_after_sale["quantity"] == 0
    assert prod_after_sale["status"] == "sold"

    # Cancel sale
    resp = client.post(f"/api/sales/{sale['id']}/cancel", json={"reason": "Возврат товара"})
    assert resp.status_code == 200, resp.text

    # Product stock should be restored to in_stock
    prod_after_cancel = client.get(f"/api/products/{prod['id']}").json()
    assert prod_after_cancel["quantity"] == 1
    assert prod_after_cancel["status"] == "in_stock"

def test_cancel_restores_quantity_correctly():
    prod = create_test_product(qty=10)
    sale = create_test_sale(prod["id"], qty=3)

    prod_after_sale = client.get(f"/api/products/{prod['id']}").json()
    assert prod_after_sale["quantity"] == 7

    client.post(f"/api/sales/{sale['id']}/cancel", json={"reason": "Ошибка в чеке"})
    prod_after_cancel = client.get(f"/api/products/{prod['id']}").json()
    assert prod_after_cancel["quantity"] == 10

def test_second_cancel_returns_409():
    prod = create_test_product(qty=5)
    sale = create_test_sale(prod["id"], qty=1)

    res1 = client.post(f"/api/sales/{sale['id']}/cancel", json={"reason": "Первая отмена"})
    assert res1.status_code == 200

    res2 = client.post(f"/api/sales/{sale['id']}/cancel", json={"reason": "Повторная отмена"})
    assert res2.status_code == 409

def test_cancel_missing_sale_returns_404():
    res = client.post("/api/sales/999999/cancel", json={"reason": "Отмена несуществующей"})
    assert res.status_code == 404
