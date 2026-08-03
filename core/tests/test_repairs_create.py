import pytest

def test_create_repair_order_success(client):
    payload = {
        "customer_name": "Иванов Иван Иванович",
        "customer_phone": "+7 900 123-45-67",
        "customer_email": "ivanov@example.com",
        "device_type": "Ноутбук",
        "brand": "Lenovo",
        "model": "ThinkPad T480",
        "serial_number": "SN-LENOVO-123",
        "reported_issue": "Не включается при нажатии кнопки питания",
        "completeness": "Ноутбук, бп",
        "appearance": "Потёртости",
        "access_code_provided": True,
        "priority": "normal"
    }

    res = client.post("/api/repairs/", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert data["id"] is not None
    assert data["number"].startswith("R-")
    assert data["status"] == "received"
    assert data["customer_name"] == "Иванов Иван Иванович"
    assert data["customer_phone"] == "+7 900 123-45-67"
    assert data["device_type"] == "Ноутбук"
    assert data["reported_issue"] == "Не включается при нажатии кнопки питания"
    assert data["access_code_provided"] is True
    assert len(data["history"]) == 1
    assert data["history"][0]["new_status"] == "received"

def test_create_repair_order_unique_number(client):
    payload1 = {
        "customer_name": "Клиент 1",
        "customer_phone": "+7 900 000-00-01",
        "device_type": "Телефон",
        "reported_issue": "Разбит экран"
    }
    payload2 = {
        "customer_name": "Клиент 2",
        "customer_phone": "+7 900 000-00-02",
        "device_type": "Планшет",
        "reported_issue": "Не заряжается"
    }

    res1 = client.post("/api/repairs/", json=payload1)
    res2 = client.post("/api/repairs/", json=payload2)

    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res1.json()["number"] != res2.json()["number"]

def test_create_repair_order_missing_required_fields(client):
    res = client.post("/api/repairs/", json={
        "customer_name": "",
        "customer_phone": "+7 900 000-00-00",
        "device_type": "Ноутбук",
        "reported_issue": "Не работает"
    })
    assert res.status_code == 422

def test_create_repair_order_invalid_priority(client):
    res = client.post("/api/repairs/", json={
        "customer_name": "Иван",
        "customer_phone": "+7 900 000-00-00",
        "device_type": "Ноутбук",
        "reported_issue": "Сломался",
        "priority": "super_high"
    })
    assert res.status_code == 422
