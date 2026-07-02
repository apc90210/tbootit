from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

@patch("app.routers.products.core_client", new_callable=AsyncMock)
def test_product_filters_ui_renders(mock_core_client):
    mock_core_client.get_products.return_value = {
        "items": [],
        "total": 0,
        "limit": 50,
        "offset": 0
    }
    mock_core_client.get_product_filter_options.return_value = {
        "brands": [{"value": "Lenovo", "count": 10}],
        "models": [{"value": "ThinkPad", "count": 10}],
        "statuses": [{"value": "in_stock", "label": "В наличии", "count": 5}]
    }
    
    response = client.get("/products?brand=Lenovo")
    assert response.status_code == 200
    html = response.text
    
    # Check that filter panel renders
    assert "Фильтры" in html
    assert "Lenovo (10)" in html
    assert "ThinkPad (10)" in html
    assert "В наличии (5)" in html
    
    # Check that Russian labels are present
    assert "Сбросить фильтры" in html
    assert "Производитель" in html
    
    # Check that no generic core API error is shown for filter options
    assert "Не удалось загрузить список фильтров" not in html

@patch("app.routers.products.core_client", new_callable=AsyncMock)
def test_product_filters_ui_fallback_on_error(mock_core_client):
    mock_core_client.get_products.return_value = {
        "items": [],
        "total": 0,
        "limit": 50,
        "offset": 0
    }
    mock_core_client.get_product_filter_options.return_value = {
        "error": True,
        "details": "Connection Refused"
    }
    
    response = client.get("/products")
    assert response.status_code == 200
    html = response.text
    
    # Check that the fallback warning is shown
    assert "Не удалось загрузить список фильтров. Поиск и таблица товаров доступны." in html
    # But generic error is not shown
    assert "Ошибка Core API" not in html
