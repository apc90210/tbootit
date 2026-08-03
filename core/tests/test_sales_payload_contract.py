import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_test_product():
    sku = f"SALE-FLOW-{uuid.uuid4().hex[:8]}"
    response = client.post("/api/products/", json={
        "sku": sku,
        "title": "Contract Test Product",
        "sale_price": 1500.0,
        "status": "in_stock",
        "quantity": 10,
        "storage_location": "store"
    })
    assert response.status_code == 200
    return response.json()["id"]

def test_sale_create_without_total_amount_success():
    pid = create_test_product()
    payload = {
        "customer_id": None,
        "payment_method": "sbp",
        "comment": "Test SBP sale without total_amount",
        "warranty_days": 30,
        "warranty_enabled": True,
        "items": [
            {
                "product_id": pid,
                "title": "Contract Test Product",
                "price": 1500.0,
                "quantity": 2
            }
        ]
    }
    response = client.post("/api/sales/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_amount"] == 3000.0
    assert data["payment_method"] == "sbp"
    assert data["status"] == "completed"

def test_sale_create_recalculates_server_total():
    pid = create_test_product()
    # Client sends total_amount = 9999.0, Core should override/calculate 1500.0
    payload = {
        "total_amount": 9999.0,
        "payment_method": "cash",
        "items": [
            {
                "product_id": pid,
                "title": "Contract Test Product",
                "price": 1500.0,
                "quantity": 1
            }
        ]
    }
    response = client.post("/api/sales/", json=payload)
    assert response.status_code == 200
    assert response.json()["total_amount"] == 1500.0

def test_sale_create_empty_items_rejected():
    payload = {
        "payment_method": "cash",
        "items": []
    }
    response = client.post("/api/sales/", json=payload)
    assert response.status_code == 400

def test_sale_create_invalid_quantity_or_price_rejected():
    pid = create_test_product()
    payload_bad_qty = {
        "payment_method": "cash",
        "items": [{"product_id": pid, "title": "Test", "price": 100.0, "quantity": 0}]
    }
    res1 = client.post("/api/sales/", json=payload_bad_qty)
    assert res1.status_code in [400, 422]

    payload_bad_price = {
        "payment_method": "cash",
        "items": [{"product_id": pid, "title": "Test", "price": -50.0, "quantity": 1}]
    }
    res2 = client.post("/api/sales/", json=payload_bad_price)
    assert res2.status_code in [400, 422]

def test_sale_create_no_warranty_supported():
    pid = create_test_product()
    payload = {
        "payment_method": "card",
        "warranty_enabled": False,
        "warranty_days": 0,
        "items": [{"product_id": pid, "title": "Contract Test Product", "price": 1500.0, "quantity": 1}]
    }
    response = client.post("/api/sales/", json=payload)
    assert response.status_code == 200
    assert response.json()["warranty_enabled"] is False
