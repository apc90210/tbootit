"""Tests for Russian UI localization in sales flow."""
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

MOCK_PRODUCT = {
    "id": 1,
    "title": "Ноутбук",
    "sku": "NB-01",
    "status": "in_stock",
    "price": 50000.0,
    "quantity": 1,
}

MOCK_SALE_ERROR = {
    "error": True,
    "status_code": 400,
    "detail": "Cannot sell product",
}

@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_russian_ui_sales_new(mock_core):
    mock_core.get_product_details.return_value = MOCK_PRODUCT
    response = client.get("/sales/new?product_id=1")
    assert response.status_code == 200
    
    text = response.text
    # Required Russian terms
    assert "Новая продажа" in text
    assert "Подтвердить продажу" in text
    assert "Цена продажи" in text
    assert "Способ оплаты" in text
    assert "Наличные" in text
    assert "Карта" in text
    assert "Перевод" in text
    assert "Смешанная оплата" in text
    assert "Другое" in text
    
    # Should not contain English fallbacks for UI
    assert ">Submit<" not in text
    assert ">Sell<" not in text
    assert ">Payment<" not in text


@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_russian_ui_sales_create_error(mock_core):
    mock_core.get_product.return_value = MOCK_PRODUCT
    mock_core.create_sale.return_value = MOCK_SALE_ERROR
    
    response = client.post(
        "/sales/create",
        data={
            "product_id": "1",
            "price": "50000",
            "payment_method": "cash",
            "notes": "",
        },
    )
    assert response.status_code == 200
    
    text = response.text
    assert "Товар нельзя продать в текущем статусе" in text
    assert "Cannot sell product" not in text  # Raw error shouldn't be exposed directly to UI


@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_russian_ui_sales_detail(mock_core):
    mock_core.get_sale.return_value = {
        "id": 1,
        "total_amount": 50000.0,
        "payment_method": "card",
        "status": "completed",
    }
    
    response = client.get("/sales/1")
    assert response.status_code == 200
    
    text = response.text
    assert "Продажа оформлена" in text
    assert "Карта" in text
    assert "Завершена" in text
    assert "Вернуться к товарам" in text
