import pytest
from app import models

def test_repair_ready_does_not_create_sale_issued_creates_sale(client, db_session):
    """
    Stage 11B Canonical Rule: Готов != продажа.
    - Transitioning to 'ready' marks repair finished, but creates NO Sale.
    - Transitioning from 'ready' to 'issued' with payment and warranty creates exactly one linked Sale.
    """
    # 1. Create a repair in diagnostics
    rep = models.RepairOrder(
        number="R-STAGE11B-001",
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

    # 3. Verify NO Sale in DB on ready
    sale_on_ready = db_session.query(models.Sale).filter(
        models.Sale.source_type == "repair",
        models.Sale.source_id == rep.id
    ).first()
    assert sale_on_ready is None, "Готов != продажа: Ready must NOT create a sale"

    # 4. Transition to issued with payment details
    res_issue = client.post(
        f"/api/repairs/{rep.id}/status",
        json={
            "status": "issued",
            "final_amount": 2800.0,
            "payment_method": "cash",
            "warranty_days": 30,
            "changed_by": "Администратор",
            "comment": "Выдан клиенту"
        }
    )
    assert res_issue.status_code == 200
    issue_body = res_issue.json()
    assert issue_body["status"] == "issued"
    assert issue_body["final_amount"] == 2800.0
    assert issue_body["payment_method"] == "cash"
    assert issue_body["warranty_days"] == 30
    assert issue_body["sale_id"] is not None

    # 5. Verify linked Sale in DB
    sale = db_session.query(models.Sale).filter(
        models.Sale.source_type == "repair",
        models.Sale.source_id == rep.id
    ).first()
    assert sale is not None
    assert sale.total_amount == 2800.0
    assert sale.status == "completed"
    assert sale.payment_method == "cash"
    assert sale.warranty_days == 30
    assert "R-STAGE11B-001" in sale.comment
    assert "Lenovo" in sale.comment

    # 6. Verify line item created
    items = db_session.query(models.SaleItem).filter(models.SaleItem.sale_id == sale.id).all()
    assert len(items) == 1
    assert items[0].product_id is None
    assert items[0].price == 2800.0
    assert items[0].quantity == 1


def test_free_repair_issued_creates_zero_amount_sale(client, db_session):
    """
    Test that a free repair issued with final_amount=0 creates a linked sale with total_amount=0.
    """
    rep = models.RepairOrder(
        number="R-STAGE11B-FREE",
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

    # Move to ready
    res_ready = client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "ready", "comment": "Без оплаты", "estimated_repair_amount": 0}
    )
    assert res_ready.status_code == 200
    assert db_session.query(models.Sale).filter(models.Sale.source_type == "repair", models.Sale.source_id == rep.id).first() is None

    # Move to issued
    res_issue = client.post(
        f"/api/repairs/{rep.id}/status",
        json={
            "status": "issued",
            "final_amount": 0.0,
            "payment_method": "cash",
            "warranty_days": 0,
            "comment": "Бесплатная выдача"
        }
    )
    assert res_issue.status_code == 200

    sale = db_session.query(models.Sale).filter(
        models.Sale.source_type == "repair",
        models.Sale.source_id == rep.id
    ).first()
    assert sale is not None
    assert sale.total_amount == 0.0
    assert sale.status == "completed"
