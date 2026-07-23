import respx
from httpx import Response
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cart_scanner_input_field_exists():
    response = client.get("/cart")
    assert response.status_code == 200
    assert "Сканировать штрихкод" in response.text
    assert 'id="scanner-input"' in response.text
    assert "autofocus" in response.text

@respx.mock
def test_scan_valid_barcode_adds_product_to_cart():
    # Mock Core API get_product_by_barcode
    mock_product = {
        "id": 101,
        "sku": "BC-101",
        "barcode": "200000000101",
        "title": "Сканерный Ноутбук Lenovo",
        "sale_price": 25000.0,
        "price": 25000.0,
        "status": "in_stock",
        "storage_location": "store",
        "quantity": 3
    }
    respx.get("http://core:8000/api/products/by-barcode/200000000101").mock(
        return_value=Response(200, json=mock_product)
    )

    response = client.post("/cart/scan", data={"barcode": "200000000101"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Сканерный Ноутбук Lenovo" in response.text
    assert "25000" in response.text

from unittest.mock import patch, AsyncMock

@respx.mock
def test_scan_unknown_barcode_shows_russian_error():
    respx.get("http://core:8000/api/products/by-barcode/999999999999").mock(
        return_value=Response(404, json={"detail": "Товар со штрихкодом '999999999999' не найден"})
    )
    respx.get(path="/api/products/").mock(
        return_value=Response(200, json={"items": [], "total": 0})
    )

    response = client.post("/cart/scan", data={"barcode": "999999999999"})
    assert response.status_code == 200
    assert "Товар со штрихкодом" in response.text
    assert "999999999999" in response.text
    assert "не найден" in response.text

@respx.mock
def test_scan_sold_product_shows_russian_error():
    mock_sold_product = {
        "id": 102,
        "sku": "BC-102",
        "barcode": "200000000102",
        "title": "Проданный Планшет iPad",
        "sale_price": 15000.0,
        "status": "sold",
        "storage_location": "store",
        "quantity": 0
    }
    respx.get("http://core:8000/api/products/by-barcode/200000000102").mock(
        return_value=Response(200, json=mock_sold_product)
    )

    response = client.post("/cart/scan", data={"barcode": "200000000102"})
    assert response.status_code == 200
    assert "Проданный Планшет iPad" in response.text
    assert "недоступен для продажи" in response.text

@respx.mock
def test_scan_quantity_zero_product_shows_russian_error():
    mock_zero_qty_product = {
        "id": 103,
        "sku": "BC-103",
        "barcode": "200000000103",
        "title": "Без остатка Монитор Dell",
        "sale_price": 12000.0,
        "status": "in_stock",
        "storage_location": "store",
        "quantity": 0
    }
    respx.get("http://core:8000/api/products/by-barcode/200000000103").mock(
        return_value=Response(200, json=mock_zero_qty_product)
    )

    response = client.post("/cart/scan", data={"barcode": "200000000103"})
    assert response.status_code == 200
    assert "недоступен для продажи" in response.text
