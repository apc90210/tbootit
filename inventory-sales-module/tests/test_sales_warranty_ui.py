from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

def test_sales_new_form_get():
    mock_product = {
        "id": 5,
        "sku": "PROD-55",
        "title": "Ноутбук ASUS",
        "sale_price": 25000.0,
        "price": 25000.0,
        "quantity": 3,
        "status": "in_stock",
        "storage_location": "store"
    }
    with patch("app.core_client.core_client.get_product", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        response = client.get("/sales/new?product_id=5")
        assert response.status_code == 200
        assert "Ноутбук ASUS" in response.text
        assert "Цена продажи" in response.text
        assert "Количество" in response.text
        assert "Без гарантии" in response.text
        assert "30" in response.text

def test_sales_create_with_warranty():
    mock_product = {
        "id": 5,
        "sku": "PROD-55",
        "title": "Ноутбук ASUS",
        "sale_price": 25000.0,
        "quantity": 3,
        "status": "in_stock"
    }

    form_data = {
        "product_id": "5",
        "price": "24000.0",
        "quantity": "1",
        "payment_method": "cash",
        "warranty_days": "30",
        "notes": "Продажа со скидкой"
    }

    with patch("app.core_client.core_client.get_product", new_callable=AsyncMock) as mock_get, \
         patch("app.core_client.core_client.create_sale", new_callable=AsyncMock) as mock_create:
        mock_get.return_value = mock_product
        mock_create.return_value = {"id": 101, "status": "completed"}

        response = client.post("/sales/create", data=form_data, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/sales/101"

        mock_create.assert_called_once()
        payload = mock_create.call_args[0][0]
        assert payload["warranty_days"] == 30
        assert payload["warranty_enabled"] == True

def test_sales_create_no_warranty():
    mock_product = {
        "id": 5,
        "sku": "PROD-55",
        "title": "Ноутбук ASUS",
        "sale_price": 25000.0,
        "quantity": 3,
        "status": "in_stock"
    }

    form_data = {
        "product_id": "5",
        "price": "25000.0",
        "quantity": "1",
        "payment_method": "card",
        "no_warranty": "true",
        "notes": "Без гарантии по договоренности"
    }

    with patch("app.core_client.core_client.get_product", new_callable=AsyncMock) as mock_get, \
         patch("app.core_client.core_client.create_sale", new_callable=AsyncMock) as mock_create:
        mock_get.return_value = mock_product
        mock_create.return_value = {"id": 102, "status": "completed"}

        response = client.post("/sales/create", data=form_data, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/sales/102"

        mock_create.assert_called_once()
        payload = mock_create.call_args[0][0]
        assert payload["warranty_days"] is None
        assert payload["warranty_enabled"] == False
