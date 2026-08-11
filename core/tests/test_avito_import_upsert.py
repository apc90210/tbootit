import pytest
from app import models

def test_avito_import_upsert_updates_existing_product(client, db_session):
    """
    Test that importing an Avito item with an existing external_item_id updates the existing Product
    and ProductExternalListing without creating a new Product or duplicate link.
    """
    payload1 = {
        "account_key": "account_laptops",
        "external_item_id": "999888777",
        "external_url": "https://www.avito.ru/item/999888777",
        "remote_status": "active",
        "title": "Исходный заголовок",
        "price": 10000.0,
        "description": "Первоначальное описание",
        "parameters": {"Цвет": "Черный"}
    }

    res1 = client.post("/api/integrations/avito/import-item", json=payload1)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "created"
    product_id_1 = data1["product_id"]

    # Import updated information for same external item ID
    payload2 = {
        "account_key": "account_laptops",
        "external_item_id": "999888777",
        "external_url": "https://www.avito.ru/item/999888777",
        "remote_status": "inactive",
        "title": "Обновленный заголовок",
        "price": 12000.0,
        "description": "Обновленное описание товара",
        "parameters": {"Цвет": "Серебристый"}
    }

    res2 = client.post("/api/integrations/avito/import-item", json=payload2)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "updated"
    assert data2["product_id"] == product_id_1

    # Verify single Product in DB
    prods = db_session.query(models.Product).filter(models.Product.sku == "AVITO-999888777").all()
    assert len(prods) == 1
    assert prods[0].title == "Обновленный заголовок"
    assert prods[0].sale_price == 12000.0

    # Verify single external listing link
    links = db_session.query(models.ProductExternalListing).filter(models.ProductExternalListing.external_item_id == "999888777").all()
    assert len(links) == 1
    assert links[0].remote_status == "inactive"
