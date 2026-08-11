import pytest
from app import models

def test_manual_product_creation_defaults_to_manual(client, db_session):
    """
    Test Blocker A fix: Creating a manual product does NOT set source_origin to 'avito'.
    It defaults to 'manual'.
    """
    payload = {
        "sku": "MANUAL-PROD-001",
        "title": "Ручной Системный Блок",
        "sale_price": 15000.0,
        "quantity": 1
    }

    res = client.post("/api/products/", json=payload)
    assert res.status_code == 200

    prod_data = res.json()
    assert prod_data["sku"] == "MANUAL-PROD-001"

    prod = db_session.query(models.Product).filter(models.Product.sku == "MANUAL-PROD-001").first()
    assert prod is not None
    assert prod.source_origin == "manual"

def test_avito_import_explicitly_sets_avito_origin(client, db_session):
    """
    Test that importing an Avito listing explicitly sets source_origin = 'avito'.
    """
    payload = {
        "account_key": "acc_origin_test",
        "external_item_id": "7766554433",
        "title": "Ноутбук HP Pavilion",
        "price": 28000.0
    }

    res = client.post("/api/integrations/avito/import-item", json=payload)
    assert res.status_code == 200
    prod_id = res.json()["product_id"]

    prod = db_session.query(models.Product).filter(models.Product.id == prod_id).first()
    assert prod is not None
    assert prod.source_origin == "avito"
