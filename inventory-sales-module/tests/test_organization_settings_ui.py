from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@patch("app.routers.settings.core_client", new_callable=AsyncMock)
def test_organization_settings_page(mock_core):
    mock_core.get_organization_settings.return_value = {
        "organization_name": "Test Org",
        "inn": "123456",
        "address": "Test Address",
        "phone": "123",
        "default_customer_label": "Person"
    }
    
    response = client.get("/settings/organization")
    assert response.status_code == 200
    assert "Test Org" in response.text
    assert "123456" in response.text
