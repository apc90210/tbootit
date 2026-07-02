from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

MOCK_PRODUCT = {"id": 1, "title": "Test Prod", "sale_price": 100, "status": "in_stock", "quantity": 5}

@patch("app.routers.cart.core_client", new_callable=AsyncMock)
def test_cart_add_and_view(mock_core):
    response = client.post("/cart/add", data={"product_id": "1", "title": "Test Prod", "price": "100.0"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Test Prod" in response.text
    
@patch("app.routers.cart.core_client", new_callable=AsyncMock)
def test_cart_checkout(mock_core):
    client.post("/cart/add", data={"product_id": "1", "title": "Test Prod", "price": "100.0"}, follow_redirects=True)
    
    mock_core.create_sale.return_value = {"id": 99}
    
    response = client.post("/cart/checkout", data={
        "payment_method": "cash",
        "notes": "",
        "warranty_enabled": "on",
        "warranty_days": "30"
    }, follow_redirects=False)
    
    assert response.status_code == 303
    assert response.headers["location"] == "/sales/99"
