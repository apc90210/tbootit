from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

def test_product_detail_with_avito_characteristics():
    """Verify that a product with Avito category & characteristics renders table cleanly."""
    mock_product = {
        "id": 58,
        "title": "Лазерный цветной принтер hp m252n на запчасти",
        "sale_price": 3500.0,
        "status": "draft",
        "storage_location": "store",
        "quantity": 1,
        "description": "Тестовое описание",
        "photos": [],
        "avito_category_name": "Принтеры",
        "avito_characteristics": {
            "Состояние": "Б/у",
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Цветная"
        }
    }
    with patch("app.routers.products.core_client.get_product_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        res = client.get("/products/58")
        assert res.status_code == 200
        assert "Характеристики Avito" in res.text
        assert "Принтеры" in res.text
        assert "Технология печати" in res.text
        assert "Лазерная" in res.text
        assert "Цветность печати" in res.text
        assert "Цветная" in res.text

def test_product_detail_without_avito_characteristics():
    """Verify that a product without Avito characteristics renders fallback text."""
    mock_product = {
        "id": 99,
        "title": "Обычный товар",
        "sale_price": 1000.0,
        "status": "in_stock",
        "storage_location": "store",
        "quantity": 1,
        "description": "Описание",
        "photos": [],
        "avito_category_name": None,
        "avito_characteristics": {}
    }
    with patch("app.routers.products.core_client.get_product_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        res = client.get("/products/99")
        assert res.status_code == 200
        assert "Характеристики Avito" in res.text
        assert "Характеристики Avito не импортированы" in res.text
