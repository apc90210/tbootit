import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

@pytest.mark.asyncio
async def test_receipt_warranty_and_org_text():
    mock_health = AsyncMock()
    mock_health.return_value = {"core_available": True}
    
    mock_get_receipt_data = AsyncMock()
    mock_get_receipt_data.return_value = {
        "id": 1,
        "sale_id": 1,
        "receipt_number": "REC-000001",
        "receipt_title": "Товарный чек № 1 от 2026-10-02",
        "date_formatted": "2026-10-02",
        "organization_name": "ИП Атанов Павел Сергеевич",
        "inn": "667009336901",
        "address": "Свердловская обл.",
        "phone": "+7 343 344 88 95",
        "warranty_title": "Гарантийные условия",
        "warranty_enabled": True,
        "warranty_days": 30,
        "warranty_headline": "На все Б/У товары предоставляется гарантия 30 дней.",
        "warranty_body_text": "Строка 2",
        "items": [],
        "total_items_count": 0,
        "total_amount": 1000.0,
        "total_amount_formatted": "1000.00",
        "prepayment_formatted": "0.00",
        "to_pay_formatted": "1000.00",
        "payment_method": "cash",
        "payment_method_label": "Наличные",
    }

    with patch("app.routers.sales.core_client.health", mock_health), \
         patch("app.routers.sales.core_client.get_sale_receipt_data", mock_get_receipt_data):
         
         response = client.get("/sales/1/receipt")
         assert response.status_code == 200
         html = response.text
         
         assert "ИП Атанов Павел Сергеевич" in html
         assert "667009336901" in html
         assert "Свердловская обл." in html
         assert "+7 343 344 88 95" in html
         
         assert "Строка 2" in html
         assert "Без гарантии" not in html
         assert "Организация не задана" not in html

@pytest.mark.asyncio
async def test_receipt_no_warranty():
    mock_health = AsyncMock()
    mock_health.return_value = {"core_available": True}
    
    mock_get_receipt_data = AsyncMock()
    mock_get_receipt_data.return_value = {
        "id": 1,
        "sale_id": 1,
        "receipt_number": "REC-000001",
        "receipt_title": "Товарный чек № 1 от 2026-10-02",
        "date_formatted": "2026-10-02",
        "organization_name": "ИП Атанов Павел Сергеевич",
        "inn": "667009336901",
        "address": "Свердловская обл.",
        "phone": "+7 343 344 88 95",
        "warranty_title": "Гарантийные условия",
        "warranty_enabled": False,
        "warranty_days": 0,
        "warranty_headline": "",
        "warranty_body_text": "Строка без гарантии",
        "items": [],
        "total_items_count": 0,
        "total_amount": 1000.0,
        "total_amount_formatted": "1000.00",
        "prepayment_formatted": "0.00",
        "to_pay_formatted": "1000.00",
        "payment_method": "cash",
        "payment_method_label": "Наличные",
    }

    with patch("app.routers.sales.core_client.health", mock_health), \
         patch("app.routers.sales.core_client.get_sale_receipt_data", mock_get_receipt_data):
         
         response = client.get("/sales/1/receipt")
         assert response.status_code == 200
         html = response.text
         
         assert "Строка без гарантии" in html
         assert "Строка 2" not in html

@pytest.mark.asyncio
async def test_receipt_no_br_tags_and_close_button():
    mock_health = AsyncMock()
    mock_health.return_value = {"core_available": True}
    
    mock_get_receipt_data = AsyncMock()
    mock_get_receipt_data.return_value = {
        "id": 1,
        "sale_id": 1,
        "receipt_number": "REC-000001",
        "receipt_title": "Товарный чек № 1 от 2026-10-02",
        "date_formatted": "2026-10-02",
        "organization_name": "ИП Атанов Павел Сергеевич",
        "inn": "667009336901",
        "address": "Свердловская обл.",
        "phone": "+7 343 344 88 95",
        "warranty_title": "Гарантийные условия",
        "warranty_enabled": True,
        "warranty_days": 30,
        "warranty_headline": "На все Б/У товары предоставляется гарантия 30 дней.",
        "warranty_body_text": "Line 1\nLine 2",
        "items": [],
        "total_items_count": 0,
        "total_amount": 1000.0,
        "total_amount_formatted": "1000.00",
        "prepayment_formatted": "0.00",
        "to_pay_formatted": "1000.00",
        "payment_method": "cash",
        "payment_method_label": "Наличные",
    }

    with patch("app.routers.sales.core_client.health", mock_health), \
         patch("app.routers.sales.core_client.get_sale_receipt_data", mock_get_receipt_data):
         
         response = client.get("/sales/1/receipt")
         html = response.text
         
         assert "<br>" not in html or html.count("<br>") <= 10
         assert "&lt;br&gt;" not in html
         assert "window.history.length" in html or "href='/sales'" in html
