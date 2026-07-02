from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock
import pytest

client = TestClient(app)

@pytest.mark.asyncio
async def test_cascading_ui_selects_rendered():
    # Mock core_client.health
    mock_health = AsyncMock()
    mock_health.return_value = {"core_available": True}
    
    # Mock core_client.get_products
    mock_get_products = AsyncMock()
    mock_get_products.return_value = {"items": [], "total": 0}
    
    # Mock core_client.get_product_filter_options
    mock_get_filter_options = AsyncMock()
    mock_get_filter_options.return_value = {
        "categories": [{"id": 1, "name": "Cat1", "count": 10}],
        "brands": [{"value": "Brand1", "count": 5}],
        "models": [{"value": "Model1", "count": 2}],
        "statuses": [{"value": "in_stock", "label": "В наличии", "count": 2}],
        "storage_locations": [{"value": "A1", "count": 2}],
        "avito_ready": [{"value": "true", "label": "Готово к Авито", "count": 1}],
        "site_ready": [{"value": "false", "label": "Не готово к сайту", "count": 1}],
        "selected": {"category_id": 1},
        "order": ["categories", "brands", "models", "statuses", "storage_locations", "avito_ready", "site_ready"]
    }
    
    with patch("app.routers.products.core_client.health", mock_health), \
         patch("app.routers.products.core_client.get_products", mock_get_products), \
         patch("app.routers.products.core_client.get_product_filter_options", mock_get_filter_options):
         
         response = client.get("/products?category_id=1")
         assert response.status_code == 200
         html = response.text
         
         # Check if cascading handlers are in the HTML
         assert 'onchange="cascadeReset(1)"' in html
         assert 'onchange="cascadeReset(2)"' in html
         assert 'onchange="cascadeReset(3)"' in html
         assert 'onchange="cascadeReset(4)"' in html
         assert 'onchange="cascadeReset(5)"' in html
         assert 'onchange="cascadeReset(6)"' in html
         
         # Check if JavaScript is present
         assert 'function cascadeReset(level)' in html
         assert "form.elements['brand'].value = '';" in html
