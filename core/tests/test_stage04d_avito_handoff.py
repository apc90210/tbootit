"""
Stage 04D - Core Avito Post-Sale Manual Handoff Tests.
Verifies Section 12 requirements:
- 1. sold product with active Avito listing + remaining stock 0 -> candidate returned;
- 2. sold product with no Avito listing -> no candidate;
- 3. remaining stock > 0 -> no removal candidate under default rule;
- 4. inactive/removed listing -> no candidate;
- 5. multi-item sale -> only eligible products returned;
- 6. historical sale lookup works;
- 7. unknown sale -> 404;
- 12. handoff fetch does not alter sale count;
- 13. handoff fetch does not alter stock;
- 14. handoff fetch does not alter stock movements;
- 15. handoff fetch does not alter external listing row/status;
- 16. no Avito API call occurs;
- 17. repeated fetch is read-only;
- 18. canonical listing URL returned unchanged.
"""

import sys
import os
import pytest
from decimal import Decimal
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
from app.database import get_db, SessionLocal
from app import models

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_stage04d_data():
    """Sets up isolated products, listings, and sales for Stage 04D tests."""
    db = SessionLocal()
    try:
        # Product 1: Stock 0, active Avito listing -> ELIGIBLE
        p1 = models.Product(
            title="Тестовый МФУ Со Складом 0",
            sku="SKU-STAGE04D-01",
            barcode="4600000004011",
            sale_price=15000.0,
            quantity=0,
            status="out_of_stock"
        )
        db.add(p1)
        db.flush()

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

        # Product 2: Stock 0, NO Avito listing -> NOT ELIGIBLE
        p2 = models.Product(
            title="Тестовый Картридж Без Авито",
            sku="SKU-STAGE04D-02",
            barcode="4600000004022",
            sale_price=2000.0,
            quantity=0,
            status="out_of_stock"
        )
        db.add(p2)
        db.flush()

        # Product 3: Stock 5 (> 0), active Avito listing -> NOT ELIGIBLE under stock=0 rule
        p3 = models.Product(
            title="Тестовый Монитор Со Складом 5",
            sku="SKU-STAGE04D-03",
            barcode="4600000004033",
            sale_price=8000.0,
            quantity=5,
            status="in_stock"
        )
        db.add(p3)
        db.flush()

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

        # Product 4: Stock 0, archived/inactive Avito listing -> NOT ELIGIBLE
        p4 = models.Product(
            title="Тестовый Ноутбук С Архивом",
            sku="SKU-STAGE04D-04",
            barcode="4600000004044",
            sale_price=25000.0,
            quantity=0,
            status="out_of_stock"
        )
        db.add(p4)
        db.flush()

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

        # Sale 1: Only product 1 (Eligible single item)
        s1 = models.Sale(
            total_amount=15000.0,
            payment_method="cash",
            status="completed"
        )
        db.add(s1)
        db.flush()

        item1 = models.SaleItem(
            sale_id=s1.id,
            product_id=p1.id,
            title=p1.title,
            quantity=1,
            price=15000.0
        )
        db.add(item1)

        # Sale 2: Only product 2 (No listing)
        s2 = models.Sale(
            total_amount=2000.0,
            payment_method="card",
            status="completed"
        )
        db.add(s2)
        db.flush()

        item2 = models.SaleItem(
            sale_id=s2.id,
            product_id=p2.id,
            title=p2.title,
            quantity=1,
            price=2000.0
        )
        db.add(item2)

        # Sale 3: Only product 3 (Stock > 0)
        s3 = models.Sale(
            total_amount=8000.0,
            payment_method="cash",
            status="completed"
        )
        db.add(s3)
        db.flush()

        item3 = models.SaleItem(
            sale_id=s3.id,
            product_id=p3.id,
            title=p3.title,
            quantity=1,
            price=8000.0
        )
        db.add(item3)

        # Sale 4: Only product 4 (Archived listing)
        s4 = models.Sale(
            total_amount=25000.0,
            payment_method="cash",
            status="completed"
        )
        db.add(s4)
        db.flush()

        item4 = models.SaleItem(
            sale_id=s4.id,
            product_id=p4.id,
            title=p4.title,
            quantity=1,
            price=25000.0
        )
        db.add(item4)

        # Sale 5: Multi-item sale (p1: eligible, p2: no listing, p3: stock>0, p4: archived)
        s5 = models.Sale(
            total_amount=50000.0,
            payment_method="card",
            status="completed"
        )
        db.add(s5)
        db.flush()

        db.add(models.SaleItem(sale_id=s5.id, product_id=p1.id, title=p1.title, quantity=1, price=15000.0))
        db.add(models.SaleItem(sale_id=s5.id, product_id=p2.id, title=p2.title, quantity=1, price=2000.0))
        db.add(models.SaleItem(sale_id=s5.id, product_id=p3.id, title=p3.title, quantity=1, price=8000.0))
        db.add(models.SaleItem(sale_id=s5.id, product_id=p4.id, title=p4.title, quantity=1, price=25000.0))

        # Historical Sale (Sale 6 equivalent): Completed earlier
        s6 = models.Sale(
            total_amount=15000.0,
            payment_method="card",
            status="completed"
        )
        db.add(s6)
        db.flush()
        db.add(models.SaleItem(sale_id=s6.id, product_id=p1.id, title=p1.title, quantity=1, price=15000.0))

        db.commit()

        yield {
            "p1_id": p1.id,
            "p2_id": p2.id,
            "p3_id": p3.id,
            "p4_id": p4.id,
            "s1_id": s1.id,
            "s2_id": s2.id,
            "s3_id": s3.id,
            "s4_id": s4.id,
            "s5_id": s5.id,
            "s6_id": s6.id,
            "listing1_url": listing1.external_url,
            "listing1_id": listing1.external_item_id
        }

    finally:
        # Cleanup test entities
        try:
            db.query(models.SaleItem).filter(models.SaleItem.sale_id.in_([s1.id, s2.id, s3.id, s4.id, s5.id, s6.id])).delete(synchronize_session=False)
            db.query(models.Sale).filter(models.Sale.id.in_([s1.id, s2.id, s3.id, s4.id, s5.id, s6.id])).delete(synchronize_session=False)
            db.query(models.ProductExternalListing).filter(models.ProductExternalListing.product_id.in_([p1.id, p2.id, p3.id, p4.id])).delete(synchronize_session=False)
            db.query(models.Product).filter(models.Product.id.in_([p1.id, p2.id, p3.id, p4.id])).delete(synchronize_session=False)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


