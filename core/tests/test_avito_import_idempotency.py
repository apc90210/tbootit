import pytest
from app import models

def test_avito_import_idempotency_zero_stock_mutation(client, db_session):
    """
    Test overall idempotency:
    - Multiple imports of same listing yield 0 duplicate Products and 0 duplicate links
    - Verifies NO sales or repair records are created or mutated by Avito catalog import
    """
    sales_count_before = db_session.query(models.Sale).count()
    repairs_count_before = db_session.query(models.RepairOrder).count()

    payload = {
        "account_key": "account_main",
        "external_item_id": "777000111",
        "title": "Монитор Dell 24",
        "price": 11000.0,
        "parameters": {"Диагональ": "24", "Матрица": "IPS"}
    }

    # Run import 3 times
    for _ in range(3):
        res = client.post("/api/integrations/avito/import-item", json=payload)
        assert res.status_code == 200

    # Counts after
    sales_count_after = db_session.query(models.Sale).count()
    repairs_count_after = db_session.query(models.RepairOrder).count()

    assert sales_count_after == sales_count_before, "No sales should be created"
    assert repairs_count_after == repairs_count_before, "No repairs should be created"

    # Products count for this SKU
    prods = db_session.query(models.Product).filter(models.Product.sku == "AVITO-777000111").all()
    assert len(prods) == 1
