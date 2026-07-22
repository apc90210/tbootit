from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

def test_sale_receipt_print_action_preview():
    mock_sale = {
        "id": 88,
        "created_at": "2026-07-22T12:00:00",
        "total_amount": 15000.0,
        "payment_method": "cash",
        "status": "completed",
        "warranty_enabled": True,
        "warranty_days": 30,
        "items": [{"product_id": 10, "title": "Монитор Dell", "price": 15000.0, "quantity": 1}]
    }

    with patch("app.core_client.core_client.get_sale", new_callable=AsyncMock) as mock_get_sale, \
         patch("app.core_client.core_client.get_organization_settings", new_callable=AsyncMock) as mock_get_org:
        mock_get_sale.return_value = mock_sale
        mock_get_org.return_value = {}

        response = client.get("/sales/88/receipt")
        assert response.status_code == 200
        assert "Товарный чек № 88" in response.text
        assert "30 дней" in response.text
        assert "Предварительная форма товарного чека" in response.text

def test_sale_receipt_no_warranty_disclaimer():
    mock_sale = {
        "id": 89,
        "created_at": "2026-07-22T12:00:00",
        "total_amount": 10000.0,
        "payment_method": "card",
        "status": "completed",
        "warranty_enabled": False,
        "warranty_days": None,
        "items": [{"product_id": 11, "title": "Клавиатура", "price": 10000.0, "quantity": 1}]
    }

    with patch("app.core_client.core_client.get_sale", new_callable=AsyncMock) as mock_get_sale, \
         patch("app.core_client.core_client.get_organization_settings", new_callable=AsyncMock) as mock_get_org:
        mock_get_sale.return_value = mock_sale
        mock_get_org.return_value = {}

        response = client.get("/sales/89/receipt")
        assert response.status_code == 200
        assert "Товар продаётся без гарантии" in response.text
