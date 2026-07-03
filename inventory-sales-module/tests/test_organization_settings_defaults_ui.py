import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

@pytest.mark.asyncio
async def test_get_settings_organization_ui_shows_defaults():
    mock_health = AsyncMock()
    mock_health.return_value = {"core_available": True}
    
    mock_get_org_settings = AsyncMock()
    mock_get_org_settings.return_value = {
        "organization_name": "ИП Атанов Павел Сергеевич",
        "inn": "667009336901",
        "address": "Свердловская обл.",
        "phone": "+7 343 344 88 95",
        "warranty_text": "Гарантия 30 дней",
        "no_warranty_text": "Без гарантии"
    }

    with patch("app.routers.settings.core_client.health", mock_health), \
         patch("app.routers.settings.core_client.get_organization_settings", mock_get_org_settings):
         
         response = client.get("/settings/organization")
         assert response.status_code == 200
         
         html = response.text
         assert 'value="ИП Атанов Павел Сергеевич"' in html
         assert 'value="667009336901"' in html
         assert '>Гарантия 30 дней</textarea>' in html
         assert '>Без гарантии</textarea>' in html

@pytest.mark.asyncio
async def test_post_settings_organization_sends_values():
    mock_update = AsyncMock()
    
    with patch("app.routers.settings.core_client.update_organization_settings", mock_update):
        response = client.post("/settings/organization", data={
            "organization_name": "ООО",
            "inn": "111",
            "address": "Moscow",
            "phone": "999",
            "default_customer_label": "Person",
            "warranty_text": "Text 1",
            "no_warranty_text": "Text 2"
        }, follow_redirects=False)
        
        assert response.status_code == 303
        
        called_payload = mock_update.call_args[0][0]
        assert called_payload["organization_name"] == "ООО"
        assert called_payload["warranty_text"] == "Text 1"
        assert called_payload["no_warranty_text"] == "Text 2"

@pytest.mark.asyncio
async def test_get_settings_organization_ui_shows_fallback_defaults():
    mock_health = AsyncMock()
    mock_health.return_value = {"core_available": True}
    
    # Return empty values to simulate blank DB row
    mock_get_org_settings = AsyncMock()
    mock_get_org_settings.return_value = {
        "organization_name": "",
        "inn": " ",
        "address": "",
        "phone": "",
        "warranty_text": "",
        "no_warranty_text": ""
    }

    with patch("app.routers.settings.core_client.health", mock_health), \
         patch("app.routers.settings.core_client.get_organization_settings", mock_get_org_settings):
         
         response = client.get("/settings/organization")
         assert response.status_code == 200
         
         html = response.text
         assert 'value="ИП Атанов Павел Сергеевич"' in html
         assert 'value="667009336901"' in html
         assert 'На все Б/У товары предоставляется гарантия 30 дней' in html
