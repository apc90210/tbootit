"""
Stage 04D R2 - Core Avito Post-Sale Manual Handoff Tests.
Verifies Section 10 requirements:
- 1. active listing + stock 0 -> show;
- 2. active listing + stock >0 -> show;
- 3. removed/inactive listing + stock 0 -> show;
- 4. removed/inactive listing + stock >0 -> show;
- 5. no Avito reference -> hide;
- 6. new sale persists immutable Avito item snapshot;
- 7. new sale persists URL snapshot when available;
- 8. product/listing edited after sale -> receipt still uses sale snapshot;
- 9. legacy sale without snapshot -> current exact product mapping fallback works;
- 10. legacy sale with removed listing -> still returned;
- 11. multiple items -> each resolved independently;
- 12. malformed URL -> item ID returned but unsafe URL not launchable;
- 13. unknown sale -> 404;
- 14. repeated fetch is read-only;
- 15. no sale/stock/listing mutation.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
core_dir = os.path.join(project_root, "core")

for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        sys.modules.pop(k, None)

while core_dir in sys.path:
    sys.path.remove(core_dir)
sys.path.insert(0, core_dir)

from app.main import app
from app.database import SessionLocal
from app import models
from app.services import sale_service

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_stage04d_data():
    """Sets up isolated products, listings, and sales for Stage 04D R2 tests."""
    db = SessionLocal()
    created_sale_ids = []
    created_product_ids = []
    try:
        # Product 1: Stock 0, active Avito listing
        p1 = models.Product(
            title="Тестовый МФУ Со Складом 0",
            sku="SKU-STAGE04D-01",
            barcode="4600000004011",
            sale_price=15000.0,
            quantity=0,
            status="out_of_stock",
            storage_location="store"
        )
        db.add(p1)
        db.flush()
        created_product_ids.append(p1.id)

        listing1 = models.ProductExternalListing(
            product_id=p1.id,
            marketplace="avito",
            external_account_key="acc1",
            external_item_id="9000000001",
            external_url="https://www.avito.ru/ekaterinburg/orgtehnika/test_mfu_9000000001",
            remote_status="active",
            sync_state="synced"
        )
        db.add(listing1)

        # Product 2: Stock 0, NO Avito listing
        p2 = models.Product(
            title="Тестовый Картридж Без Авито",
            sku="SKU-STAGE04D-02",
            barcode="4600000004022",
            sale_price=2000.0,
            quantity=0,
            status="out_of_stock",
            storage_location="store"
        )
        db.add(p2)
        db.flush()
        created_product_ids.append(p2.id)

        # Product 3: Stock 5 (> 0), active Avito listing
        p3 = models.Product(
            title="Тестовый Монитор Со Складом 5",
            sku="SKU-STAGE04D-03",
            barcode="4600000004033",
            sale_price=8000.0,
            quantity=5,
            status="in_stock",
            storage_location="store"
        )
        db.add(p3)
        db.flush()
        created_product_ids.append(p3.id)

        listing3 = models.ProductExternalListing(
            product_id=p3.id,
            marketplace="avito",
            external_account_key="acc1",
            external_item_id="9000000003",
            external_url="https://www.avito.ru/ekaterinburg/monitory/test_mon_9000000003",
            remote_status="active",
            sync_state="synced"
        )
        db.add(listing3)

        # Product 4: Stock 0, archived/inactive Avito listing
        p4 = models.Product(
            title="Тестовый Ноутбук С Архивом",
            sku="SKU-STAGE04D-04",
            barcode="4600000004044",
            sale_price=25000.0,
            quantity=0,
            status="out_of_stock",
            storage_location="store"
        )
        db.add(p4)
        db.flush()
        created_product_ids.append(p4.id)

        listing4 = models.ProductExternalListing(
            product_id=p4.id,
            marketplace="avito",
            external_account_key="acc1",
            external_item_id="9000000004",
            external_url="https://www.avito.ru/ekaterinburg/noutbuki/test_nb_9000000004",
            remote_status="archived",
            sync_state="synced"
        )
        db.add(listing4)

        # Product 5: Stock 4 (> 0), removed/inactive Avito listing
        p5 = models.Product(
            title="Тестовый Системный Блок Снятый",
            sku="SKU-STAGE04D-05",
            barcode="4600000004055",
            sale_price=30000.0,
            quantity=4,
            status="in_stock",
            storage_location="store"
        )
        db.add(p5)
        db.flush()
        created_product_ids.append(p5.id)

        listing5 = models.ProductExternalListing(
            product_id=p5.id,
            marketplace="avito",
            external_account_key="acc1",
            external_item_id="9000000005",
            external_url="https://www.avito.ru/ekaterinburg/kompyutery/test_pc_9000000005",
            remote_status="removed",
            sync_state="synced"
        )
        db.add(listing5)

        # Product 6: Malformed / Unsafe URL
        p6 = models.Product(
            title="Тестовый Товар С Опасным URL",
            sku="SKU-STAGE04D-06",
            barcode="4600000004066",
            sale_price=1000.0,
            quantity=0,
            status="out_of_stock",
            storage_location="store"
        )
        db.add(p6)
        db.flush()
        created_product_ids.append(p6.id)

        listing6 = models.ProductExternalListing(
            product_id=p6.id,
            marketplace="avito",
            external_account_key="acc1",
            external_item_id="9000000006",
            external_url="http://unsafe-phishing.example.com/item/9000000006",
            remote_status="active",
            sync_state="synced"
        )
        db.add(listing6)

        # Product 7: New sale candidate with initial stock 10
        p7 = models.Product(
            title="Тестовый Планшет Для Продажи",
            sku="SKU-STAGE04D-07",
            barcode="4600000004077",
            sale_price=12000.0,
            quantity=10,
            status="in_stock",
            storage_location="store"
        )
        db.add(p7)
        db.flush()
        created_product_ids.append(p7.id)

        listing7 = models.ProductExternalListing(
            product_id=p7.id,
            marketplace="avito",
            external_account_key="acc1",
            external_item_id="9000000007",
            external_url="https://www.avito.ru/ekaterinburg/planshety/test_tab_9000000007",
            remote_status="active",
            sync_state="synced"
        )
        db.add(listing7)

        # Product 8: External listing with MISSING/NULL external_url (ID-only)
        p8 = models.Product(
            title="Тестовый Товар С Авито Без URL",
            sku="SKU-STAGE04D-08",
            barcode="4600000004088",
            sale_price=5000.0,
            quantity=2,
            status="in_stock",
            storage_location="store"
        )
        db.add(p8)
        db.flush()
        created_product_ids.append(p8.id)

        listing8 = models.ProductExternalListing(
            product_id=p8.id,
            marketplace="avito",
            external_account_key="acc1",
            external_item_id="9000000008",
            external_url=None,
            remote_status="active",
            sync_state="synced"
        )
        db.add(listing8)

        # Product 9: No external listing row, but has AVITO-<id> SKU convention
        p9 = models.Product(
            title="Тестовый Товар С Артикулом AVITO В SKU",
            sku="AVITO-9000000009",
            barcode="4600000004099",
            sale_price=7500.0,
            quantity=1,
            status="in_stock",
            storage_location="store"
        )
        db.add(p9)
        db.flush()
        created_product_ids.append(p9.id)

        # Sale 1: Only product 1 (active listing + stock 0)
        s1 = models.Sale(total_amount=15000.0, payment_method="cash", status="completed")
        db.add(s1)
        db.flush()
        created_sale_ids.append(s1.id)
        db.add(models.SaleItem(sale_id=s1.id, product_id=p1.id, title=p1.title, quantity=1, price=15000.0))

        # Sale 2: Only product 2 (no Avito listing)
        s2 = models.Sale(total_amount=2000.0, payment_method="card", status="completed")
        db.add(s2)
        db.flush()
        created_sale_ids.append(s2.id)
        db.add(models.SaleItem(sale_id=s2.id, product_id=p2.id, title=p2.title, quantity=1, price=2000.0))

        # Sale 3: Only product 3 (active listing + stock > 0)
        s3 = models.Sale(total_amount=8000.0, payment_method="card", status="completed")
        db.add(s3)
        db.flush()
        created_sale_ids.append(s3.id)
        db.add(models.SaleItem(sale_id=s3.id, product_id=p3.id, title=p3.title, quantity=1, price=8000.0))

        # Sale 4: Only product 4 (removed/archived listing + stock 0)
        s4 = models.Sale(total_amount=25000.0, payment_method="cash", status="completed")
        db.add(s4)
        db.flush()
        created_sale_ids.append(s4.id)
        db.add(models.SaleItem(sale_id=s4.id, product_id=p4.id, title=p4.title, quantity=1, price=25000.0))

        # Sale 4b: Only product 5 (removed/inactive listing + stock > 0)
        s4b = models.Sale(total_amount=30000.0, payment_method="card", status="completed")
        db.add(s4b)
        db.flush()
        created_sale_ids.append(s4b.id)
        db.add(models.SaleItem(sale_id=s4b.id, product_id=p5.id, title=p5.title, quantity=1, price=30000.0))

        # Sale 5: Multi-item sale (p1: active stock 0, p2: no listing, p3: active stock 5, p4: archived stock 0)
        s5 = models.Sale(total_amount=50000.0, payment_method="card", status="completed")
        db.add(s5)
        db.flush()
        created_sale_ids.append(s5.id)
        db.add(models.SaleItem(sale_id=s5.id, product_id=p1.id, title=p1.title, quantity=1, price=15000.0))
        db.add(models.SaleItem(sale_id=s5.id, product_id=p2.id, title=p2.title, quantity=1, price=2000.0))
        db.add(models.SaleItem(sale_id=s5.id, product_id=p3.id, title=p3.title, quantity=1, price=8000.0))
        db.add(models.SaleItem(sale_id=s5.id, product_id=p4.id, title=p4.title, quantity=1, price=25000.0))

        # Sale 6: Malformed URL sale
        s6 = models.Sale(total_amount=1000.0, payment_method="cash", status="completed")
        db.add(s6)
        db.flush()
        created_sale_ids.append(s6.id)
        db.add(models.SaleItem(sale_id=s6.id, product_id=p6.id, title=p6.title, quantity=1, price=1000.0))

        # Sale 7: Legacy mapping ID + missing external_url (ID-only)
        s7 = models.Sale(total_amount=5000.0, payment_method="cash", status="completed")
        db.add(s7)
        db.flush()
        created_sale_ids.append(s7.id)
        db.add(models.SaleItem(sale_id=s7.id, product_id=p8.id, title=p8.title, quantity=1, price=5000.0))

        # Sale 8: Legacy ID via AVITO-<id> SKU + no listing
        s8 = models.Sale(total_amount=7500.0, payment_method="card", status="completed")
        db.add(s8)
        db.flush()
        created_sale_ids.append(s8.id)
        db.add(models.SaleItem(sale_id=s8.id, product_id=p9.id, title=p9.title, quantity=1, price=7500.0))

        # Sale 9: Multi-item mixed sale (p1: clickable, p8: ID-only, p2: non-Avito)
        s9 = models.Sale(total_amount=22000.0, payment_method="card", status="completed")
        db.add(s9)
        db.flush()
        created_sale_ids.append(s9.id)
        db.add(models.SaleItem(sale_id=s9.id, product_id=p1.id, title=p1.title, quantity=1, price=15000.0))
        db.add(models.SaleItem(sale_id=s9.id, product_id=p8.id, title=p8.title, quantity=1, price=5000.0))
        db.add(models.SaleItem(sale_id=s9.id, product_id=p2.id, title=p2.title, quantity=1, price=2000.0))

        db.commit()

        yield {
            "p1_id": p1.id,
            "p2_id": p2.id,
            "p3_id": p3.id,
            "p4_id": p4.id,
            "p5_id": p5.id,
            "p6_id": p6.id,
            "p7_id": p7.id,
            "p8_id": p8.id,
            "p9_id": p9.id,
            "s1_id": s1.id,
            "s2_id": s2.id,
            "s3_id": s3.id,
            "s4_id": s4.id,
            "s4b_id": s4b.id,
            "s5_id": s5.id,
            "s6_id": s6.id,
            "s7_id": s7.id,
            "s8_id": s8.id,
            "s9_id": s9.id,
            "listing1_url": listing1.external_url,
            "listing1_id": listing1.external_item_id,
            "listing3_id": listing3.external_item_id,
            "listing4_id": listing4.external_item_id,
            "listing5_id": listing5.external_item_id,
            "listing6_id": listing6.external_item_id,
            "listing8_id": listing8.external_item_id,
            "created_sale_ids": created_sale_ids,
            "created_product_ids": created_product_ids
        }


    finally:
        try:
            db.query(models.SaleItem).filter(models.SaleItem.sale_id.in_(created_sale_ids)).delete(synchronize_session=False)
            db.query(models.Sale).filter(models.Sale.id.in_(created_sale_ids)).delete(synchronize_session=False)
            db.query(models.ProductExternalListing).filter(models.ProductExternalListing.product_id.in_(created_product_ids)).delete(synchronize_session=False)
            db.query(models.Product).filter(models.Product.id.in_(created_product_ids)).delete(synchronize_session=False)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


def test_01_active_listing_stock_zero_shows(setup_stage04d_data):
    """Section 10.1: active listing + stock 0 -> show."""
    s1_id = setup_stage04d_data["s1_id"]
    p1_id = setup_stage04d_data["p1_id"]
    listing1_id = setup_stage04d_data["listing1_id"]
    listing1_url = setup_stage04d_data["listing1_url"]

    resp = client.get(f"/api/sales/{s1_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sale_id"] == s1_id
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["product_id"] == p1_id
    assert item["avito_item_id"] == listing1_id
    assert item["can_open_avito"] is True
    assert item["listing_url"] == listing1_url
    assert item["remaining_stock"] == 0
    assert item["remote_status"] == "active"


def test_02_active_listing_stock_greater_than_zero_shows(setup_stage04d_data):
    """Section 10.2: active listing + stock >0 -> show."""
    s3_id = setup_stage04d_data["s3_id"]
    p3_id = setup_stage04d_data["p3_id"]
    listing3_id = setup_stage04d_data["listing3_id"]

    resp = client.get(f"/api/sales/{s3_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sale_id"] == s3_id
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["product_id"] == p3_id
    assert item["avito_item_id"] == listing3_id
    assert item["can_open_avito"] is True
    assert item["remaining_stock"] == 5
    assert item["remote_status"] == "active"


def test_03_removed_inactive_listing_stock_zero_shows(setup_stage04d_data):
    """Section 10.3: removed/inactive listing + stock 0 -> show."""
    s4_id = setup_stage04d_data["s4_id"]
    p4_id = setup_stage04d_data["p4_id"]
    listing4_id = setup_stage04d_data["listing4_id"]

    resp = client.get(f"/api/sales/{s4_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sale_id"] == s4_id
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["product_id"] == p4_id
    assert item["avito_item_id"] == listing4_id
    assert item["can_open_avito"] is True
    assert item["remaining_stock"] == 0
    assert item["remote_status"] == "archived"


def test_04_removed_inactive_listing_stock_greater_than_zero_shows(setup_stage04d_data):
    """Section 10.4: removed/inactive listing + stock >0 -> show."""
    s4b_id = setup_stage04d_data["s4b_id"]
    p5_id = setup_stage04d_data["p5_id"]
    listing5_id = setup_stage04d_data["listing5_id"]

    resp = client.get(f"/api/sales/{s4b_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sale_id"] == s4b_id
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["product_id"] == p5_id
    assert item["avito_item_id"] == listing5_id
    assert item["can_open_avito"] is True
    assert item["remaining_stock"] == 4
    assert item["remote_status"] == "removed"


def test_05_no_avito_reference_hides(setup_stage04d_data):
    """Section 10.5: no Avito reference -> hide."""
    s2_id = setup_stage04d_data["s2_id"]

    resp = client.get(f"/api/sales/{s2_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sale_id"] == s2_id
    assert len(data["items"]) == 0


def test_06_and_07_new_sale_persists_immutable_avito_snapshot(setup_stage04d_data):
    """
    Section 10.6 & 10.7:
    New sale persists immutable Avito item snapshot and URL snapshot when available.
    """
    db = SessionLocal()
    p7_id = setup_stage04d_data["p7_id"]
    try:
        new_sale, _ = sale_service.execute_canonical_sale(
            db=db,
            items_data=[{"product_id": p7_id, "quantity": 1, "price": 12000.0, "title": "Планшет"}],
            payment_method="cash",
            customer_id=None,
            cashier_name="Кассир Тест"
        )
        setup_stage04d_data["created_sale_ids"].append(new_sale.id)

        # Inspect persisted SaleItem snapshot in DB
        sale_item = db.query(models.SaleItem).filter(models.SaleItem.sale_id == new_sale.id).first()
        assert sale_item is not None
        assert sale_item.avito_item_id == "9000000007"
        assert sale_item.avito_listing_url == "https://www.avito.ru/ekaterinburg/planshety/test_tab_9000000007"

        # Verify handoff endpoint returns it with source_of_linkage == "sale_snapshot"
        resp = client.get(f"/api/sales/{new_sale.id}/avito-handoff")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["avito_item_id"] == "9000000007"
        assert data["items"][0]["listing_url"] == "https://www.avito.ru/ekaterinburg/planshety/test_tab_9000000007"
        assert data["items"][0]["source_of_linkage"] == "sale_snapshot"
        assert data["items"][0]["can_open_avito"] is True

    finally:
        db.close()


def test_08_product_listing_edited_after_sale_receipt_still_uses_snapshot(setup_stage04d_data):
    """
    Section 10.8:
    product/listing edited after sale -> receipt still uses sale snapshot.
    """
    db = SessionLocal()
    p7_id = setup_stage04d_data["p7_id"]
    try:
        # Create a sale with snapshot
        sale, _ = sale_service.execute_canonical_sale(
            db=db,
            items_data=[{"product_id": p7_id, "quantity": 1, "price": 12000.0, "title": "Планшет До Редактирования"}],
            payment_method="card",
            cashier_name="Кассир Тест"
        )
        setup_stage04d_data["created_sale_ids"].append(sale.id)

        # Now edit/archive the product listing in catalog AFTER the sale
        listing = db.query(models.ProductExternalListing).filter(models.ProductExternalListing.product_id == p7_id).first()
        assert listing is not None
        listing.external_item_id = "CHANGED_ITEM_ID_9999"
        listing.external_url = "https://www.avito.ru/changed_url_9999"
        listing.remote_status = "closed"
        db.commit()

        # Receipt must STILL return original snapshot values!
        resp = client.get(f"/api/sales/{sale.id}/avito-handoff")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["avito_item_id"] == "9000000007"
        assert item["listing_url"] == "https://www.avito.ru/ekaterinburg/planshety/test_tab_9000000007"
        assert item["source_of_linkage"] == "sale_snapshot"

    finally:
        db.close()


def test_09_legacy_sale_without_snapshot_uses_current_product_mapping(setup_stage04d_data):
    """
    Section 10.9:
    legacy sale without snapshot -> current exact product mapping fallback works.
    """
    s1_id = setup_stage04d_data["s1_id"]
    listing1_id = setup_stage04d_data["listing1_id"]

    resp = client.get(f"/api/sales/{s1_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["avito_item_id"] == listing1_id
    assert item["source_of_linkage"] == "current_product_mapping"


def test_10_legacy_sale_with_removed_listing_still_returned(setup_stage04d_data):
    """
    Section 10.10:
    legacy sale with removed listing -> still returned.
    """
    s4_id = setup_stage04d_data["s4_id"]
    listing4_id = setup_stage04d_data["listing4_id"]

    resp = client.get(f"/api/sales/{s4_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["avito_item_id"] == listing4_id
    assert item["remote_status"] == "archived"
    assert item["can_open_avito"] is True


def test_11_multiple_items_each_resolved_independently(setup_stage04d_data):
    """
    Section 10.11:
    multiple items -> each resolved independently.
    Sale 5 contains:
    - p1: active, stock 0 -> eligible
    - p2: no Avito listing -> omitted
    - p3: active, stock 5 -> eligible
    - p4: archived, stock 0 -> eligible
    Expected: exactly 3 items returned, each with its own independent IDs and URLs.
    """
    s5_id = setup_stage04d_data["s5_id"]
    p1_id = setup_stage04d_data["p1_id"]
    p3_id = setup_stage04d_data["p3_id"]
    p4_id = setup_stage04d_data["p4_id"]

    resp = client.get(f"/api/sales/{s5_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sale_id"] == s5_id
    assert len(data["items"]) == 3
    ret_product_ids = {it["product_id"] for it in data["items"]}
    assert ret_product_ids == {p1_id, p3_id, p4_id}

    for it in data["items"]:
        assert it["can_open_avito"] is True
        assert it["avito_item_id"] is not None
        assert "avito.ru" in it["listing_url"]


def test_12_malformed_url_item_id_returned_but_unsafe_url_not_launchable(setup_stage04d_data):
    """
    Section 10.12:
    malformed URL -> item ID returned but unsafe URL not launchable.
    Product 6 has external_item_id="9000000006", but external_url is "http://unsafe-phishing.example.com/...".
    Server must return the avito_item_id, but can_open_avito must be False and listing_url must be blocked/empty.
    """
    s6_id = setup_stage04d_data["s6_id"]
    p6_id = setup_stage04d_data["p6_id"]

    resp = client.get(f"/api/sales/{s6_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["product_id"] == p6_id
    assert item["avito_item_id"] == "9000000006"
    assert item["can_open_avito"] is False
    assert "unsafe-phishing" not in item["listing_url"]


def test_13_unknown_sale_returns_404():
    """Section 10.13: unknown sale -> 404."""
    resp = client.get("/api/sales/999999/avito-handoff")
    assert resp.status_code == 404


def test_14_repeated_fetch_is_read_only(setup_stage04d_data):
    """Section 10.14: repeated fetch is read-only."""
    s1_id = setup_stage04d_data["s1_id"]
    res1 = client.get(f"/api/sales/{s1_id}/avito-handoff").json()
    res2 = client.get(f"/api/sales/{s1_id}/avito-handoff").json()
    res3 = client.get(f"/api/sales/{s1_id}/avito-handoff").json()
    assert res1 == res2 == res3


def test_15_no_sale_stock_or_listing_mutation(setup_stage04d_data, monkeypatch):
    """
    Section 10.15:
    no sale/stock/listing mutation and no Avito API call occurs.
    """
    def fail_call(*args, **kwargs):
        raise RuntimeError("Avito network call attempted!")

    monkeypatch.setattr("urllib.request.urlopen", fail_call)

    db = SessionLocal()
    try:
        sales_before = db.query(models.Sale).count()
        sale_items_before = db.query(models.SaleItem).count()
        movements_before = db.query(models.StockMovement).count()
        listings_before = db.query(models.ProductExternalListing).count()

        p1 = db.query(models.Product).filter(models.Product.id == setup_stage04d_data["p1_id"]).first()
        stock_before = p1.quantity

        l1 = db.query(models.ProductExternalListing).filter(models.ProductExternalListing.product_id == p1.id).first()
        status_before = l1.remote_status

        # Perform handoff fetch
        s1_id = setup_stage04d_data["s1_id"]
        resp = client.get(f"/api/sales/{s1_id}/avito-handoff")
        assert resp.status_code == 200

        # Verify DB state strictly unchanged
        sales_after = db.query(models.Sale).count()
        sale_items_after = db.query(models.SaleItem).count()
        movements_after = db.query(models.StockMovement).count()
        listings_after = db.query(models.ProductExternalListing).count()

        p1_after = db.query(models.Product).filter(models.Product.id == setup_stage04d_data["p1_id"]).first()
        stock_after = p1_after.quantity

        l1_after = db.query(models.ProductExternalListing).filter(models.ProductExternalListing.product_id == p1.id).first()
        status_after = l1_after.remote_status

        assert sales_after == sales_before
        assert sale_items_after == sale_items_before
        assert movements_after == movements_before
        assert listings_after == listings_before
        assert stock_after == stock_before
        assert status_after == status_before

    finally:
        db.close()


def test_16_snapshot_id_with_no_url_article_visible_not_clickable(setup_stage04d_data):
    """
    Stage 04D R2B (1 & 2):
    Snapshot ID + no URL -> article visible, can_open_avito = False, listing_url = "".
    """
    db = SessionLocal()
    p1_id = setup_stage04d_data["p1_id"]
    try:
        # Create sale item directly with snapshot item ID but NO URL
        s_custom = models.Sale(total_amount=5000.0, payment_method="cash", status="completed")
        db.add(s_custom)
        db.flush()
        setup_stage04d_data["created_sale_ids"].append(s_custom.id)

        db.add(models.SaleItem(
            sale_id=s_custom.id,
            product_id=p1_id,
            title="Товар Со Снапшотом Без URL",
            quantity=1,
            price=5000.0,
            avito_item_id="999888777",
            avito_listing_url=None
        ))
        db.commit()

        resp = client.get(f"/api/sales/{s_custom.id}/avito-handoff")
        assert resp.status_code == 200
        data = resp.json()

        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["avito_item_id"] == "999888777"
        assert item["can_open_avito"] is False
        assert item["listing_url"] == "" or item["listing_url"] is None
        assert item["source_of_linkage"] == "sale_snapshot"

    finally:
        db.close()


def test_17_legacy_mapping_missing_external_url_article_visible_not_clickable(setup_stage04d_data):
    """
    Stage 04D R2B (3 & 4):
    Legacy mapping ID + missing external_url -> article visible, not clickable.
    Product 8 has external_item_id="9000000008", but external_url is NULL.
    """
    s7_id = setup_stage04d_data["s7_id"]
    p8_id = setup_stage04d_data["p8_id"]

    resp = client.get(f"/api/sales/{s7_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["product_id"] == p8_id
    assert item["avito_item_id"] == "9000000008"
    assert item["can_open_avito"] is False
    assert item["listing_url"] == "" or item["listing_url"] is None
    assert item["source_of_linkage"] == "current_product_mapping"


def test_18_no_synthetic_url_fallback_remains(setup_stage04d_data):
    """
    Stage 04D R2B (10):
    No synthetic https://www.avito.ru/{id} fallback remains.
    Sale 8 has product 9 with SKU "AVITO-9000000009" and no external listing.
    The response MUST return avito_item_id="9000000009", can_open_avito=False,
    and MUST NOT synthesize "https://www.avito.ru/9000000009".
    """
    s8_id = setup_stage04d_data["s8_id"]
    p9_id = setup_stage04d_data["p9_id"]

    resp = client.get(f"/api/sales/{s8_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["product_id"] == p9_id
    assert item["avito_item_id"] == "9000000009"
    assert item["can_open_avito"] is False
    assert item["listing_url"] != "https://www.avito.ru/9000000009"
    assert item["listing_url"] == "" or item["listing_url"] is None


def test_19_multi_item_mixed_clickable_id_only_non_avito(setup_stage04d_data):
    """
    Stage 04D R2B (9):
    Multi-item mixed case:
    - p1: clickable (active, valid URL)
    - p8: ID-only (active, external_url is NULL)
    - p2: non-Avito (no listing, standard SKU)
    Expected: exactly 2 items returned.
    - p1: can_open_avito=True, valid URL
    - p8: can_open_avito=False, empty URL, avito_item_id="9000000008"
    - p2: omitted
    """
    s9_id = setup_stage04d_data["s9_id"]
    p1_id = setup_stage04d_data["p1_id"]
    p8_id = setup_stage04d_data["p8_id"]

    resp = client.get(f"/api/sales/{s9_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["items"]) == 2
    items_by_pid = {it["product_id"]: it for it in data["items"]}
    assert p1_id in items_by_pid
    assert p8_id in items_by_pid

    # p1 is clickable
    item1 = items_by_pid[p1_id]
    assert item1["can_open_avito"] is True
    assert item1["avito_item_id"] == "9000000001"
    assert item1["listing_url"] == "https://www.avito.ru/ekaterinburg/orgtehnika/test_mfu_9000000001"

    # p8 is ID-only
    item8 = items_by_pid[p8_id]
    assert item8["can_open_avito"] is False
    assert item8["avito_item_id"] == "9000000008"
    assert item8["listing_url"] == "" or item8["listing_url"] is None