def test_01_active_listing_zero_stock_returns_candidate(setup_stage04d_data):
    """Section 12.1: Sold product with active Avito listing + remaining stock 0 -> candidate returned."""
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
    assert item["remaining_stock"] == 0
    assert item["needs_manual_avito_removal"] is True
    assert item["listing_id"] == listing1_id
    assert item["listing_url"] == listing1_url


def test_02_product_with_no_avito_listing_omitted(setup_stage04d_data):
    """Section 12.2: Sold product with no Avito listing -> no candidate."""
    s2_id = setup_stage04d_data["s2_id"]

    resp = client.get(f"/api/sales/{s2_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sale_id"] == s2_id
    assert len(data["items"]) == 0


def test_03_remaining_stock_greater_than_zero_omitted(setup_stage04d_data):
    """Section 12.3: Remaining stock > 0 -> no removal candidate under default rule."""
    s3_id = setup_stage04d_data["s3_id"]

    resp = client.get(f"/api/sales/{s3_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sale_id"] == s3_id
    assert len(data["items"]) == 0


def test_04_inactive_or_removed_listing_omitted(setup_stage04d_data):
    """Section 12.4: Inactive/removed listing -> no candidate."""
    s4_id = setup_stage04d_data["s4_id"]

    resp = client.get(f"/api/sales/{s4_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sale_id"] == s4_id
    assert len(data["items"]) == 0


def test_05_multi_item_sale_filters_only_eligible_products(setup_stage04d_data):
    """Section 12.5: Multi-item sale -> only eligible products returned."""
    s5_id = setup_stage04d_data["s5_id"]
    p1_id = setup_stage04d_data["p1_id"]

    resp = client.get(f"/api/sales/{s5_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sale_id"] == s5_id
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == p1_id
    assert data["items"][0]["needs_manual_avito_removal"] is True


def test_06_historical_sale_lookup_works(setup_stage04d_data):
    """Section 12.6: Historical sale lookup works."""
    s6_id = setup_stage04d_data["s6_id"]
    p1_id = setup_stage04d_data["p1_id"]
    listing1_id = setup_stage04d_data["listing1_id"]

    resp = client.get(f"/api/sales/{s6_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()

    assert data["sale_id"] == s6_id
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == p1_id
    assert data["items"][0]["remaining_stock"] == 0
    assert data["items"][0]["listing_id"] == listing1_id
    assert "avito.ru" in data["items"][0]["listing_url"]


def test_07_unknown_sale_returns_404():
    """Section 12.7: Unknown sale -> 404."""
    resp = client.get("/api/sales/999999/avito-handoff")
    assert resp.status_code == 404


def test_12_to_15_read_only_invariants(setup_stage04d_data):
    """
    Sections 12.12, 12.13, 12.14, 12.15:
    Handoff fetch does NOT alter sale count, stock, stock movements, or external listing row/status.
    """
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


def test_16_no_avito_api_call_occurs(setup_stage04d_data, monkeypatch):
    """Section 12.16: No Avito API call occurs."""
    # Poison any potential network call
    def fail_call(*args, **kwargs):
        raise RuntimeError("Avito network call attempted!")

    monkeypatch.setattr("urllib.request.urlopen", fail_call)
    
    s1_id = setup_stage04d_data["s1_id"]
    resp = client.get(f"/api/sales/{s1_id}/avito-handoff")
    assert resp.status_code == 200


def test_17_repeated_fetch_is_read_only(setup_stage04d_data):
    """Section 12.17: Repeated fetch is safe and read-only."""
    s1_id = setup_stage04d_data["s1_id"]
    res1 = client.get(f"/api/sales/{s1_id}/avito-handoff").json()
    res2 = client.get(f"/api/sales/{s1_id}/avito-handoff").json()
    res3 = client.get(f"/api/sales/{s1_id}/avito-handoff").json()
    assert res1 == res2 == res3


def test_18_canonical_listing_url_returned_unchanged(setup_stage04d_data):
    """Section 12.18: Canonical listing URL returned unchanged."""
    s1_id = setup_stage04d_data["s1_id"]
    listing1_url = setup_stage04d_data["listing1_url"]

    resp = client.get(f"/api/sales/{s1_id}/avito-handoff")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"][0]["listing_url"] == listing1_url
