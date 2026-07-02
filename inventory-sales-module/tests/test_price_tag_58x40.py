from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@patch("app.routers.products.core_client", new_callable=AsyncMock)
def test_price_tag_page(mock_core):
    mock_core.get_product_details.return_value = {"id": 1, "sku": "SKU123", "title": "Test", "sale_price": 500, "status": "in_stock"}
    response = client.get("/products/1/price-tag")
    assert response.status_code == 200
    assert "SKU123" in response.text
    assert "58mm" in response.text
    assert "40mm" in response.text
    assert "500" in response.text
