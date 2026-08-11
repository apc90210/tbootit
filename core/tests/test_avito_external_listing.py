import pytest
from app import models

def test_create_avito_external_listing(client, db_session):
    """
    Test creating a new external listing link in Core API via POST /api/integrations/avito/import-item:
    - Creates a new Product with source_origin = 'avito'
    - Creates ProductExternalListing record
    - Verifies marketplace = 'avito', external_account_key, external_item_id, external_url, remote_status
    - Verifies audit events logged
    """
    payload = {
        "account_key": "account_main",
        "external_item_id": "2847291011",
        "external_url": "https://www.avito.ru/moskva/noutbuki/lenovo_ideapad_3_2847291011",
        "remote_status": "active",
        "remote_status_raw": "Активно",
        "title": "Ноутбук Lenovo IdeaPad 3 15ADA05",
        "price": 25000.0,
        "description": "Отличный рабочий ноутбук в идеальном состоянии",
        "category_path": ["Электроника", "Ноутбуки"],
        "brand": "Lenovo",
        "model": "IdeaPad 3",
        "condition": "Б/у",
        "parameters": {"Диагональ": "15.6", "Процессор": "AMD Ryzen 3"},
        "photos": []
    }

    res = client.post("/api/integrations/avito/import-item", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "created"
    product_id = data["product_id"]
    link_id = data["external_listing_id"]

    # Verify Product in DB
    prod = db_session.query(models.Product).filter(models.Product.id == product_id).first()
    assert prod is not None
    assert prod.title == "Ноутбук Lenovo IdeaPad 3 15ADA05"
    assert prod.sale_price == 25000.0
    assert prod.sku == "AVITO-2847291011"
    assert prod.source_origin == "avito"

    # Verify ProductExternalListing in DB
    link = db_session.query(models.ProductExternalListing).filter(models.ProductExternalListing.id == link_id).first()
    assert link is not None
    assert link.product_id == product_id
    assert link.marketplace == "avito"
    assert link.external_account_key == "account_main"
    assert link.external_item_id == "2847291011"
    assert link.remote_status == "active"

    # Verify Audit log
    audit_prod = db_session.query(models.AuditLog).filter(
        models.AuditLog.entity_type == "product",
        models.AuditLog.action == "avito.product_imported"
    ).first()
    assert audit_prod is not None

    audit_link = db_session.query(models.AuditLog).filter(
        models.AuditLog.entity_type == "product_external_listing",
        models.AuditLog.action == "avito.external_link_created"
    ).first()
    assert audit_link is not None
