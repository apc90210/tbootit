"""Tests for sales routes in inventory-sales-module."""
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

MOCK_PRODUCT_SELLABLE = {
    "id": 1,
    "title": "Ноутбук HP",
    "sku": "HP-001",
    "status": "in_stock",
    "sale_price": 25000.0,
    "price": 25000.0,
    "quantity": 1,
    "brand": "HP",
    "model": "ProBook",
    "storage_location": "A1",
}

MOCK_PRODUCT_SOLD = {
    "id": 2,
    "title": "Монитор Dell",
    "sku": "DELL-002",
    "status": "sold",
    "sale_price": 10000.0,
    "price": 10000.0,
    "quantity": 0,
    "brand": "Dell",
    "model": "U2419",
    "storage_location": "B2",
}

MOCK_SALE = {
    "id": 1,
    "customer_id": None,
    "total_amount": 25000.0,
    "payment_method": "cash",
    "comment": None,
    "status": "completed",
    "created_at": "2026-07-02T10:00:00",
    "cancelled_at": None,
    "cancel_reason": None,
}

MOCK_SALES_LIST = {
    "items": [MOCK_SALE],
    "total": 1,
    "limit": 50,
    "offset": 0,
}


@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_sales_list_returns_page(mock_core):
    mock_core.get_sales.return_value = MOCK_SALES_LIST
    response = client.get("/sales")
    assert response.status_code == 200
    assert "Продажи" in response.text
    assert "#1" in response.text


@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_sales_list_empty(mock_core):
    mock_core.get_sales.return_value = {"items": [], "total": 0, "limit": 50, "offset": 0}
    response = client.get("/sales")
    assert response.status_code == 200
    assert "Продаж пока нет" in response.text


@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_sales_new_renders_form_for_sellable(mock_core):
    mock_core.get_product_details.return_value = MOCK_PRODUCT_SELLABLE
    response = client.get("/sales/new?product_id=1")
    assert response.status_code == 200
    assert "Новая продажа" in response.text
    assert "Подтвердить продажу" in response.text
    assert "Ноутбук HP" in response.text


@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_sales_new_rejects_sold_product(mock_core):
    mock_core.get_product_details.return_value = MOCK_PRODUCT_SOLD
    response = client.get("/sales/new?product_id=2")
    assert response.status_code == 200
    assert "Товар нельзя продать в текущем статусе" in response.text
    assert "Подтвердить продажу" not in response.text


@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_sales_create_calls_core_and_redirects(mock_core):
    mock_core.get_product.return_value = MOCK_PRODUCT_SELLABLE
    mock_core.create_sale.return_value = MOCK_SALE
    response = client.post(
        "/sales/create",
        data={
            "product_id": "1",
            "price": "25000",
            "payment_method": "cash",
            "notes": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/sales/1" in response.headers["location"]
    mock_core.create_sale.assert_called_once()


@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_sales_create_shows_error_on_core_failure(mock_core):
    mock_core.get_product.return_value = MOCK_PRODUCT_SELLABLE
    mock_core.create_sale.return_value = {
        "error": True,
        "status_code": 400,
        "detail": "Cannot sell product 1 in status 'sold'",
    }
    response = client.post(
        "/sales/create",
        data={
            "product_id": "1",
            "price": "25000",
            "payment_method": "cash",
            "notes": "",
        },
    )
    assert response.status_code == 200
    assert "Товар нельзя продать в текущем статусе" in response.text


@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_sale_detail_renders(mock_core):
    mock_core.get_sale.return_value = MOCK_SALE
    response = client.get("/sales/1")
    assert response.status_code == 200
    assert "Продажа оформлена" in response.text
    assert "25000" in response.text


@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_sale_detail_not_found(mock_core):
    mock_core.get_sale.return_value = {"error": "Not Found", "status_code": 404}
    response = client.get("/sales/999")
    assert response.status_code == 200
    assert "Продажа не найдена" in response.text
