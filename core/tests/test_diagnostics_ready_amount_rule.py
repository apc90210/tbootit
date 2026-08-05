import pytest
from app import models
import json

def test_diagnostics_to_ready_blocked_when_amount_is_none(client, db_session):
    # 1. Create a repair order and transition to diagnostics
    create_res = client.post("/api/repairs/", json={
        "customer_name": "Тест Блокировки Перехода",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест"
    })
    assert create_res.status_code == 201
    rep_id = create_res.json()["id"]

    client.post(f"/api/repairs/{rep_id}/status", json={"status": "diagnostics"})

    hist_count_before = db_session.query(models.RepairStatusHistory).filter(models.RepairStatusHistory.repair_id == rep_id).count()
    audit_count_before = db_session.query(models.AuditLog).filter(models.AuditLog.entity_id == rep_id).count()

    # 2. Attempt diagnostics -> ready with estimated_repair_amount=None -> Blocked (HTTP 400)
    res = client.post(f"/api/repairs/{rep_id}/status", json={"status": "ready"})
    assert res.status_code == 400
    assert "укажите стоимость ремонта" in res.json()["detail"]
    assert "Можно указать 0 ₽" in res.json()["detail"]

    # 3. Verify status remains diagnostics, no history or audit entry created
    det_res = client.get(f"/api/repairs/{rep_id}")
    assert det_res.json()["status"] == "diagnostics"

    hist_count_after = db_session.query(models.RepairStatusHistory).filter(models.RepairStatusHistory.repair_id == rep_id).count()
    audit_count_after = db_session.query(models.AuditLog).filter(models.AuditLog.entity_id == rep_id).count()
    assert hist_count_after == hist_count_before
    assert audit_count_after == audit_count_before


def test_diagnostics_to_ready_success_with_zero_amount_and_no_comment(client, db_session):
    create_res = client.post("/api/repairs/", json={
        "customer_name": "Тест Суммы 0",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест"
    })
    rep_id = create_res.json()["id"]

    client.post(f"/api/repairs/{rep_id}/status", json={"status": "diagnostics"})

    # Set estimated_repair_amount = 0
    client.patch(f"/api/repairs/{rep_id}", json={"estimated_repair_amount": 0})

    # Transition diagnostics -> ready without comment and without text fields
    res = client.post(f"/api/repairs/{rep_id}/status", json={"status": "ready"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["closed_at"] is None
    assert data["issued_at"] is None

    # Check history created with comment=None
    history = db_session.query(models.RepairStatusHistory).filter(
        models.RepairStatusHistory.repair_id == rep_id,
        models.RepairStatusHistory.new_status == "ready"
    ).first()
    assert history is not None
    assert history.comment is None


def test_diagnostics_to_ready_success_with_amount_2800_and_optional_comment(client, db_session):
    create_res = client.post("/api/repairs/", json={
        "customer_name": "Тест Суммы 2800",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Телефон",
        "reported_issue": "Тест"
    })
    rep_id = create_res.json()["id"]

    client.post(f"/api/repairs/{rep_id}/status", json={"status": "diagnostics"})

    # Set estimated_repair_amount = 2800, leave diagnosis text fields empty
    client.patch(f"/api/repairs/{rep_id}", json={"estimated_repair_amount": 2800})

    # Transition diagnostics -> ready with optional comment
    res = client.post(f"/api/repairs/{rep_id}/status", json={
        "status": "ready",
        "comment": "Всё готово к выдаче"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "ready"

    # Verify history records comment
    history = db_session.query(models.RepairStatusHistory).filter(
        models.RepairStatusHistory.repair_id == rep_id,
        models.RepairStatusHistory.new_status == "ready"
    ).first()
    assert history is not None
    assert history.comment == "Всё готово к выдаче"
