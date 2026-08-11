import pytest
from app import models

def test_repair_sale_idempotency_and_cancellation(client, db_session):
    """
    Test idempotency of repair-sale creation:
    - Multiple transitions to ready do NOT create duplicate sales.
    - Updated amount is saved to existing sale.
    - Transition to canceled updates linked sale status to 'canceled'.
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

    # 1. First transition to ready (amount = 3000)
    res1 = client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "ready", "comment": "Готов 1", "estimated_repair_amount": 3000}
    )
    assert res1.status_code == 200

    sales_count_1 = db_session.query(models.Sale).filter(
        models.Sale.source_type == "repair",
        models.Sale.source_id == rep.id
    ).count()
    assert sales_count_1 == 1

    # 2. Transition to in_repair and then ready again with updated amount 3500
    client.post(f"/api/repairs/{rep.id}/status", json={"status": "in_repair", "comment": "Допработа"})
    res2 = client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "ready", "comment": "Готов 2", "estimated_repair_amount": 3500}
    )
    assert res2.status_code == 200

    sales_2 = db_session.query(models.Sale).filter(
        models.Sale.source_type == "repair",
        models.Sale.source_id == rep.id
    ).all()
    assert len(sales_2) == 1
    assert sales_2[0].total_amount == 3500.0

    # 3. Transition to in_repair and then canceled
    client.post(f"/api/repairs/{rep.id}/status", json={"status": "in_repair", "comment": "Возврат на доработку"})
    res3 = client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "canceled", "comment": "Клиент передумал", "changed_by": "Менеджер"}
    )
    assert res3.status_code == 200

    db_session.expire_all()
    sale_after_cancel = db_session.query(models.Sale).filter(
        models.Sale.source_type == "repair",
        models.Sale.source_id == rep.id
    ).first()
    assert sale_after_cancel.status == "canceled"
    assert sale_after_cancel.cancelled_at is not None
