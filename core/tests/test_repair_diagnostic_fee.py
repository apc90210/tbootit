import pytest
from app import models

def test_create_repair_diagnostic_fee_default(client):
    res = client.post("/api/repairs/", json={
        "customer_name": "Тест Дефолта Диагностики",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["diagnostic_fee"] == 500.0

def test_create_repair_diagnostic_fee_custom_and_zero(client):
    # Custom 750
    res750 = client.post("/api/repairs/", json={
        "customer_name": "Тест 750",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 750
    })
    assert res750.status_code == 201
    assert res750.json()["diagnostic_fee"] == 750.0

    # Zero 0
    res0 = client.post("/api/repairs/", json={
        "customer_name": "Тест 0",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 0
    })
    assert res0.status_code == 201
    assert res0.json()["diagnostic_fee"] == 0.0

def test_create_repair_diagnostic_fee_validation(client):
    # Negative value
    res_neg = client.post("/api/repairs/", json={
        "customer_name": "Тест Отрицательный",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": -100
    })
    assert res_neg.status_code in [400, 422]

    # Invalid string
    res_str = client.post("/api/repairs/", json={
        "customer_name": "Тест Буквы",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": "abc"
    })
    assert res_str.status_code == 422

def test_read_endpoints_include_diagnostic_fee(client):
    res = client.post("/api/repairs/", json={
        "customer_name": "Тест Чтения",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 650
    })
    rep_id = res.json()["id"]
    number = res.json()["number"]

    # Detail
    res_det = client.get(f"/api/repairs/{rep_id}")
    assert res_det.status_code == 200
    assert res_det.json()["diagnostic_fee"] == 650.0

    # By number
    res_num = client.get(f"/api/repairs/by-number/{number}")
    assert res_num.status_code == 200
    assert res_num.json()["diagnostic_fee"] == 650.0

    # List
    res_list = client.get("/api/repairs/")
    assert res_list.status_code == 200
    items = res_list.json()["items"]
    match = next(i for i in items if i["id"] == rep_id)
    assert match["diagnostic_fee"] == 650.0

def test_patch_diagnostic_fee_and_terminal_protection(client):
    res = client.post("/api/repairs/", json={
        "customer_name": "Тест PATCH",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 500
    })
    rep_id = res.json()["id"]

    # PATCH 500 -> 800
    res_patch = client.patch(f"/api/repairs/{rep_id}", json={"diagnostic_fee": 800})
    assert res_patch.status_code == 200
    assert res_patch.json()["diagnostic_fee"] == 800.0

    # PATCH 800 -> 0
    res_patch0 = client.patch(f"/api/repairs/{rep_id}", json={"diagnostic_fee": 0})
    assert res_patch0.status_code == 200
    assert res_patch0.json()["diagnostic_fee"] == 0.0

    # Transition to terminal status 'canceled'
    client.post(f"/api/repairs/{rep_id}/status", json={"status": "canceled", "comment": "Отменён"})

    # Attempt PATCH on terminal repair -> 409 Conflict
    res_term = client.patch(f"/api/repairs/{rep_id}", json={"diagnostic_fee": 1000})
    assert res_term.status_code == 409

def test_options_diagnostic_fee_default(client):
    res = client.get("/api/repairs/options")
    assert res.status_code == 200
    assert res.json().get("default_diagnostic_fee") == 500

def test_audit_contains_diagnostic_fee(client, db_session):
    import json
    res = client.post("/api/repairs/", json={
        "customer_name": "Тест Аудита",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 750
    })
    rep_id = res.json()["id"]

    audit_logs = db_session.query(models.AuditLog).filter(
        models.AuditLog.entity_type == "repair_order",
        models.AuditLog.entity_id == rep_id
    ).all()

    create_log = next(a for a in audit_logs if a.action == "repair.created")
    val_create = json.loads(create_log.new_value)
    assert val_create.get("diagnostic_fee") == 750.0

    # PATCH
    client.patch(f"/api/repairs/{rep_id}", json={"diagnostic_fee": 900})

    audit_logs_after = db_session.query(models.AuditLog).filter(
        models.AuditLog.entity_type == "repair_order",
        models.AuditLog.entity_id == rep_id
    ).all()

    update_log = next(a for a in audit_logs_after if a.action == "repair.updated")
    val_old = json.loads(update_log.old_value)
    val_new = json.loads(update_log.new_value)
    assert val_old.get("diagnostic_fee") == 750.0
    assert val_new.get("diagnostic_fee") == 900.0
