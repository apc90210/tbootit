import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_update_sale_price_none_preserves_existing():
    """Verify that sending sale_price=None does not trigger 422 float_type and preserves existing price."""
    # Create product with initial sale_price
    create_payload = {
        "title": "Товар для проверки сохранения цены",
        "sale_price": 25000.0,
        "purchase_price": 15000.0,
        "quantity": 1
    }
    resp = client.post("/api/products/", json=create_payload)
    assert resp.status_code == 200
    prod_id = resp.json()["id"]

    # Update description and send sale_price=None
    update_payload = {
        "title": "Товар для проверки сохранения цены (обновлено)",
        "description": "Обновленное описание товара",
        "sale_price": None,
        "quantity": 1
    }
    up_resp = client.put(f"/api/products/{prod_id}", json=update_payload)
    assert up_resp.status_code == 200, f"Expected 200, got {up_resp.status_code}: {up_resp.text}"
    updated = up_resp.json()
    assert updated["sale_price"] == 25000.0, "Existing sale_price should be preserved when None is passed"
    assert updated["title"] == "Товар для проверки сохранения цены (обновлено)"

def test_full_update_sale_price_updates_integer_and_decimal():
    """Verify integer and decimal price updates."""
    create_payload = {
        "title": "Товар для теста цен",
        "sale_price": 10000.0,
        "quantity": 1
    }
    resp = client.post("/api/products/", json=create_payload)
    assert resp.status_code == 200
    prod_id = resp.json()["id"]

    # Update to integer price
    up1 = client.put(f"/api/products/{prod_id}", json={"title": "Товар", "sale_price": 12000.0, "quantity": 1})
    assert up1.status_code == 200
    assert up1.json()["sale_price"] == 12000.0

    # Update to decimal price
    up2 = client.put(f"/api/products/{prod_id}", json={"title": "Товар", "sale_price": 12450.50, "quantity": 1})
    assert up2.status_code == 200
    assert up2.json()["sale_price"] == 12450.50

def test_product_details_includes_price_alias():
    """Verify GET /api/products/{id}/details contains 'price' alias matching 'sale_price'."""
    create_payload = {
        "title": "Товар с алиасом цены",
        "sale_price": 33000.0,
        "quantity": 1
    }
    resp = client.post("/api/products/", json=create_payload)
    assert resp.status_code == 200
    prod_id = resp.json()["id"]

    det_resp = client.get(f"/api/products/{prod_id}/details")
    assert det_resp.status_code == 200
    det = det_resp.json()
    assert det["sale_price"] == 33000.0
    assert det.get("price") == 33000.0
