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

@respx.mock
def test_scan_reserved_product_shows_russian_error():
    mock_reserved_product = {
        "id": 102,
        "sku": "BC-102",
        "barcode": "200000000102",
        "title": "Зарезервированный ПК",
        "sale_price": 40000.0,
        "status": "reserved",
        "storage_location": "store",
        "quantity": 1
    }
    respx.get("http://core:8000/api/products/by-barcode/200000000102").mock(
        return_value=Response(200, json=mock_reserved_product)
    )

    response = client.post("/cart/scan", data={"barcode": "200000000102"})
    assert response.status_code == 200
    assert "зарезервирован и недоступен для продажи" in response.text

@respx.mock
def test_scan_sold_product_shows_russian_error():
    mock_sold_product = {
        "id": 103,
        "sku": "BC-103",
        "barcode": "200000000103",
        "title": "Проданный Планшет iPad",
        "sale_price": 15000.0,
        "status": "sold",
        "storage_location": "store",
        "quantity": 0
    }
    respx.get("http://core:8000/api/products/by-barcode/200000000103").mock(
        return_value=Response(200, json=mock_sold_product)
    )

    response = client.post("/cart/scan", data={"barcode": "200000000103"})
    assert response.status_code == 200
    assert "уже продан и недоступен для продажи" in response.text

@respx.mock
def test_scan_draft_product_shows_russian_error():
    mock_draft_product = {
        "id": 104,
        "sku": "BC-104",
        "barcode": "200000000104",
        "title": "Черновик Мышь",
        "sale_price": 500.0,
        "status": "draft",
        "storage_location": "store",
        "quantity": 5
    }
    respx.get("http://core:8000/api/products/by-barcode/200000000104").mock(
        return_value=Response(200, json=mock_draft_product)
    )

    response = client.post("/cart/scan", data={"barcode": "200000000104"})
    assert response.status_code == 200
    assert "ещё не готов к продаже" in response.text

@respx.mock
def test_scan_quantity_zero_product_shows_russian_error():
    mock_zero_qty = {
        "id": 105,
        "sku": "BC-105",
        "barcode": "200000000105",
        "title": "Без остатка Монитор Dell",
        "sale_price": 12000.0,
        "status": "in_stock",
        "storage_location": "store",
        "quantity": 0
    }
    respx.get("http://core:8000/api/products/by-barcode/200000000105").mock(
        return_value=Response(200, json=mock_zero_qty)
    )

    response = client.post("/cart/scan", data={"barcode": "200000000105"})
    assert response.status_code == 200
    assert "отсутствует в остатках" in response.text

@respx.mock
def test_scan_unknown_barcode_shows_russian_error():
    respx.get("http://core:8000/api/products/by-barcode/999999999999").mock(
        return_value=Response(404, json={"detail": "Товар с таким штрихкодом не найден (999999999999)."})
    )

    response = client.post("/cart/scan", data={"barcode": "999999999999"})
    assert response.status_code == 200
    assert "не найден" in response.text
    assert "999999999999" in response.text

@respx.mock
def test_scan_sku_or_id_in_scanner_input_is_blocked():
    # Core API by-barcode returns 404 for SKU or ID
    respx.get("http://core:8000/api/products/by-barcode/SKU-123").mock(
        return_value=Response(404, json={"detail": "Товар с таким штрихкодом не найден (SKU-123)."})
    )

    response = client.post("/cart/scan", data={"barcode": "SKU-123"})
    assert response.status_code == 200
    assert "не найден" in response.text
    assert "SKU-123" in response.text
