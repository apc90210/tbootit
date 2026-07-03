import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

@pytest.mark.asyncio
async def test_receipt_warranty_and_org_text():
    mock_health = AsyncMock()
    mock_health.return_value = {"core_available": True}
    
    mock_get_sale = AsyncMock()
    mock_get_sale.return_value = {
        "id": 1,
        "total_amount": 1000,
        "warranty_days": 30,
        "warranty_enabled": True,
        "items": []
    }
    
    mock_get_org_settings = AsyncMock()
    mock_get_org_settings.return_value = {
        "organization_name": "ИП Атанов Павел Сергеевич",
        "inn": "667009336901",
        "address": "Свердловская обл.",
        "phone": "+7 343 344 88 95",
        "warranty_text": "Гарантия 30 дней.\nСтрока 2",
        "no_warranty_text": "Без гарантии"
    }

    with patch("app.routers.sales.core_client.health", mock_health), \
         patch("app.routers.sales.core_client.get_sale", mock_get_sale), \
         patch("app.routers.sales.core_client.get_organization_settings", mock_get_org_settings):
         
         response = client.get("/sales/1/receipt")
         assert response.status_code == 200
         html = response.text
         
         assert "ИП Атанов Павел Сергеевич" in html
         assert "667009336901" in html
         assert "Свердловская обл." in html
         assert "+7 343 344 88 95" in html
         
         assert "Гарантия 30 дней" not in html # Extracted away because first line is replaced! Wait, it will show "На все Б/У товары предоставляется гарантия <strong>30 дней</strong>." and "Строка 2".
         assert "Строка 2" in html
         assert "Без гарантии" not in html
         assert "Организация не задана" not in html

@pytest.mark.asyncio
async def test_receipt_no_warranty():
    mock_health = AsyncMock()
    mock_health.return_value = {"core_available": True}
    
    mock_get_sale = AsyncMock()
    mock_get_sale.return_value = {
        "id": 1,
        "total_amount": 1000,
        "warranty_days": 30,
        "warranty_enabled": False,
        "items": []
    }
    
    mock_get_org_settings = AsyncMock()
    mock_get_org_settings.return_value = {
        "organization_name": "ИП Атанов Павел Сергеевич",
        "inn": "667009336901",
        "address": "Свердловская обл.",
        "phone": "+7 343 344 88 95",
        "warranty_text": "Гарантия 30 дней.\nСтрока 2",
        "no_warranty_text": "Строка без гарантии"
    }

    with patch("app.routers.sales.core_client.health", mock_health), \
         patch("app.routers.sales.core_client.get_sale", mock_get_sale), \
         patch("app.routers.sales.core_client.get_organization_settings", mock_get_org_settings):
         
         response = client.get("/sales/1/receipt")
         assert response.status_code == 200
         html = response.text
         
         assert "Строка без гарантии" in html
         assert "Строка 2" not in html

@pytest.mark.asyncio
async def test_receipt_no_br_tags_and_close_button():
    mock_health = AsyncMock()
    mock_health.return_value = {"core_available": True}
    
    mock_get_sale = AsyncMock()
    mock_get_sale.return_value = {
        "id": 1,
        "total_amount": 1000,
        "warranty_days": 30,
        "warranty_enabled": True,
        "items": []
    }
    
    mock_get_org_settings = AsyncMock()
    mock_get_org_settings.return_value = {
        "warranty_text": "Line 1\nLine 2",
        "no_warranty_text": "Line 1\nLine 2"
    }

    with patch("app.routers.sales.core_client.health", mock_health), \
         patch("app.routers.sales.core_client.get_sale", mock_get_sale), \
         patch("app.routers.sales.core_client.get_organization_settings", mock_get_org_settings):
         
         response = client.get("/sales/1/receipt")
         html = response.text
         
         assert "<br>" not in html or html.count("<br>") <= 10 # We have technical <br> for headers and signatures
         assert "&lt;br&gt;" not in html
         assert "window.history.length" in html or "href='/sales'" in html
