from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

@patch("app.routers.products.core_client", new_callable=AsyncMock)
def test_index_route(mock_core_client):
    mock_core_client.health.return_value = {"core_available": True}
    response = client.get("/")
    assert response.status_code == 200
    assert "Техноребут" in response.text
    assert "Доступен" in response.text

@patch("app.routers.products.core_client", new_callable=AsyncMock)
def test_products_route(mock_core_client):
    mock_core_client.get_products.return_value = {
        "items": [{"id": 1, "title": "Test Item", "status": "in_stock", "quantity": 1}],
        "total": 1,
        "limit": 50,
        "offset": 0
    }
    response = client.get("/products")
    assert response.status_code == 200
    assert "Test Item" in response.text

@patch("app.routers.products.core_client", new_callable=AsyncMock)
def test_product_detail_route(mock_core_client):
    mock_core_client.get_product_details.return_value = {
        "id": 1, "title": "Test Item", "status": "in_stock", "quantity": 1
    }
    response = client.get("/products/1")
    assert response.status_code == 200
    assert "Test Item" in response.text


@patch("app.routers.products.core_client", new_callable=AsyncMock)
def test_products_route_has_json_add_shortcut_and_controls(mock_core_client):
    """Stage 07C-R1-R3: Verify '+ Добавить новый товар через JSON' shortcut and quick controls."""
    mock_core_client.get_products.return_value = {
        "items": [{"id": 1, "title": "Test Item", "status": "in_stock", "quantity": 1}],
        "total": 1,
        "limit": 50,
        "offset": 0
    }
    response = client.get("/products")
    assert response.status_code == 200
    html = response.text

    # Shortcut button present and points to /products/json
    assert '+ Добавить новый товар через JSON' in html
    assert 'href="/products/json"' in html
    assert 'id="btn-add-product-json"' in html

    # Existing top quick controls preserved
    assert 'location=all' in html
    assert 'location=store' in html
    assert 'location=workshop' in html
    assert 'location=archive' in html
    assert 'location=draft' in html
    assert 'Все' in html
    assert 'Магазин' in html
    assert 'Мастерская' in html
    assert 'Архив' in html
    assert 'Черновики' in html

