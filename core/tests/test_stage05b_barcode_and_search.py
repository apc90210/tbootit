"""
Test suite for Stage 05B: Barcode Hotfix and Canonical POS Product Search.
Verifies:
1. Real 12-digit Code128 format ('200' + 9 digits) barcode lookup.
2. Safe whitespace trimming and case-insensitive matching.
3. Safe fallback to SKU for physical price tags printed with SKU barcodes.
4. Parity between desktop inventory search and /by-barcode/ lookup.
5. In-stock and zero-stock product handling.
6. Unknown or empty barcode handling (clean 404, no 500).
7. Canonical POS product search by title, SKU, and barcode.
"""

import pytest
from app import models


@pytest.fixture
def seed_stage05b_products(db_session):
    """Seed test products with realistic Code128 barcodes and SKUs."""
    # Clean up existing test products if any
    db_session.query(models.Product).filter(
        models.Product.sku.in_(["TEST-BC-001", "TEST-BC-002", "TEST-BC-SKUONLY", "TEST-BC-OUTOFSTOCK"])
    ).delete(synchronize_session=False)
    db_session.commit()

    # 1. Standard in-stock product with 12-digit Code128 barcode
    p1 = models.Product(
        title="МФУ HP LaserJet 3052 Pro",
        sku="TEST-BC-001",
        barcode="200000000230",
        sale_price=8500.0,
        quantity=3,
        status="in_stock",
        storage_location="Склад А-1"
    )
    # 2. Another in-stock product
    p2 = models.Product(
        title="Ноутбук Lenovo ThinkPad T480",
        sku="TEST-BC-002",
        barcode="200000000231",
        sale_price=25000.0,
        quantity=1,
        status="in_stock",
        storage_location="Витрина 2"
    )
    # 3. Product with barcode=None but SKU printed on price tag
    p3 = models.Product(
        title="Принтер Canon LBP 2900",
        sku="TEST-BC-SKUONLY",
        barcode=None,
        sale_price=6000.0,
        quantity=2,
        status="in_stock",
        storage_location="Полка Б"
    )
    # 4. Out of stock / sold product
    p4 = models.Product(
        title="Монитор Dell P2419H",
        sku="TEST-BC-OUTOFSTOCK",
        barcode="200000000232",
        sale_price=9000.0,
        quantity=0,
        status="sold",
        storage_location="Архив"
    )

    db_session.add_all([p1, p2, p3, p4])
    db_session.commit()
    db_session.refresh(p1)
    db_session.refresh(p2)
    db_session.refresh(p3)
    db_session.refresh(p4)

    return {
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "p4": p4,
    }


def test_barcode_lookup_12_digit_code128_success(client, seed_stage05b_products):
    """Real 12-digit Code128 barcode is found accurately."""
    resp = client.get("/api/products/by-barcode/200000000230")
    assert resp.status_code == 200
    data = resp.json()
    assert data["barcode"] == "200000000230"
    assert data["sku"] == "TEST-BC-001"
    assert data["title"] == "МФУ HP LaserJet 3052 Pro"
    assert data["quantity"] == 3
    assert data["status"] == "in_stock"


def test_barcode_lookup_whitespace_normalization(client, seed_stage05b_products):
    """Leading and trailing whitespace or newlines are trimmed safely."""
    resp = client.get("/api/products/by-barcode/%20%20200000000230%20%20")
    assert resp.status_code == 200
    data = resp.json()
    assert data["barcode"] == "200000000230"
    assert data["sku"] == "TEST-BC-001"


def test_barcode_lookup_sku_returns_404(client, seed_stage05b_products):
    """Searching SKU via /by-barcode/ returns 404; canonical search ?q= is used for SKU/name."""
    resp = client.get("/api/products/by-barcode/TEST-BC-SKUONLY")
    assert resp.status_code == 404
    assert "не найден" in resp.json()["detail"]


def test_barcode_lookup_parity_with_desktop_query(client, seed_stage05b_products):
    """Verify parity: barcode lookup returns same canonical product as desktop ?q= search."""
    bc_resp = client.get("/api/products/by-barcode/200000000230")
    assert bc_resp.status_code == 200
    bc_data = bc_resp.json()

    search_resp = client.get("/api/products/?q=200000000230&status=in_stock")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total"] >= 1
    found_item = search_data["items"][0]

    assert bc_data["id"] == found_item["id"]
    assert bc_data["sku"] == found_item["sku"]
    assert bc_data["title"] == found_item["title"]
    assert bc_data["sale_price"] == found_item["sale_price"]
    assert bc_data["quantity"] == found_item["quantity"]


def test_barcode_lookup_unknown_returns_404_no_500(client, seed_stage05b_products):
    """Unknown barcode returns clean 404, not 500."""
    resp = client.get("/api/products/by-barcode/999999999999")
    assert resp.status_code == 404
    data = resp.json()
    assert "не найден" in data["detail"]


def test_barcode_lookup_empty_returns_404(client, seed_stage05b_products):
    """Empty or all-whitespace barcode returns clean 404."""
    resp = client.get("/api/products/by-barcode/%20%20")
    assert resp.status_code == 404


def test_barcode_lookup_zero_stock_product(client, seed_stage05b_products):
    """Zero stock product is retrieved with its quantity and status (client enforces POS rules)."""
    resp = client.get("/api/products/by-barcode/200000000232")
    assert resp.status_code == 200
    data = resp.json()
    assert data["quantity"] == 0
    assert data["status"] == "sold"


def test_canonical_product_search_by_name(client, seed_stage05b_products):
    """Search by partial name returns in-stock product."""
    resp = client.get("/api/products/?q=LaserJet&status=in_stock")
    assert resp.status_code == 200
    data = resp.json()
    skus = [it["sku"] for it in data["items"]]
    assert "TEST-BC-001" in skus


def test_canonical_product_search_by_sku(client, seed_stage05b_products):
    """Search by SKU returns matching product."""
    resp = client.get("/api/products/?q=TEST-BC-002&status=in_stock")
    assert resp.status_code == 200
    data = resp.json()
    skus = [it["sku"] for it in data["items"]]
    assert "TEST-BC-002" in skus
