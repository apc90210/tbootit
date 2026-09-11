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


def test_avito_id_lookup_across_all_statuses(client, db_session: Session):
    """
    Verify that Avito ID (external_item_id) is searched across the ENTIRE database
    regardless of status (in_stock, sold, archive, draft, reserved).
    """
    avito_id = "test_lookup_univ_1001"
    base_payload = {
        "account_key": "acc_main",
        "external_item_id": avito_id,
        "external_url": f"https://www.avito.ru/item/{avito_id}",
        "remote_status": "active",
        "title": "Универсальный ноутбук для проверки",
        "price": 25000.0,
        "description": "Первичное описание",
        "parameters": {"Бренд": "Asus", "Память": "16 ГБ"}
    }

    # 1. Initial import creates product in store
    r1 = client.post("/api/integrations/avito/import-item", json=base_payload)
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["status"] == "created"
    prod_id = data1["product_id"]

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == prod_id).first()
    assert p.status == "in_stock"
    assert p.storage_location == "store"
    assert p.quantity == 1
    assert p.sale_price == 25000.0

    # Verify total product count in DB for this SKU is 1
    count = db_session.query(models.Product).filter(models.Product.sku == f"AVITO-{avito_id}").count()
    assert count == 1

    # 2. Re-import when already in_stock: updates data if changed, no duplication, no stock reset
    update_payload = dict(base_payload)
    update_payload["price"] = 26500.0
    update_payload["description"] = "Обновленное описание"
    r2 = client.post("/api/integrations/avito/import-item", json=update_payload)
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["status"] == "updated"
    assert data2["product_id"] == prod_id  # SAME product

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == prod_id).first()
    assert p.sale_price == 26500.0
    assert p.description == "Обновленное описание"
    assert p.status == "in_stock"
    assert p.storage_location == "store"
    assert p.quantity == 1  # Not reset, not incremented

    # Product count is STILL 1 (no duplicate created)
    count = db_session.query(models.Product).filter(models.Product.sku == f"AVITO-{avito_id}").count()
    assert count == 1

    # 3. Simulate Sale / move to Archive
    p.status = "sold"
    p.storage_location = "archive"
    p.quantity = 0
    db_session.commit()

    # Re-import when in ARCHIVE with active status -> found and reactivated to store
    r3 = client.post("/api/integrations/avito/import-item", json=base_payload)
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["status"] == "updated"
    assert data3["product_id"] == prod_id  # SAME product

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == prod_id).first()
    assert p.status == "in_stock"
    assert p.storage_location == "store"
    assert p.quantity == 1  # Restored to 1
    count = db_session.query(models.Product).filter(models.Product.sku == f"AVITO-{avito_id}").count()
    assert count == 1

    # 4. Simulate status='draft' / location='draft'
    p.status = "draft"
    p.storage_location = "draft"
    p.quantity = 0
    db_session.commit()

    # Re-import when in DRAFT with active status -> found and activated to store
    r4 = client.post("/api/integrations/avito/import-item", json=base_payload)
    assert r4.status_code == 200
    assert r4.json()["product_id"] == prod_id

    db_session.expire_all()
    p = db_session.query(models.Product).filter(models.Product.id == prod_id).first()
    assert p.status == "in_stock"
    assert p.storage_location == "store"
    assert p.quantity == 1
    count = db_session.query(models.Product).filter(models.Product.sku == f"AVITO-{avito_id}").count()
    assert count == 1


def test_identical_reimport_does_nothing_to_stock_and_creates_no_duplicates(client, db_session: Session):
    """
    Verify that re-importing identical listing data leaves stock unchanged,
    creates zero duplicates, and updates only timestamp.
    """
    avito_id = "test_identical_noop_2002"
    payload = {
        "account_key": "acc_main",
        "external_item_id": avito_id,
        "external_url": f"https://www.avito.ru/item/{avito_id}",
        "remote_status": "active",
        "title": "Монитор 27 дюймов 144 Гц",
        "price": 14000.0,
        "description": "Отличное состояние",
        "parameters": {"Диагональ": "27"}
    }

    # First import
    res1 = client.post("/api/integrations/avito/import-item", json=payload)
    assert res1.status_code == 200
    prod_id = res1.json()["product_id"]

    # Re-import identical payload 3 times in a row
    for _ in range(3):
        res = client.post("/api/integrations/avito/import-item", json=payload)
        assert res.status_code == 200
        assert res.json()["product_id"] == prod_id
        assert res.json()["status"] == "updated"

    db_session.expire_all()
    # Check that only ONE product exists in DB
    prods = db_session.query(models.Product).filter(models.Product.sku == f"AVITO-{avito_id}").all()
    assert len(prods) == 1
    assert prods[0].status == "in_stock"
    assert prods[0].storage_location == "store"
    assert prods[0].quantity == 1
    assert prods[0].sale_price == 14000.0

    # Check that only ONE external listing link exists
    links = db_session.query(models.ProductExternalListing).filter(
        models.ProductExternalListing.external_item_id == avito_id
    ).all()
    assert len(links) == 1


def test_avito_id_sku_fallback_when_external_listing_missing(client, db_session: Session):
    """
    Verify that even if ProductExternalListing row was deleted or never created,
    the lookup falls back to searching products by SKU ('AVITO-{id}') across all statuses,
    prevents duplicate product creation, and automatically heals the external link.
    """
    avito_id = "test_fallback_sku_3003"
    sku = f"AVITO-{avito_id}"

    # Pre-create product in DB without external listing
    p = models.Product(
        sku=sku,
        title="Товар созданный вручную без external_listing",
        sale_price=8000.0,
        status="in_stock",
        storage_location="store",
        quantity=1
    )
    db_session.add(p)
    db_session.commit()
    prod_id = p.id

    # Verify no external listing exists yet
    ext = db_session.query(models.ProductExternalListing).filter(
        models.ProductExternalListing.external_item_id == avito_id
    ).first()
    assert ext is None

    # Now import from Avito with this ID
    payload = {
        "account_key": "acc_main",
        "external_item_id": avito_id,
        "external_url": f"https://www.avito.ru/item/{avito_id}",
        "remote_status": "active",
        "title": "Обновленный через Авито товар",
        "price": 8500.0,
        "description": "Описание получено с Авито",
        "parameters": {}
    }

    res = client.post("/api/integrations/avito/import-item", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == prod_id  # Matched existing product!

    db_session.expire_all()
    # Verify product was updated and NOT duplicated
    prods = db_session.query(models.Product).filter(models.Product.sku == sku).all()
    assert len(prods) == 1
    assert prods[0].id == prod_id
    assert prods[0].title == "Обновленный через Авито товар"
    assert prods[0].sale_price == 8500.0

    # Verify external listing was healed and linked to the existing product
    ext = db_session.query(models.ProductExternalListing).filter(
        models.ProductExternalListing.external_item_id == avito_id
    ).first()
    assert ext is not None
    assert ext.product_id == prod_id
