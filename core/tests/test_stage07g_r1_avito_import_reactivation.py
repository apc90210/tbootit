import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db
from app import models


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_a_create_new_avito_product(client, db_session: Session):
    """TEST A: Active Avito ID absent -> one Product created; in_stock/store/1; external relation created."""
    payload = {
        "account_key": "acc_main",
        "external_item_id": "item_stage07g_test_a",
        "external_url": "https://www.avito.ru/item/item_stage07g_test_a",
        "remote_status": "active",
        "title": "Ноутбук Lenovo IdeaPad 3",
        "price": 28000.0,
        "description": "Новый в упаковке",
        "parameters": {"Бренд": "Lenovo"}
    }
    res = client.post("/api/integrations/avito/import-item", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "created"
    p_id = data["product_id"]

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert p is not None
    assert p.status == "in_stock"
    assert p.storage_location == "store"
    assert p.quantity == 1
    assert p.sale_price == 28000.0

    ext = db_session.query(models.ProductExternalListing).filter(
        models.ProductExternalListing.external_item_id == "item_stage07g_test_a"
    ).first()
    assert ext is not None
    assert ext.product_id == p_id


def test_b_repeat_active_import(client, db_session: Session):
    """TEST B: Existing in_stock/store/1 -> same Product ID; created = 0; updated = 1; quantity still 1."""
    payload = {
        "account_key": "acc_main",
        "external_item_id": "item_stage07g_test_b",
        "external_url": "https://www.avito.ru/item/item_stage07g_test_b",
        "remote_status": "active",
        "title": "Монитор Dell 24",
        "price": 11000.0,
        "parameters": {}
    }
    res1 = client.post("/api/integrations/avito/import-item", json=payload)
    p_id = res1.json()["product_id"]

    res2 = client.post("/api/integrations/avito/import-item", json=payload)
    data2 = res2.json()
    assert data2["status"] == "updated"
    assert data2["product_id"] == p_id

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert p.quantity == 1
    assert p.status == "in_stock"
    assert p.storage_location == "store"


def test_c_archived_product_reactivation(client, db_session: Session):
    """TEST C: Existing sold/archive/0 with same Avito ID -> same Product ID; in_stock/store/1; event avito_import_reactivated; zero duplicate."""
    payload = {
        "account_key": "acc_main",
        "external_item_id": "item_stage07g_test_c",
        "external_url": "https://www.avito.ru/item/item_stage07g_test_c",
        "remote_status": "active",
        "title": "Планшет Samsung Tab A",
        "price": 14000.0,
        "parameters": {}
    }
    res1 = client.post("/api/integrations/avito/import-item", json=payload)
    p_id = res1.json()["product_id"]

    # Move to sold/archive/0
    p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    p.status = "sold"
    p.storage_location = "archive"
    p.quantity = 0
    db_session.commit()

    # Deliberate active import reactivates
    res2 = client.post("/api/integrations/avito/import-item", json=payload)
    assert res2.status_code == 200
    assert res2.json()["product_id"] == p_id

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert p.status == "in_stock"
    assert p.storage_location == "store"
    assert p.quantity == 1

    # Check event
    event = db_session.query(models.ProductEvent).filter(
        models.ProductEvent.product_id == p_id,
        models.ProductEvent.event_type == "avito_import_reactivated"
    ).first()
    assert event is not None

    # Zero duplicate products
    count = db_session.query(models.Product).filter(models.Product.sku == f"AVITO-item_stage07g_test_c").count()
    assert count == 1


def test_d_draft_positive_stock_to_in_stock(client, db_session: Session):
    """TEST D: draft/store/1 + active -> in_stock/store/1."""
    payload = {
        "account_key": "acc_main",
        "external_item_id": "item_stage07g_test_d",
        "external_url": "https://www.avito.ru/item/item_stage07g_test_d",
        "remote_status": "active",
        "title": "Клавиатура Keychron",
        "price": 6000.0,
        "parameters": {}
    }
    res1 = client.post("/api/integrations/avito/import-item", json=payload)
    p_id = res1.json()["product_id"]

    # Set draft/store/1
    p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    p.status = "draft"
    p.storage_location = "store"
    p.quantity = 1
    db_session.commit()

    # Active Avito import -> in_stock/store/1
    res2 = client.post("/api/integrations/avito/import-item", json=payload)
    assert res2.status_code == 200
    assert res2.json()["product_id"] == p_id

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert p.status == "in_stock"
    assert p.storage_location == "store"
    assert p.quantity == 1


def test_e_quantity_inflation_protection(client, db_session: Session):
    """TEST E: Run same active import 5 times -> quantity remains 1."""
    payload = {
        "account_key": "acc_main",
        "external_item_id": "item_stage07g_test_e",
        "external_url": "https://www.avito.ru/item/item_stage07g_test_e",
        "remote_status": "active",
        "title": "Мышь Logitech MX Master",
        "price": 7500.0,
        "parameters": {}
    }
    res1 = client.post("/api/integrations/avito/import-item", json=payload)
    p_id = res1.json()["product_id"]

    for _ in range(5):
        r = client.post("/api/integrations/avito/import-item", json=payload)
        assert r.status_code == 200
        assert r.json()["product_id"] == p_id

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert p.quantity == 1
    count = db_session.query(models.Product).filter(models.Product.sku == "AVITO-item_stage07g_test_e").count()
    assert count == 1


def test_f_content_update(client, db_session: Session):
    """TEST F: Change Avito price/title -> same Product ID; fields update; quantity unchanged."""
    payload = {
        "account_key": "acc_main",
        "external_item_id": "item_stage07g_test_f",
        "external_url": "https://www.avito.ru/item/item_stage07g_test_f",
        "remote_status": "active",
        "title": "Исходный заголовок",
        "price": 10000.0,
        "description": "Исходное описание",
        "parameters": {}
    }
    res1 = client.post("/api/integrations/avito/import-item", json=payload)
    p_id = res1.json()["product_id"]

    update_payload = dict(payload)
    update_payload["title"] = "Обновленный заголовок"
    update_payload["price"] = 12500.0
    update_payload["description"] = "Обновленное описание"

    res2 = client.post("/api/integrations/avito/import-item", json=update_payload)
    assert res2.status_code == 200
    assert res2.json()["product_id"] == p_id

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert p.title == "Обновленный заголовок"
    assert p.sale_price == 12500.0
    assert p.description == "Обновленное описание"
    assert p.quantity == 1


def test_g_through_j_inactive_listing_does_not_zero_stock(client, db_session: Session):
    """
    TEST G, H, I, J:
    in_stock/store/1 + blocked/removed/archived/closed -> physical state unchanged.
    """
    statuses = [
        ("blocked", "заблокировано"),
        ("removed", "снято с публикации"),
        ("archived", "в архиве"),
        ("closed", "завершено")
    ]

    for idx, (rem_st, raw_st) in enumerate(statuses):
        item_id = f"item_stage07g_test_inactive_{idx}"
        payload_active = {
            "account_key": "acc_main",
            "external_item_id": item_id,
            "external_url": f"https://www.avito.ru/item/{item_id}",
            "remote_status": "active",
            "title": f"Товар для теста {rem_st}",
            "price": 5000.0 + idx,
            "parameters": {}
        }
        res1 = client.post("/api/integrations/avito/import-item", json=payload_active)
        p_id = res1.json()["product_id"]

        # Re-import with remote inactive status
        payload_inactive = dict(payload_active)
        payload_inactive["remote_status"] = rem_st
        payload_inactive["remote_status_raw"] = raw_st

        res2 = client.post("/api/integrations/avito/import-item", json=payload_inactive)
        assert res2.status_code == 200
        assert res2.json()["product_id"] == p_id

        db_session.expire_all()
        p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
        # Physical stock MUST remain untouched!
        assert p.status == "in_stock", f"Status for {rem_st} was changed to {p.status}!"
        assert p.storage_location == "store", f"Location for {rem_st} was changed to {p.storage_location}!"
        assert p.quantity == 1, f"Quantity for {rem_st} was zeroed to {p.quantity}!"

        # External listing reflects remote status
        ext = db_session.query(models.ProductExternalListing).filter(
            models.ProductExternalListing.external_item_id == item_id
        ).first()
        assert ext.remote_status == rem_st


def test_k_l_m_local_sale_then_deliberate_reimport(client, db_session: Session):
    """
    TEST K: local sale -> sold/archive/0.
    TEST L: deliberate active re-import -> in_stock/store/1.
    TEST M: sale history preserved (Sale / SaleItem unchanged).
    """
    item_id = "item_stage07g_test_sale_reimport"
    payload = {
        "account_key": "acc_main",
        "external_item_id": item_id,
        "external_url": f"https://www.avito.ru/item/{item_id}",
        "remote_status": "active",
        "title": "Телевизор LG 43",
        "price": 22000.0,
        "parameters": {}
    }
    r_init = client.post("/api/integrations/avito/import-item", json=payload)
    p_id = r_init.json()["product_id"]

    # TEST K: local sale
    sale_payload = {
        "total_amount": 22000.0,
        "payment_method": "card",
        "comment": "Test K local sale",
        "items": [
            {
                "product_id": p_id,
                "title": "Телевизор LG 43",
                "price": 22000.0,
                "quantity": 1
            }
        ]
    }
    r_sale = client.post("/api/sales/", json=sale_payload)
    assert r_sale.status_code == 200
    sale_id = r_sale.json()["id"]

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert p.status == "sold"
    assert p.storage_location == "archive"
    assert p.quantity == 0

    # TEST L: deliberate active re-import
    r_reimport = client.post("/api/integrations/avito/import-item", json=payload)
    assert r_reimport.status_code == 200
    assert r_reimport.json()["product_id"] == p_id

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert p.status == "in_stock"
    assert p.storage_location == "store"
    assert p.quantity == 1

    # TEST M: sale history preserved
    sale_record = db_session.query(models.Sale).filter(models.Sale.id == sale_id).first()
    assert sale_record is not None
    assert sale_record.total_amount == 22000.0
    sale_item = db_session.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).first()
    assert sale_item is not None
    assert sale_item.product_id == p_id


