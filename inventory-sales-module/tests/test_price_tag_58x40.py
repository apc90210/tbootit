import respx
from httpx import Response
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@respx.mock
def test_price_tag_58x40_route_returns_200_and_css():
    mock_product = {
        "id": 201,
        "sku": "TAG-58-201",
        "barcode": "200000000201",
        "title": "Тестовый Видеокарта RTX 3070",
        "sale_price": 35000.0,
        "price": 35000.0,
        "condition": "Б/У",
        "status": "in_stock"
    }
    respx.get("http://core:8000/api/products/201/details").mock(
        return_value=Response(200, json=mock_product)
    )

    response = client.get("/products/201/price-tag/58x40")
    assert response.status_code == 200
    assert "58mm 40mm" in response.text
    assert "Тестовый Видеокарта RTX 3070" in response.text
    assert "35 000 ₽" in response.text
    assert "Гарантия 30 дней" in response.text
    assert "window.print()" in response.text
    assert "window.close()" in response.text
    assert "Предварительная форма ценника" in response.text

@respx.mock
def test_manual_print_price_overrides_preview_without_mutating_core():
    mock_product = {
        "id": 202,
        "sku": "TAG-58-202",
        "barcode": "200000000202",
        "title": "Материнская плата B450",
        "sale_price": 8000.0,
        "price": 8000.0,
        "condition": "Б/У",
        "status": "in_stock"
    }
    # Mock Core API product details
    details_route = respx.get("http://core:8000/api/products/202/details").mock(
        return_value=Response(200, json=mock_product)
    )
    # Ensure no PATCH or PUT to Core API happens
    patch_route = respx.patch("http://core:8000/api/products/202").mock(
        return_value=Response(500, json={"error": "Core product.price should not be mutated!"})
    )

    # User requests price tag preview with manual print price = 7500
    response = client.get("/products/202/price-tag/58x40?print_price=7500")
    assert response.status_code == 200
    assert "7 500 ₽" in response.text
    
    # Assert PATCH request to Core API was NEVER called
    assert not patch_route.called
    assert details_route.called
