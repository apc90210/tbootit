import pytest
from app import models

def test_repair_sale_idempotency_and_cancellation(client, db_session):
    """
    Test idempotency of repair-sale creation on issue:
    - Moving to ready creates NO sale.
    - Multiple transitions/retries to issued do NOT create duplicate sales.
    - Exactly one sale exists.
    - Backward casual transition from issued is rejected.
    """
    rep = models.RepairOrder(
        number="R-IDEMPOTENT-001",
        status="diagnostics",
        customer_name="Идемпотентный Тест",
        customer_phone="+79998887766",
        device_type="Моноблок",
        brand="Apple",
        model="iMac",
        reported_issue="Замена SSD",
        estimated_repair_amount=3000
    )
    db_session.add(rep)
    db_session.commit()

    # 1. Transition to ready (no sale created)
    res_ready = client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "ready", "comment": "Готов", "estimated_repair_amount": 3000}
    )
    assert res_ready.status_code == 200
    assert db_session.query(models.Sale).filter(models.Sale.source_type == "repair", models.Sale.source_id == rep.id).count() == 0

    # 2. First transition to issued
    res1 = client.post(
        f"/api/repairs/{rep.id}/status",
        json={
            "status": "issued",
            "final_amount": 3000.0,
            "payment_method": "card",
            "warranty_days": 30,
            "comment": "Выдан"
        }
    )
    assert res1.status_code == 200

    sales_count_1 = db_session.query(models.Sale).filter(
        models.Sale.source_type == "repair",
        models.Sale.source_id == rep.id
    ).count()
    assert sales_count_1 == 1

    # 3. Retry/double-submit to issued
    res2 = client.post(
        f"/api/repairs/{rep.id}/status",
        json={
            "status": "issued",
            "final_amount": 3000.0,
            "payment_method": "card",
            "warranty_days": 30,
            "comment": "Повторный вызов"
        }
    )
    assert res2.status_code == 200

    sales_count_2 = db_session.query(models.Sale).filter(
        models.Sale.source_type == "repair",
        models.Sale.source_id == rep.id
    ).count()
    assert sales_count_2 == 1, "Idempotency: double submit must NOT create duplicate sale"

    # 4. Backward casual transition from issued is blocked
    res_back = client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "ready", "comment": "Откат назад"}
    )
    assert res_back.status_code == 409