def test_n_cancellation_workflow(client, db_session: Session):
    """TEST N: Existing cancellation workflow still restores stock correctly."""
    item_id = "item_stage07g_test_cancel"
    payload = {
        "account_key": "acc_main",
        "external_item_id": item_id,
        "external_url": f"https://www.avito.ru/item/{item_id}",
        "remote_status": "active",
        "title": "Колонки JBL",
        "price": 4000.0,
        "parameters": {}
    }
    r_init = client.post("/api/integrations/avito/import-item", json=payload)
    p_id = r_init.json()["product_id"]

    # Sell
    sale_payload = {
        "total_amount": 4000.0,
        "payment_method": "cash",
        "items": [{"product_id": p_id, "title": "Колонки JBL", "price": 4000.0, "quantity": 1}]
    }
    r_sale = client.post("/api/sales/", json=sale_payload)
    sale_id = r_sale.json()["id"]

    # Cancel sale
    r_cancel = client.post(f"/api/sales/{sale_id}/cancel", json={"reason": "Customer changed mind"})
    assert r_cancel.status_code == 200

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == p_id).first()
    assert p.status == "in_stock"
    assert p.storage_location == "store"
    assert p.quantity == 1


def test_o_p_primary_and_fallback_lookup(client, db_session: Session):
    """
    TEST O: Find same product across all statuses.
    TEST P: SKU fallback heals missing relation without duplicate.
    """
    item_id = "item_stage07g_test_fallback_sku"
    sku = f"AVITO-{item_id}"

    # Pre-create product in DB without external listing
    p = models.Product(
        sku=sku,
        title="Локально созданный товар для проверки SKU fallback",
        sale_price=9900.0,
        status="in_stock",
        storage_location="store",
        quantity=1
    )
    db_session.add(p)
    db_session.commit()
    p_id = p.id

    payload = {
        "account_key": "acc_main",
        "external_item_id": item_id,
        "external_url": f"https://www.avito.ru/item/{item_id}",
        "remote_status": "active",
        "title": "Обновленный с Авито",
        "price": 10500.0,
        "parameters": {}
    }
    r = client.post("/api/integrations/avito/import-item", json=payload)
    assert r.status_code == 200
    assert r.json()["product_id"] == p_id

    # Healed external listing
    ext = db_session.query(models.ProductExternalListing).filter(
        models.ProductExternalListing.external_item_id == item_id
    ).first()
    assert ext is not None
    assert ext.product_id == p_id

    # Zero duplicate product
    count = db_session.query(models.Product).filter(models.Product.sku == sku).count()
    assert count == 1


def test_q_local_only_product_unaffected(client, db_session: Session):
    """
    TEST Q: Create normal internal product without Avito ID:
    - valid; appears in product workflows; unaffected by Avito sync.
    """
    # Create internal product via POST /api/products/
    create_payload = {
        "title": "Внутренний сервисный кабель",
        "sku": "LOCAL-CABLE-001",
        "sale_price": 500.0,
        "purchase_price": 200.0,
        "status": "in_stock",
        "storage_location": "workshop",
        "quantity": 5
    }
    res = client.post("/api/products/", json=create_payload)
    assert res.status_code == 200
    prod_id = res.json()["id"]

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == prod_id).first()
    assert p is not None
    assert p.sku == "LOCAL-CABLE-001"
    assert p.storage_location == "workshop"
    assert p.quantity == 5

    # Check that external listings has no entry for this product
    ext = db_session.query(models.ProductExternalListing).filter(
        models.ProductExternalListing.product_id == prod_id
    ).first()
    assert ext is None
