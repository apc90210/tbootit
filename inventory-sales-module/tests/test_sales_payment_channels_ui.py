import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


def test_cart_has_legal_entity_account_option():
    """Cart checkout form includes Счёт юрлица and СБП payment options."""
    # Add an item to cart so the checkout form is shown
    client.post("/cart/add", data={"product_id": "1", "title": "Test", "price": "100.0"})
    response = client.get("/cart")
    assert response.status_code == 200
    html = response.text
    assert 'value="legal_entity_account"' in html
    assert 'Счёт юрлица' in html
    assert 'value="sbp"' in html
    assert 'СБП' in html


def test_cart_has_all_payment_options():
    """All six payment methods are present in cart form."""
    # Add an item to cart so the checkout form is shown
    client.post("/cart/add", data={"product_id": "1", "title": "Test", "price": "100.0"})
    response = client.get("/cart")
    assert response.status_code == 200
    html = response.text
    assert 'value="cash"' in html
    assert 'value="card"' in html
    assert 'value="transfer"' in html
    assert 'value="sbp"' in html
    assert 'value="legal_entity_account"' in html
    assert 'value="other"' in html


@pytest.mark.asyncio
async def test_receipt_shows_payment_method_label():
    """Receipt page shows the human-readable payment method label."""
    mock_get_sale = AsyncMock(return_value={
        "id": 1,
        "total_amount": 5000,
        "items": [],
        "payment_method": "legal_entity_account",
        "warranty_enabled": False,
        "warranty_days": 0,
        "created_at": "2026-07-03T10:00:00",
        "customer_label": "Тест"
    })
    mock_health = AsyncMock(return_value={"core_available": True})
    mock_get_org = AsyncMock(return_value={
        "organization_name": "ИП Тест",
        "inn": "123456789",
        "address": "ул. Тест",
        "phone": "+7 000 000 00 00",
        "default_customer_label": "Частное лицо",
        "warranty_text": "Гарантия 30 дней.",
        "no_warranty_text": "Без гарантии."
    })

    with patch("app.routers.sales.core_client.get_sale", mock_get_sale), \
         patch("app.routers.sales.core_client.health", mock_health), \
         patch("app.routers.sales.core_client.get_organization_settings", mock_get_org):

        response = client.get("/sales/1/receipt")
        assert response.status_code == 200
        html = response.text
        assert "Счёт юрлица" in html
