from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@patch("app.routers.products.core_client", new_callable=AsyncMock)
def test_price_tag_print_action_preview(mock_core):
    mock_core.get_product_details.return_value = {
        "id": 1, "sku": "SKU-PRINT-123", "title": "Принтер HP", "sale_price": 7500.0, "status": "in_stock"
    }
    response = client.get("/products/1/price-tag")
    assert response.status_code == 200
    assert "SKU-PRINT-123" in response.text
    assert "Принтер HP" in response.text
    assert "Печать ценника" in response.text
    assert "Предварительная форма ценника" in response.text

def test_products_list_has_price_tag_button():
    mock_products = {
        "items": [
            {"id": 1, "sku": "SKU-1", "title": "Товар 1", "status": "in_stock", "quantity": 1, "storage_location": "store", "price": 1000},
            {"id": 2, "sku": "SKU-2", "title": "Товар 2", "status": "sold", "quantity": 0, "storage_location": "store", "price": 2000}
        ],
        "total": 2, "limit": 50, "offset": 0
    }
    with patch("app.routers.products.core_client.get_products", new_callable=AsyncMock) as mock_get_prods, \
         patch("app.routers.products.core_client.get_product_filter_options", new_callable=AsyncMock) as mock_get_opts:
        mock_get_prods.return_value = mock_products
        mock_get_opts.return_value = {}
        response = client.get("/products")
        assert response.status_code == 200
        assert "Печать ценника" in response.text
