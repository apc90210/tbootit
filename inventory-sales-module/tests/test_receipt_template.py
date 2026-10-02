from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@patch("app.routers.sales.core_client", new_callable=AsyncMock)
def test_sale_receipt_page(mock_core):
    mock_core.get_sale_receipt_data.return_value = {
        "id": 99,
        "sale_id": 99,
        "receipt_number": "REC-000099",
        "receipt_title": "Товарный чек № 99 от 2026-10-02",
        "date_formatted": "2026-10-02",
        "organization_name": "Test Org",
        "inn": "7700000000",
        "address": "Тестовый адрес",
        "phone": "+7 999 000 00 00",
        "warranty_title": "Гарантийные условия",
        "warranty_enabled": True,
        "warranty_days": 30,
        "warranty_body_text": "Гарантия 30 дней",
        "items": [
            {
                "idx": 1,
                "title": "Prod",
                "quantity": 1,
                "price": 1000.0,
                "unit_price": 1000.0,
                "line_total": 1000.0,
                "price_formatted": "1000.00",
                "line_total_formatted": "1000.00",
                "unit": "шт",
                "code": "1",
            }
        ],
        "total_items_count": 1,
        "total_amount": 1000.0,
        "total_amount_formatted": "1000.00",
        "prepayment_formatted": "0.00",
        "to_pay_formatted": "1000.00",
        "payment_method": "cash",
        "payment_method_label": "Наличные",
    }
    
    response = client.get("/sales/99/receipt")
    assert response.status_code == 200
    html = response.text
    assert "Товарный чек № 99" in html
    assert "Test Org" in html
    assert "Гарантийные условия" in html
    assert "30 дней" in html
    assert "openCanonicalPdfPrint()" in html
    assert "/sales/99/receipt/print" in html
    assert "window.print()" not in html
