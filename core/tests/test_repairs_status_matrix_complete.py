import pytest
from app import models

VALID_REPAIR_TRANSITIONS = {
    "received": {"diagnostics", "canceled"},
    "diagnostics": {"waiting_customer", "waiting_parts", "in_repair", "ready", "unrepairable", "canceled"},
    "waiting_customer": {"diagnostics", "waiting_parts", "in_repair", "unrepairable", "canceled"},
    "waiting_parts": {"waiting_customer", "in_repair", "unrepairable", "canceled"},
    "in_repair": {"waiting_customer", "waiting_parts", "ready", "unrepairable", "canceled"},
    "ready": {"in_repair", "issued"},
    "unrepairable": {"issued", "canceled"},
    "issued": set(),
    "canceled": set(),
}

def test_all_valid_status_transitions_complete(client, db_session):
    """
    Test every allowed transition in VALID_REPAIR_TRANSITIONS matrix.
    """
    for start_status, allowed_targets in VALID_REPAIR_TRANSITIONS.items():
        for target in allowed_targets:
            # Create a repair with initial start_status directly in DB
            repair = models.RepairOrder(
                number=f"TEST-{start_status}-{target}",
                status=start_status,
                customer_name="Тест Переходов",
                customer_phone="+7 900 111-22-33",
                device_type="Ноутбук",
                reported_issue="Тестирование переходов"
            )
            db_session.add(repair)
            db_session.commit()
            db_session.refresh(repair)

            resp = client.post(
                f"/api/repairs/{repair.id}/status",
                json={"status": target, "comment": f"Переход {start_status} -> {target}"}
            )
            assert resp.status_code == 200, f"Allowed transition {start_status} -> {target} failed with status {resp.status_code}: {resp.text}"
            data = resp.json()
            assert data["status"] == target

            # Verify history entry created
            hist_resp = client.get(f"/api/repairs/{repair.id}/history")
            assert hist_resp.status_code == 200
            history = hist_resp.json()
            last_entry = history[-1]
            assert last_entry["old_status"] == start_status
            assert last_entry["new_status"] == target

def test_diagnostics_to_ready_comment_requirement(client, db_session):
    """
    Test that diagnostics -> ready transition requires a non-empty comment.
    Empty or whitespace-only comments must be rejected with HTTP 400 and preserve status/history.
    """
    repair = models.RepairOrder(
        number="TEST-DIAG-READY-REQ",
        status="diagnostics",
        customer_name="Тест Диагностика Готов",
        customer_phone="+7 900 333-22-11",
        device_type="Смартфон",
        reported_issue="Не включается"
    )
    db_session.add(repair)
    db_session.commit()

    hist_before = len(db_session.query(models.RepairStatusHistory).filter_by(repair_id=repair.id).all())

    # 1. Attempt without comment -> should return HTTP 400
    res_no_comment = client.post(f"/api/repairs/{repair.id}/status", json={"status": "ready"})
    assert res_no_comment.status_code == 400
    assert "требуется указать комментарий" in res_no_comment.json()["detail"]

    # 2. Attempt with whitespace-only comment -> should return HTTP 400
    res_ws_comment = client.post(f"/api/repairs/{repair.id}/status", json={"status": "ready", "comment": "   "})
    assert res_ws_comment.status_code == 400

    # Verify status and history remained untouched
    db_session.refresh(repair)
    assert repair.status == "diagnostics"
    hist_after = len(db_session.query(models.RepairStatusHistory).filter_by(repair_id=repair.id).all())
    assert hist_after == hist_before

    # 3. Valid transition with comment -> should succeed
    res_success = client.post(
        f"/api/repairs/{repair.id}/status",
        json={"status": "ready", "comment": "Сбой устранён сбросом настроек"}
    )
    assert res_success.status_code == 200
    assert res_success.json()["status"] == "ready"
    assert res_success.json()["closed_at"] is None  # 'ready' does not close repair!

    # Verify history entry created with comment
    hist_final = db_session.query(models.RepairStatusHistory).filter_by(repair_id=repair.id).all()
    assert len(hist_final) == hist_before + 1
    assert hist_final[-1].comment == "Сбой устранён сбросом настроек"

def test_forbidden_status_transitions_rejected(client, db_session):
    """
    Test key forbidden transitions to ensure HTTP 409 Conflict is returned and status/history remain unchanged.
    """
    forbidden_pairs = [
        ("received", "ready"),
        ("received", "issued"),
        ("diagnostics", "issued"),
        ("waiting_parts", "diagnostics"),
        ("ready", "canceled"),
        ("unrepairable", "ready"),
        ("issued", "diagnostics"),
        ("canceled", "diagnostics"),
    ]

    for start_status, forbidden_target in forbidden_pairs:
        repair = models.RepairOrder(
            number=f"TEST-FORBIDDEN-{start_status}-{forbidden_target}",
            status=start_status,
            customer_name="Тест Запрета",
            customer_phone="+7 900 111-22-33",
            device_type="Ноутбук",
            reported_issue="Тестирование запрещённого перехода"
        )
        db_session.add(repair)
        db_session.commit()
        db_session.refresh(repair)

        # Count history entries before
        hist_before = len(db_session.query(models.RepairStatusHistory).filter_by(repair_id=repair.id).all())

        resp = client.post(
            f"/api/repairs/{repair.id}/status",
            json={"status": forbidden_target, "comment": "Запрещённая попытка"}
        )
        assert resp.status_code == 409, f"Forbidden transition {start_status} -> {forbidden_target} expected 409, got {resp.status_code}"
        
        # Verify status in DB did NOT change
        db_session.refresh(repair)
        assert repair.status == start_status

        # Verify no new history entry created
        hist_after = len(db_session.query(models.RepairStatusHistory).filter_by(repair_id=repair.id).all())
        assert hist_after == hist_before
