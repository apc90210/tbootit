import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("app.routers.cart.core_client.create_sale", new_callable=AsyncMock)
def test_cart_checkout_sbp_and_warranty(mock_create_sale):
    mock_create_sale.return_value = {"id": 101, "total_amount": 2500.0, "status": "completed"}
    
    # 1. Add item to cart session
    client.post("/cart/add", data={"product_id": "1", "title": "Item 1", "price": "2500.0"})
    
    # 2. Checkout SBP
    response = client.post(
        "/cart/checkout",
        data={
            "payment_method": "sbp",
            "warranty_enabled": "on",
            "warranty_days": "30",
            "notes": "Fast checkout SBP"
        },
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/sales/101"
    
    # Verify core_client payload
    called_payload = mock_create_sale.call_args[0][0]
    assert called_payload["payment_method"] == "sbp"
    assert called_payload["warranty_enabled"] is True
    assert called_payload["warranty_days"] == 30
    assert called_payload["total_amount"] == 2500.0
