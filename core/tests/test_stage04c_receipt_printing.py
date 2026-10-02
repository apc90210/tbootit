"""
Stage 04C - Core Receipt Printing Tests.
Verifies Section 12 requirements:
- known completed sale -> print document 200;
- correct content type (application/pdf);
- PDF/header signature valid;
- document is non-empty;
- receipt number matches sale;
- total matches sale;
- payment method matches sale;
- item snapshot matches sale_items;
- quantity/price match sale snapshot;
- terms/signature section present according to canonical template;
- unknown sale -> 404;
- printing endpoint does not create sale;
- printing endpoint does not alter stock;
- printing endpoint does not create stock movement;
- repeated print fetch is safe/read-only;
- desktop receipt rendering regression remains PASS.
"""

import sys
import os
import io
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
import pypdf

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_test_sale():
    """Sets up an isolated completed sale and organization settings for printing tests."""
    db = SessionLocal()
    try:
        # Ensure org settings exist
        org = db.query(models.OrganizationSettings).first()
        if not org:
            org = models.OrganizationSettings(
                organization_name="ООО ТЕХНОРЕБУТ ТЕСТ",
                inn="7701987654",
                address="г. Москва, ул. Тестовая, д. 1",
                phone="+7 (495) 123-45-67",
                default_cashier_name="Старший кассир",
                default_customer_label="Розничный покупатель",
                warranty_text="Гарантийное обслуживание осуществляется в авторизованном СЦ.",
                no_warranty_text="Товар продается как есть.",
            )
            db.add(org)
            db.commit()
            db.refresh(org)
        else:
            org.organization_name = "ООО ТЕХНОРЕБУТ ТЕСТ"
            org.inn = "7701987654"
            org.default_cashier_name = "Старший кассир"
            org.default_customer_label = "Розничный покупатель"
            db.commit()

        # Create a test product
        product = models.Product(
            title="Тестовый смартфон SuperPhone 128GB",
            sku="TEST-PRINT-SP-01",
            barcode="4601234567890",
            quantity=10,
            sale_price=Decimal("15000.00"),
            status="active",
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Create a completed sale
        sale = models.Sale(
            total_amount=Decimal("15000.00"),
            payment_method="cash",
            status="completed",
            warranty_enabled=True,
            warranty_days=45,
        )
        db.add(sale)
        db.commit()
        db.refresh(sale)

        sale_item = models.SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            title=product.title,
            quantity=1,
            price=Decimal("15000.00"),
        )
        db.add(sale_item)
        db.commit()

        yield {
            "sale_id": sale.id,
            "product_id": product.id,
            "product_title": product.title,
            "price": 15000.0,
            "quantity": 1,
            "payment_method": "cash",
            "cashier_name": "Кассир Иван",
            "warranty_days": 45,
        }
    finally:
        db.close()


def test_01_known_completed_sale_print_200(setup_test_sale):
    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    assert resp.status_code == 200


def test_02_correct_content_type(setup_test_sale):
    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert f'receipt_{sale_id}.pdf' in resp.headers.get("content-disposition", "")


def test_03_pdf_header_and_signature_valid(setup_test_sale):
    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    assert resp.content.startswith(b"%PDF-")


def test_04_document_is_non_empty(setup_test_sale):
    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    assert len(resp.content) > 5000  # valid PDF with embedded fonts is tens of kilobytes


def test_05_receipt_number_matches_sale(setup_test_sale):
    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    reader = pypdf.PdfReader(io.BytesIO(resp.content))
    text = reader.pages[0].extract_text()
    assert f"Товарный чек № {sale_id}" in text


def test_06_total_matches_sale(setup_test_sale):
    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    reader = pypdf.PdfReader(io.BytesIO(resp.content))
    text = reader.pages[0].extract_text()
    assert "15000.00" in text
    assert "Итого:" in text
    assert "К оплате:" in text


def test_07_payment_method_matches_sale(setup_test_sale):
    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    reader = pypdf.PdfReader(io.BytesIO(resp.content))
    text = reader.pages[0].extract_text()
    assert "Наличные" in text


def test_08_item_snapshot_matches_sale_items(setup_test_sale):
    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    reader = pypdf.PdfReader(io.BytesIO(resp.content))
    text = reader.pages[0].extract_text()
    assert "Тестовый смартфон SuperPhone" in text


def test_09_quantity_and_price_match_sale_snapshot(setup_test_sale):
    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    reader = pypdf.PdfReader(io.BytesIO(resp.content))
    text = reader.pages[0].extract_text()
    assert "15000.00" in text
    assert "шт" in text


def test_10_terms_and_signature_section_present(setup_test_sale):
    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    reader = pypdf.PdfReader(io.BytesIO(resp.content))
    text = reader.pages[0].extract_text()
    assert "Гарантийные условия" in text
    assert "45 дней" in text
    assert "Отпустил:" in text
    assert "Покупатель:" in text
    assert "Подпись покупателя:" in text


def test_11_unknown_sale_returns_404():
    resp = client.get("/api/sales/99999999/receipt/print")
    assert resp.status_code == 404


def test_16_printing_endpoint_does_not_create_sale(setup_test_sale):
    db = SessionLocal()
    count_before = db.query(models.Sale).count()
    db.close()

    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    assert resp.status_code == 200

    db = SessionLocal()
    count_after = db.query(models.Sale).count()
    db.close()

    assert count_before == count_after


def test_17_printing_endpoint_does_not_alter_stock(setup_test_sale):
    db = SessionLocal()
    prod_before = db.query(models.Product).filter(models.Product.id == setup_test_sale["product_id"]).first()
    stock_before = prod_before.quantity
    db.close()

    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    assert resp.status_code == 200

    db = SessionLocal()
    prod_after = db.query(models.Product).filter(models.Product.id == setup_test_sale["product_id"]).first()
    stock_after = prod_after.quantity
    db.close()

    assert stock_before == stock_after


def test_18_printing_endpoint_does_not_create_stock_movement(setup_test_sale):
    db = SessionLocal()
    movements_before = db.query(models.StockMovement).count()
    db.close()

    sale_id = setup_test_sale["sale_id"]
    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    assert resp.status_code == 200

    db = SessionLocal()
    movements_after = db.query(models.StockMovement).count()
    db.close()

    assert movements_before == movements_after


def test_19_repeated_print_fetch_is_safe_and_readonly(setup_test_sale):
    sale_id = setup_test_sale["sale_id"]
    resp1 = client.get(f"/api/sales/{sale_id}/receipt/print")
    resp2 = client.get(f"/api/sales/{sale_id}/receipt/print")
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert len(resp1.content) == len(resp2.content)
