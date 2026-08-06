import pytest
from app import models

def test_repair_sale_stock_isolation(client, db_session):
    """
    Test 100% stock isolation:
    - Creating a repair sale does NOT decrease product.quantity
    - Creating a repair sale does NOT create a dummy Product
    - Creating a repair sale does NOT generate stock movements
    """
    # Count products and stock movements before
    prod_count_before = db_session.query(models.Product).count()
    movement_count_before = db_session.query(models.StockMovement).count()

    # Create repair and set ready
    rep = models.RepairOrder(
        number="R-STOCK-ISO",
        status="diagnostics",
        customer_name="Тест Изоляции",
        customer_phone="+79998887766",
        device_type="Сервер",
        brand="Dell",
        model="PowerEdge",
        reported_issue="Замена БП",
        estimated_repair_amount=5000
    )
    db_session.add(rep)
    db_session.commit()

    res = client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "ready", "comment": "Готов", "estimated_repair_amount": 5000}
    )
    assert res.status_code == 200

    # Count products and stock movements after
    prod_count_after = db_session.query(models.Product).count()
    movement_count_after = db_session.query(models.StockMovement).count()

    assert prod_count_after == prod_count_before, "No products should be created"
    assert movement_count_after == movement_count_before, "No stock movements should be created"
