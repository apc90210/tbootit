from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "source": "chatgpt",
    "schema_version": "1.0",
    "operation": "create_or_update",
    "product": {
        "sku": "TEST-VALIDATE-001",
        "title": "Тестовый ноутбук",
        "category_path": ["Ноутбуки"],
        "brand": "TestBrand",
        "sale_price": 25000,
        "quantity": 1,
        "storage_location": "Склад 1"
    },
    "avito": {
        "title": "Тестовый ноутбук для Авито",
        "description": "Описание для Авито",
        "price": 25000,
        "contact_name": "Техноребут",
        "phone": "+7 999 000-00-01",
        "parameters": {"Производитель": "TestBrand"}
    }
}

INVALID_PAYLOAD = {
    "source": "chatgpt",
    "schema_version": "1.0",
    "operation": "create_or_update",
    "product": {
        "sku": "",       # empty sku = error
        "title": ""      # empty title = error
    }
}

def test_validate_valid_json():
    r = client.post("/api/product-cards/validate-json", json=VALID_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is True
    assert data["errors"] == []

def test_validate_invalid_json():
    r = client.post("/api/product-cards/validate-json", json=INVALID_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0

def test_validate_missing_avito_phone_warning():
    payload = {**VALID_PAYLOAD, "avito": {"title": "T", "description": "D", "price": 1000}}
    r = client.post("/api/product-cards/validate-json", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is True
    assert any("телефон" in w.lower() for w in data.get("warnings", []))
