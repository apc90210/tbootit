import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_organization_settings():
    response = client.get("/api/settings/organization")
    assert response.status_code == 200
    data = response.json()
    assert "organization_name" in data
    assert "inn" in data

def test_update_organization_settings():
    payload = {
        "organization_name": "ООО Тестовая Компания",
        "inn": "123456789012",
        "address": "Тестовый адрес",
        "phone": "+7 000 000 00 00",
        "default_customer_label": "Тестовый покупатель"
    }
    response = client.put("/api/settings/organization", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["organization_name"] == "ООО Тестовая Компания"
    assert data["inn"] == "123456789012"
    
    # revert for other tests
    payload["organization_name"] = "ИП Атанов Павел Сергеевич"
    client.put("/api/settings/organization", json=payload)
