import pytest
from app import models

def test_sold_product_reactivated_from_archive_via_avito_reimport(client, db_session):
    """
    Test scenario requested by Owner:
    1. Product is sold in the shop (moves to archive, status sold, quantity 0).
    2. Avito item is later reactivated on Avito and re-imported into Technoreboot.
    3. Technoreboot pulls the product out of archive, restores status 'in_stock',
       storage_location 'store', quantity 1, and updates details.
    4. Reverse mechanism: if Avito item becomes inactive, re-import moves it back to archive.
    """
    item_id = "111222333"
    sku = f"AVITO-{item_id}"

    # 1. Initial import as active
    init_payload = {
        "account_key": "account_laptops",
        "external_item_id": item_id,
        "external_url": f"https://www.avito.ru/item/{item_id}",
        "remote_status": "active",
        "title": "Игровой ноутбук ASUS ROG",
        "price": 75000.0,
        "description": "Отличное состояние",
        "parameters": {"Цвет": "Черный"}
    }
    r1 = client.post("/api/integrations/avito/import-item", json=init_payload)
    assert r1.status_code == 200
    p_id = r1.json()["product_id"]

    db_session.expire_all()
    prod = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert prod.status == "in_stock"
    assert prod.storage_location == "store"
    assert prod.quantity == 1

    # 2. Sell the product in the shop
    sale_payload = {
        "total_amount": 75000.0,
        "payment_method": "card",
        "comment": "Продажа в магазине",
        "items": [
            {"product_id": p_id, "title": prod.title, "price": 75000.0, "quantity": 1}
        ]
    }
    r_sale = client.post("/api/sales/", json=sale_payload)
    assert r_sale.status_code == 200

    db_session.expire_all()
    prod = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert prod.status == "sold"
    assert prod.storage_location == "archive"
    assert prod.quantity == 0

    # 3. Owner makes listing active on Avito again and re-imports
    reactivate_payload = {
        "account_key": "account_laptops",
        "external_item_id": item_id,
        "external_url": f"https://www.avito.ru/item/{item_id}",
        "remote_status": "active",
        "title": "Игровой ноутбук ASUS ROG (Новое объявление)",
        "price": 72000.0,
        "description": "Обновленная цена и состояние",
        "parameters": {"Цвет": "Черный", "Память": "16 ГБ"}
    }
    r_reimport = client.post("/api/integrations/avito/import-item", json=reactivate_payload)
    assert r_reimport.status_code == 200
    assert r_reimport.json()["status"] == "updated"
    assert r_reimport.json()["product_id"] == p_id

    db_session.expire_all()
    prod = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert prod.title == "Игровой ноутбук ASUS ROG (Новое объявление)"
    assert prod.sale_price == 72000.0
    assert prod.status == "in_stock"
    assert prod.storage_location == "store"
    assert prod.quantity == 1

    # Verify event logged
    events = db_session.query(models.ProductEvent).filter(
        models.ProductEvent.product_id == p_id,
        models.ProductEvent.event_type == "avito_reactivated"
    ).all()
    assert len(events) >= 1

    # 4. Reverse mechanism: listing is closed/inactive on Avito, re-importing moves product to archive
    inactive_payload = {
        "account_key": "account_laptops",
        "external_item_id": item_id,
        "external_url": f"https://www.avito.ru/item/{item_id}",
        "remote_status": "inactive",
        "remote_status_raw": "Завершено",
        "title": "Игровой ноутбук ASUS ROG (Новое объявление)",
        "price": 72000.0,
        "description": "Обновленная цена и состояние"
    }
    r_inactive = client.post("/api/integrations/avito/import-item", json=inactive_payload)
    assert r_inactive.status_code == 200

    db_session.expire_all()
    prod = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert prod.status == "sold"
    assert prod.storage_location == "archive"
    assert prod.quantity == 0

    events_archived = db_session.query(models.ProductEvent).filter(
        models.ProductEvent.product_id == p_id,
        models.ProductEvent.event_type == "avito_archived"
    ).all()
    assert len(events_archived) >= 1

    # 5. Reactivate once more: pulls back out of archive
    r_reimport2 = client.post("/api/integrations/avito/import-item", json=reactivate_payload)
    assert r_reimport2.status_code == 200

    db_session.expire_all()
    prod = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert prod.status == "in_stock"
    assert prod.storage_location == "store"
    assert prod.quantity == 1

def test_new_product_imported_as_inactive_starts_in_archive(client, db_session):
    """
    Test that importing a previously closed/inactive Avito listing for the first time
    creates it in archive status.
    """
    item_id = "555666777"
    payload = {
        "account_key": "account_laptops",
        "external_item_id": item_id,
        "external_url": f"https://www.avito.ru/item/{item_id}",
        "remote_status": "closed",
        "remote_status_raw": "Снято с публикации",
        "title": "Старый архивный монитор",
        "price": 3000.0
    }
    r = client.post("/api/integrations/avito/import-item", json=payload)
    assert r.status_code == 200
    p_id = r.json()["product_id"]

    db_session.expire_all()
    prod = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert prod.status == "sold"
    assert prod.storage_location == "archive"
    assert prod.quantity == 0
