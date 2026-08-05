import pytest
from app import models

def test_diagnostics_exit_all_statuses_with_inline_amount(client, db_session):
    """
    Test exiting diagnostics to all allowed target statuses with inline estimated_repair_amount.
    """
    transitions = [
        ("ready", 2800),
        ("ready", 0),
        ("waiting_customer", 0),
        ("waiting_parts", 500),
        ("in_repair", 1000),
        ("unrepairable", 0),
        ("canceled", 0),
    ]

    for idx, (target_status, amount) in enumerate(transitions):
        # Create repair in diagnostics status with amount=None and text fields=None
        create_res = client.post("/api/repairs/", json={
            "customer_name": f"Тест Выхода {idx}",
            "customer_phone": "+7 900 111-22-33",
            "device_type": "Ноутбук",
            "reported_issue": "Тест"
        })
        rep_id = create_res.json()["id"]
        client.post(f"/api/repairs/{rep_id}/status", json={"status": "diagnostics"})

        # Submit status transition with inline estimated_repair_amount
        res = client.post(f"/api/repairs/{rep_id}/status", json={
            "status": target_status,
            "estimated_repair_amount": amount,
            "comment": None
        })
        assert res.status_code == 200, f"Transition diagnostics -> {target_status} with amount {amount} failed: {res.text}"
        data = res.json()
        assert data["status"] == target_status
        assert data["estimated_repair_amount"] == amount

        # Verify history entry created
        history = db_session.query(models.RepairStatusHistory).filter_by(repair_id=rep_id, new_status=target_status).first()
        assert history is not None
        assert history.comment is None


def test_diagnostics_exit_fallback_to_saved_amount_and_zero_override(client, db_session):
    """
    Test that exiting diagnostics uses saved amount if request amount is None,
    and that explicit request amount=0 overrides saved amount=2800.
    """
    # 1. Saved amount = 2800, request amount = None -> Uses saved amount 2800
    create_res1 = client.post("/api/repairs/", json={
        "customer_name": "Тест Сохранённого Значения",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест"
    })
    rep1_id = create_res1.json()["id"]
    client.post(f"/api/repairs/{rep1_id}/status", json={"status": "diagnostics"})
    client.patch(f"/api/repairs/{rep1_id}", json={"estimated_repair_amount": 2800})

    res1 = client.post(f"/api/repairs/{rep1_id}/status", json={"status": "ready"})
    assert res1.status_code == 200
    assert res1.json()["status"] == "ready"
    assert res1.json()["estimated_repair_amount"] == 2800

    # 2. Saved amount = 2800, request amount = 0 -> Explicit 0 overrides saved 2800
    create_res2 = client.post("/api/repairs/", json={
        "customer_name": "Тест Перезаписи Нулем",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест"
    })
    rep2_id = create_res2.json()["id"]
    client.post(f"/api/repairs/{rep2_id}/status", json={"status": "diagnostics"})
    client.patch(f"/api/repairs/{rep2_id}", json={"estimated_repair_amount": 2800})

    res2 = client.post(f"/api/repairs/{rep2_id}/status", json={
        "status": "ready",
        "estimated_repair_amount": 0
    })
    assert res2.status_code == 200
    assert res2.json()["status"] == "ready"
    assert res2.json()["estimated_repair_amount"] == 0


def test_diagnostics_exit_validation_rejections(client, db_session):
    """
    Test that negative amounts or decimal floats in status transition are rejected.
    """
    create_res = client.post("/api/repairs/", json={
        "customer_name": "Тест Ошибок Валидации",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест"
    })
    rep_id = create_res.json()["id"]
    client.post(f"/api/repairs/{rep_id}/status", json={"status": "diagnostics"})

    hist_count_before = db_session.query(models.RepairStatusHistory).filter_by(repair_id=rep_id).count()

    # Negative amount -> HTTP 422
    res_neg = client.post(f"/api/repairs/{rep_id}/status", json={
        "status": "ready",
        "estimated_repair_amount": -100
    })
    assert res_neg.status_code == 422

    # Decimal amount -> HTTP 422
    res_dec = client.post(f"/api/repairs/{rep_id}/status", json={
        "status": "ready",
        "estimated_repair_amount": 500.5
    })
    assert res_dec.status_code == 422

    # Verify status and history remained untouched
    det = client.get(f"/api/repairs/{rep_id}").json()
    assert det["status"] == "diagnostics"
    assert det["estimated_repair_amount"] is None
    hist_count_after = db_session.query(models.RepairStatusHistory).filter_by(repair_id=rep_id).count()
    assert hist_count_after == hist_count_before
