from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

def test_sale_receipt_print_action_preview():
    mock_receipt_data = {
        "id": 88,
        "sale_id": 88,
        "receipt_number": "REC-000088",
        "receipt_title": "Товарный чек № 88 от 2026-07-22",
        "date_formatted": "2026-07-22",
        "created_at": "2026-07-22T12:00:00",
        "organization_name": "ООО ТехноРебут",
        "inn": "667009336901",
        "address": "Екатеринбург",
        "phone": "+7 343 344 88 95",
        "total_amount": 15000.0,
        "total_amount_formatted": "15000.00",
        "prepayment_formatted": "0.00",
        "to_pay_formatted": "15000.00",
        "payment_method": "cash",
        "payment_method_label": "Наличные",
        "status": "completed",
        "warranty_title": "Гарантийные условия",
        "warranty_enabled": True,
        "warranty_days": 30,
        "warranty_headline": "На все Б/У товары предоставляется гарантия 30 дней.",
        "warranty_body_text": "Условия гарантии",
        "items": [
            {
                "idx": 1,
                "product_id": 10,
                "title": "Монитор Dell",
                "price": 15000.0,
                "unit_price": 15000.0,
                "line_total": 15000.0,
                "price_formatted": "15000.00",
                "line_total_formatted": "15000.00",
                "quantity": 1,
                "unit": "шт",
            }
        ],
        "total_items_count": 1,
    }

    with patch("app.core_client.core_client.get_sale_receipt_data", new_callable=AsyncMock) as mock_get_data:
        mock_get_data.return_value = mock_receipt_data

        response = client.get("/sales/88/receipt")
        assert response.status_code == 200
        assert "Товарный чек № 88" in response.text
        assert "30 дней" in response.text
        assert "Предварительная форма товарного чека" in response.text

def test_sale_receipt_no_warranty_disclaimer():
    mock_receipt_data = {
        "id": 89,
        "sale_id": 89,
        "receipt_number": "REC-000089",
        "receipt_title": "Товарный чек № 89 от 2026-07-22",
        "date_formatted": "2026-07-22",
        "created_at": "2026-07-22T12:00:00",
        "organization_name": "ООО ТехноРебут",
        "inn": "667009336901",
        "address": "Екатеринбург",
        "phone": "+7 343 344 88 95",
        "total_amount": 10000.0,
        "total_amount_formatted": "10000.00",
        "prepayment_formatted": "0.00",
        "to_pay_formatted": "10000.00",
        "payment_method": "card",
        "payment_method_label": "Банковская карта",
        "status": "completed",
        "warranty_title": "Гарантийные условия",
        "warranty_enabled": False,
        "warranty_days": 0,
        "warranty_headline": "",
        "warranty_body_text": "Товар продаётся без гарантии, в том состоянии, в котором есть.",
        "items": [
            {
                "idx": 1,
                "product_id": 11,
                "title": "Клавиатура",
                "price": 10000.0,
                "unit_price": 10000.0,
                "line_total": 10000.0,
                "price_formatted": "10000.00",
                "line_total_formatted": "10000.00",
                "quantity": 1,
                "unit": "шт",
            }
        ],
        "total_items_count": 1,
    }

    with patch("app.core_client.core_client.get_sale_receipt_data", new_callable=AsyncMock) as mock_get_data:
        mock_get_data.return_value = mock_receipt_data

        response = client.get("/sales/89/receipt")
        assert response.status_code == 200
        assert "Товар продаётся без гарантии" in response.text
