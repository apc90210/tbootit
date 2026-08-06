import pytest
from app import models

def test_repair_ready_creates_sale_and_audit(client, db_session):
    """
    Test that transitioning a repair to status='ready' creates a linked Sale record.
    Verifies:
    - Sale created with total_amount = repair.estimated_repair_amount (e.g. 2800)
    - source_type = 'repair'
    - source_id = repair.id
    - Description contains repair number and issue
    - Audit log event repair.sale_created is generated
    """
    # 1. Create a repair in diagnostics
    rep = models.RepairOrder(
        number="R-STAGE05C-001",
        status="diagnostics",
        customer_name="Тест Продажи",
        customer_phone="+79998887766",
        device_type="Ноутбук",
        brand="Lenovo",
        model="IdeaPad 3",
        reported_issue="Не включается",
        estimated_repair_amount=2800
    )
    db_session.add(rep)
    db_session.commit()

    # 2. Transition to ready via API
    res = client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "ready", "comment": "Диагностика завершена, готов к выдаче", "estimated_repair_amount": 2800}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ready"
    assert body["estimated_repair_amount"] == 2800

    # 3. Verify linked Sale in DB
    sale = db_session.query(models.Sale).filter(
        models.Sale.source_type == "repair",
        models.Sale.source_id == rep.id
    ).first()
    assert sale is not None
    assert sale.total_amount == 2800.0
    assert sale.status == "completed"
    assert "R-STAGE05C-001" in sale.comment
    assert "Lenovo" in sale.comment
    assert "IdeaPad 3" in sale.comment
    assert "Не включается" in sale.comment

    # 4. Verify line item created
    items = db_session.query(models.SaleItem).filter(models.SaleItem.sale_id == sale.id).all()
    assert len(items) == 1
    assert items[0].product_id is None
    assert items[0].price == 2800.0
    assert items[0].quantity == 1

    # 5. Verify audit log entry
    audit = db_session.query(models.AuditLog).filter(
        models.AuditLog.action == "repair.sale_created",
        models.AuditLog.entity_id == rep.id
    ).first()
    assert audit is not None

def test_free_repair_ready_creates_zero_amount_sale(client, db_session):
    """
    Test that a free repair (estimated_repair_amount=0) creates a linked sale with total_amount=0.
    """
    rep = models.RepairOrder(
        number="R-STAGE05C-FREE",
        status="diagnostics",
        customer_name="Бесплатный Ремонт",
        customer_phone="+79998887766",
        device_type="Телефон",
        brand="Xiaomi",
        model="Redmi Note",
        reported_issue="Чистка разъёма",
        estimated_repair_amount=0
    )
    db_session.add(rep)
    db_session.commit()

    res = client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "ready", "comment": "Без оплаты", "estimated_repair_amount": 0}
    )
    assert res.status_code == 200

    sale = db_session.query(models.Sale).filter(
        models.Sale.source_type == "repair",
        models.Sale.source_id == rep.id
    ).first()
    assert sale is not None
    assert sale.total_amount == 0.0
    assert sale.status == "completed"
