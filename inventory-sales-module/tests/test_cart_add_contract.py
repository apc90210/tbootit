import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("app.routers.cart.core_client.get_product", new_callable=AsyncMock)
def test_add_to_cart_without_price_uses_core_price(mock_get_product):
    mock_get_product.return_value = {
        "id": 46,
        "title": "Fetched Core Product",
        "price": 1200.0,
        "status": "in_stock",
        "storage_location": "store",
        "quantity": 5
    }
    
    response = client.post(
        "/cart/add",
        data={"product_id": "46"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "Fetched Core Product" in response.text
    assert "1 200" in response.text or "1200" in response.text

@patch("app.routers.cart.core_client.get_product", new_callable=AsyncMock)
def test_add_to_cart_reserved_product_blocked(mock_get_product):
    mock_get_product.return_value = {
        "id": 47,
        "title": "Reserved Item",
        "price": 500.0,
        "status": "reserved",
        "storage_location": "store",
        "quantity": 1
    }
    
    response = client.post(
        "/cart/add",
        data={"product_id": "47"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "зарезервирован" in response.text
