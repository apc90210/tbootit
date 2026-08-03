import pytest

def test_repairs_search_by_number_phone_serial(client):
    r1 = client.post("/api/repairs/", json={
        "customer_name": "Алексей Смирнов",
        "customer_phone": "+7 912 345-67-89",
        "device_type": "Ноутбук",
        "brand": "Asus",
        "model": "ZenBook",
        "serial_number": "SN-ASUS-999",
        "reported_issue": "Зависает при загрузке"
    }).json()

    # Search by number
    res_num = client.get(f"/api/repairs/?q={r1['number']}")
    assert res_num.status_code == 200
    assert res_num.json()["total"] == 1
    assert res_num.json()["items"][0]["id"] == r1["id"]

    # Search by phone
    res_phone = client.get("/api/repairs/?q=345-67-89")
    assert res_phone.status_code == 200
    assert res_phone.json()["total"] >= 1

    # Search by serial number
    res_sn = client.get("/api/repairs/?q=SN-ASUS-999")
    assert res_sn.status_code == 200
    assert res_sn.json()["total"] == 1

def test_repairs_filter_by_status_and_priority(client):
    r_urgent = client.post("/api/repairs/", json={
        "customer_name": "Срочный Клиент",
        "customer_phone": "+7 900 111-11-11",
        "device_type": "Телефон",
        "reported_issue": "Разбит динамик",
        "priority": "urgent"
    }).json()

    res_prio = client.get("/api/repairs/?priority=urgent")
    assert res_prio.status_code == 200
    assert any(item["id"] == r_urgent["id"] for item in res_prio.json()["items"])

    res_status = client.get("/api/repairs/?status=received")
    assert res_status.status_code == 200
    assert res_status.json()["total"] >= 1

def test_get_repair_by_number_endpoint(client):
    r = client.post("/api/repairs/", json={
        "customer_name": "По номеру",
        "customer_phone": "+7 900 222-22-22",
        "device_type": "Монитор",
        "reported_issue": "Нет изображения"
    }).json()

    res = client.get(f"/api/repairs/by-number/{r['number']}")
    assert res.status_code == 200
    assert res.json()["id"] == r["id"]
