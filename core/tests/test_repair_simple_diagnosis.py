import pytest
from app import models
import json

def test_patch_and_read_simple_diagnosis(client):
    # 1. Create a repair order
    create_res = client.post("/api/repairs/", json={
        "customer_name": "Тест Смета",
        "customer_phone": "+7 900 123-45-67",
        "device_type": "Ноутбук",
        "reported_issue": "Не включается"
    })
    assert create_res.status_code == 201
    rep_id = create_res.json()["id"]
    number = create_res.json()["number"]

    # 2. PATCH all 4 fields with line breaks, unicode, and integer amount 4100
    diag_text = "Неисправен разъём питания.\nТребуется замена разъёма и чистка."
    works_text = "1. Разборка ноутбука - 500 ₽\n2. Замена разъёма - 1500 ₽\n3. Чистка - 1000 ₽"
    parts_text = "1. Разъём питания - 800 ₽\n2. Термопаста - 300 ₽"

    patch_res = client.patch(f"/api/repairs/{rep_id}", json={
        "diagnosis_text": diag_text,
        "planned_works_text": works_text,
        "planned_parts_text": parts_text,
        "estimated_repair_amount": 4100
    })
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["diagnosis_text"] == diag_text
    assert patched_data["planned_works_text"] == works_text
    assert patched_data["planned_parts_text"] == parts_text
    assert patched_data["estimated_repair_amount"] == 4100
    assert isinstance(patched_data["estimated_repair_amount"], int)

    # 3. GET detail
    det_res = client.get(f"/api/repairs/{rep_id}")
    assert det_res.status_code == 200
    assert det_res.json()["diagnosis_text"] == diag_text
    assert det_res.json()["planned_works_text"] == works_text
    assert det_res.json()["planned_parts_text"] == parts_text
    assert det_res.json()["estimated_repair_amount"] == 4100

    # 4. GET by-number
    num_res = client.get(f"/api/repairs/by-number/{number}")
    assert num_res.status_code == 200
    assert num_res.json()["diagnosis_text"] == diag_text
    assert num_res.json()["estimated_repair_amount"] == 4100

    # 5. GET list
    list_res = client.get("/api/repairs/")
    assert list_res.status_code == 200
    match = next(i for i in list_res.json()["items"] if i["id"] == rep_id)
    assert match["diagnosis_text"] == diag_text
    assert match["estimated_repair_amount"] == 4100


def test_simple_diagnosis_zero_and_clearing(client):
    create_res = client.post("/api/repairs/", json={
        "customer_name": "Тест Очистка",
        "customer_phone": "+7 900 123-45-67",
        "device_type": "Телефон",
        "reported_issue": "Сброс"
    })
    rep_id = create_res.json()["id"]

    # PATCH amount 0
    patch0 = client.patch(f"/api/repairs/{rep_id}", json={
        "diagnosis_text": "Осмотр выполнен",
        "estimated_repair_amount": 0
    })
    assert patch0.status_code == 200
    assert patch0.json()["estimated_repair_amount"] == 0
    assert isinstance(patch0.json()["estimated_repair_amount"], int)

    # Clear text fields by setting to None
    patch_clear = client.patch(f"/api/repairs/{rep_id}", json={
        "diagnosis_text": None,
        "estimated_repair_amount": None
    })
    assert patch_clear.status_code == 200
    assert patch_clear.json()["diagnosis_text"] is None
    assert patch_clear.json()["estimated_repair_amount"] is None


def test_simple_diagnosis_validation(client):
    create_res = client.post("/api/repairs/", json={
        "customer_name": "Тест Валидации",
        "customer_phone": "+7 900 123-45-67",
        "device_type": "Планшет",
        "reported_issue": "Тест"
    })
    rep_id = create_res.json()["id"]

    # Negative amount rejected
    res_neg = client.patch(f"/api/repairs/{rep_id}", json={"estimated_repair_amount": -500})
    assert res_neg.status_code in [400, 422]

    # Decimal amount rejected (422)
    res_dec = client.patch(f"/api/repairs/{rep_id}", json={"estimated_repair_amount": 4100.5})
    assert res_dec.status_code == 422


def test_simple_diagnosis_terminal_protection(client):
    create_res = client.post("/api/repairs/", json={
        "customer_name": "Тест Закрытого",
        "customer_phone": "+7 900 123-45-67",
        "device_type": "Монитор",
        "reported_issue": "Тест"
    })
    rep_id = create_res.json()["id"]

    # Transition to terminal status 'canceled'
    client.post(f"/api/repairs/{rep_id}/status", json={"status": "canceled", "comment": "Отменён"})

    # Terminal PATCH rejected -> 409 Conflict
    res_term = client.patch(f"/api/repairs/{rep_id}", json={
        "diagnosis_text": "Попытка извращения",
        "estimated_repair_amount": 5000
    })
    assert res_term.status_code == 409


def test_simple_diagnosis_audit_log(client, db_session):
    create_res = client.post("/api/repairs/", json={
        "customer_name": "Тест Аудита Сметы",
        "customer_phone": "+7 900 123-45-67",
        "device_type": "ПК",
        "reported_issue": "Гудит"
    })
    rep_id = create_res.json()["id"]

    # Update diagnosis
    client.patch(f"/api/repairs/{rep_id}", json={
        "diagnosis_text": "Замена кулера",
        "estimated_repair_amount": 1500
    })

    audit_logs = db_session.query(models.AuditLog).filter(
        models.AuditLog.entity_type == "repair_order",
        models.AuditLog.entity_id == rep_id
    ).all()

    update_log = next(a for a in audit_logs if a.action == "repair.updated")
    val_new = json.loads(update_log.new_value)
    assert val_new.get("diagnosis_text") == "Замена кулера"
    assert val_new.get("estimated_repair_amount") == 1500
