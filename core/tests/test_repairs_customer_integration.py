import pytest
from app import models

def test_customer_integration_and_snapshot_immutability(client, db_session):
    """
    Test Customer auto-creation, reuse by phone, snapshot in RepairOrder,
    snapshot immutability upon Customer edit, and rejection of unknown customer_id.
    """
    phone = "+7 955 888-77-66"

    # 1. Create repair with new phone -> should auto-create Customer
    res1 = client.post("/api/repairs/", json={
        "customer_name": "Виктор Снапшотов",
        "customer_phone": phone,
        "customer_email": "victor@snap.local",
        "device_type": "Ноутбук",
        "reported_issue": "Тест создания клиента"
    })
    assert res1.status_code == 201
    rep1_data = res1.json()
    cust_id = rep1_data["customer_id"]
    assert cust_id is not None

    # Verify Customer record exists in DB
    cust = db_session.query(models.Customer).filter(models.Customer.id == cust_id).first()
    assert cust is not None
    assert cust.phone == phone

    # 2. Create second repair with same phone -> should reuse existing Customer without creating duplicate
    cust_count_before = db_session.query(models.Customer).filter(models.Customer.phone == phone).count()
    res2 = client.post("/api/repairs/", json={
        "customer_name": "Виктор Снапшотов",
        "customer_phone": phone,
        "device_type": "Телефон",
        "reported_issue": "Второй ремонт того же клиента"
    })
    assert res2.status_code == 201
    rep2_data = res2.json()
    assert rep2_data["customer_id"] == cust_id

    cust_count_after = db_session.query(models.Customer).filter(models.Customer.phone == phone).count()
    assert cust_count_after == cust_count_before == 1

    # 3. Snapshot Immutability: Update Customer name via /api/customers/{id}
    res_cust_upd = client.patch(f"/api/customers/{cust_id}", json={
        "name": "Виктор Снапшотов (Изменён)",
        "phone": phone,
        "email": "victor@snap.local"
    })
    assert res_cust_upd.status_code == 200

    # Verify historical repair snapshot did NOT change
    res_rep1_check = client.get(f"/api/repairs/{rep1_data['id']}")
    assert res_rep1_check.status_code == 200
    assert res_rep1_check.json()["customer_name"] == "Виктор Снапшотов"

    # 4. Unknown customer_id -> should return HTTP 404
    res_err = client.post("/api/repairs/", json={
        "customer_id": 999999,
        "customer_name": "Неизвестный И.И.",
        "customer_phone": "+7 900 000-00-00",
        "device_type": "Ноутбук",
        "reported_issue": "Тест несуществующего customer_id"
    })
    assert res_err.status_code == 404
