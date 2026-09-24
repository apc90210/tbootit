import os
import sys
import uuid
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
core_path = str(REPO_ROOT / "core")
inv_path = str(REPO_ROOT / "inventory-sales-module")
admin_path = str(REPO_ROOT / "admin-shell")

# Clean sys.modules to avoid collision
for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        sys.modules.pop(k, None)

if core_path in sys.path:
    sys.path.remove(core_path)
sys.path.insert(0, core_path)

from app.main import app as core_app
from app.database import SessionLocal, engine
from app import models
from sqlalchemy import text

core_client = TestClient(core_app)


def verify_db_integrity():
    with engine.connect() as conn:
        fk_errors = conn.execute(text("PRAGMA foreign_key_check")).fetchall()
        assert fk_errors == [], f"Foreign key check failed: {fk_errors}"
        quick_check = conn.execute(text("PRAGMA quick_check")).fetchall()
        assert quick_check == [("ok",)], f"Quick check failed: {quick_check}"


# ==============================================================================
# 1. UNICODE & CASE-INSENSITIVE SEARCH TESTS
# ==============================================================================

def test_cyrillic_case_insensitive_search():
    """Verify Cyrillic queries: 'монитор', 'Монитор', 'МОНИТОР', 'мОнИтОр' return identical results."""
    uid = uuid.uuid4().hex[:6]
    title = f"Игровой Монитор UltraSync {uid}"
    sku = f"МОН-{uid}"
    brand = f"БрендМонитор-{uid}"
    model_name = f"Модель-М-{uid}"

    with SessionLocal() as db:
        prod = models.Product(
            title=title,
            sku=sku,
            brand=brand,
            model=model_name,
            serial_number=f"СЕРИЯ-{uid}",
            sale_price=19990.0,
            quantity=5,
            status="in_stock",
            storage_location="store"
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        prod_id = prod.id

    casing_variants = ["монитор", "Монитор", "МОНИТОР", "мОнИтОр"]
    results_sets = []

    for query in casing_variants:
        resp = core_client.get(f"/api/products/?q={query}&limit=100")
        assert resp.status_code == 200
        items = resp.json()["items"]
        matching_ids = [item["id"] for item in items if item["id"] == prod_id]
        assert len(matching_ids) == 1, f"Product {prod_id} not found for query '{query}'"
        results_sets.append([item["id"] for item in items])

    # Verify identical result lists across all casing variants
    for res in results_sets[1:]:
        assert res == results_sets[0], "Casing variants returned divergent result lists"

    # Clean up test product
    with SessionLocal() as db:
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        if p:
            db.delete(p)
            db.commit()


def test_latin_case_insensitive_search():
    """Verify Latin queries: 'thinkpad', 'ThinkPad', 'THINKPAD', 'tHiNkPaD' return identical results."""
    uid = uuid.uuid4().hex[:6]
    title = f"Laptop ThinkPad T14s Gen2 {uid}"
    sku = f"TP-{uid}"
    brand = f"LenovoThink-{uid}"

    with SessionLocal() as db:
        prod = models.Product(
            title=title,
            sku=sku,
            brand=brand,
            sale_price=45000.0,
            quantity=2,
            status="in_stock",
            storage_location="store"
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        prod_id = prod.id

    casing_variants = ["thinkpad", "ThinkPad", "THINKPAD", "tHiNkPaD"]
    results_sets = []

    for query in casing_variants:
        resp = core_client.get(f"/api/products/?q={query}&limit=100")
        assert resp.status_code == 200
        items = resp.json()["items"]
        matching_ids = [item["id"] for item in items if item["id"] == prod_id]
        assert len(matching_ids) == 1, f"Product {prod_id} not found for query '{query}'"
        results_sets.append([item["id"] for item in items])

    for res in results_sets[1:]:
        assert res == results_sets[0]

    with SessionLocal() as db:
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        if p:
            db.delete(p)
            db.commit()


def test_case_insensitive_faceted_filters():
    """Verify faceted filters (brand, model, storage_location) are case-insensitive."""
    uid = uuid.uuid4().hex[:6]
    brand = f"АкваБренд-{uid}"
    model_name = f"ВолнаПро-{uid}"
    storage_loc = "store"

    with SessionLocal() as db:
        prod = models.Product(
            title=f"Тест Фильтров {uid}",
            brand=brand,
            model=model_name,
            sale_price=1000.0,
            quantity=1,
            status="in_stock",
            storage_location=storage_loc
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        prod_id = prod.id

    # Filter with lower case
    resp_lower = core_client.get(f"/api/products/?brand={brand.lower()}&model={model_name.lower()}")
    assert resp_lower.status_code == 200
    ids_lower = [item["id"] for item in resp_lower.json()["items"]]
    assert prod_id in ids_lower

    # Filter with upper case
    resp_upper = core_client.get(f"/api/products/?brand={brand.upper()}&model={model_name.upper()}")
    assert resp_upper.status_code == 200
    ids_upper = [item["id"] for item in resp_upper.json()["items"]]
    assert prod_id in ids_upper

    assert ids_lower == ids_upper

    with SessionLocal() as db:
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        if p:
            db.delete(p)
            db.commit()


# ==============================================================================
# 2. OWNER-ONLY SAFE DELETE TESTS
# ==============================================================================

def test_delete_product_rbac_user_forbidden():
    """Verify non-owner request (x-auth-is-owner: 0) is forbidden with 403."""
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        prod = models.Product(
            title=f"Защищенный Товар {uid}",
            sale_price=5000.0,
            quantity=1,
            status="in_stock"
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        prod_id = prod.id

    # Attempt delete as USER (x-auth-is-owner: 0)
    resp = core_client.delete(f"/api/products/{prod_id}", headers={"x-auth-is-owner": "0", "x-api-token": "dev-token"})
    assert resp.status_code == 403
    assert "владельца" in resp.json()["detail"].lower()

    # Verify product still exists in db
    with SessionLocal() as db:
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        assert p is not None
        db.delete(p)
        db.commit()


def test_owner_hard_delete_new_product_without_history():
    """Verify OWNER can permanently hard-delete a new erroneous product without historical links."""
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        prod = models.Product(
            title=f"Ошибочный Товар Без Связей {uid}",
            sku=f"ERR-{uid}",
            sale_price=12000.0,
            quantity=1,
            status="draft",
            storage_location="draft"
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        prod_id = prod.id

        # Add child records: photo, event, stock movement
        photo = models.ProductPhoto(
            product_id=prod_id,
            filename="test.jpg",
            storage_path=f"data/storage/products/{prod_id}/test.jpg",
            media_url=f"/media/products/{prod_id}/test.jpg"
        )
        event = models.ProductEvent(product_id=prod_id, event_type="create", comment="Initial draft")
        stock = models.StockMovement(product_id=prod_id, movement_type="initial", quantity_delta=1, new_quantity=1)
        db.add_all([photo, event, stock])
        db.commit()

    # OWNER deletes product
    resp = core_client.delete(f"/api/products/{prod_id}", headers={"x-auth-is-owner": "1", "x-api-token": "dev-token"})
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "ok"
    assert res_data["action"] == "hard_deleted"

    # Verify product and child records are completely removed
    with SessionLocal() as db:
        assert db.query(models.Product).filter(models.Product.id == prod_id).first() is None
        assert db.query(models.ProductPhoto).filter(models.ProductPhoto.product_id == prod_id).first() is None
        assert db.query(models.ProductEvent).filter(models.ProductEvent.product_id == prod_id).first() is None
        assert db.query(models.StockMovement).filter(models.StockMovement.product_id == prod_id).first() is None

        # Verify audit_log entry
        audit = db.query(models.AuditLog).filter(
            models.AuditLog.entity_type == "product",
            models.AuditLog.entity_id == prod_id,
            models.AuditLog.action == "delete_hard"
        ).first()
        assert audit is not None
        assert "hard-deleted" in audit.comment

    verify_db_integrity()


def test_owner_soft_delete_product_with_sales_history():
    """Verify product linked to a completed sale is archived (soft-deleted), preserving history and FKs."""
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        prod = models.Product(
            title=f"Проданный Товар {uid}",
            sku=f"SOLD-{uid}",
            sale_price=25000.0,
            quantity=1,
            status="sold",
            storage_location="store"
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        prod_id = prod.id

        sale = models.Sale(
            total_amount=25000.0,
            payment_method="card",
            status="completed"
        )
        db.add(sale)
        db.commit()
        db.refresh(sale)
        sale_id = sale.id

        sale_item = models.SaleItem(
            sale_id=sale_id,
            product_id=prod_id,
            title=prod.title,
            price=25000.0,
            quantity=1
        )
        db.add(sale_item)
        db.commit()

    # OWNER deletes product with sales history
    resp = core_client.delete(f"/api/products/{prod_id}", headers={"x-auth-is-owner": "1", "x-api-token": "dev-token"})
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "ok"
    assert res_data["action"] == "soft_deleted"

    # Verify product is safely archived, NOT deleted
    with SessionLocal() as db:
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        assert p is not None
        assert p.status == "archived"
        assert p.storage_location == "archive"

        # Verify sale and sale_item are completely intact
        si = db.query(models.SaleItem).filter(models.SaleItem.product_id == prod_id).first()
        assert si is not None
        assert si.sale_id == sale_id

        # Verify audit_log entry
        audit = db.query(models.AuditLog).filter(
            models.AuditLog.entity_type == "product",
            models.AuditLog.entity_id == prod_id,
            models.AuditLog.action == "delete_soft"
        ).first()
        assert audit is not None
        assert "archived" in audit.comment

        # Cleanup test sale, events, and archived product
        db.query(models.ProductEvent).filter(models.ProductEvent.product_id == prod_id).delete()
        db.delete(si)
        db.delete(sale)
        db.flush()
        db.delete(p)
        db.commit()

    verify_db_integrity()


def test_inventory_and_admin_delete_endpoints():
    """Verify inventory module and admin-shell delete endpoints enforce OWNER check."""
    # Test inventory-sales-module endpoint
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            sys.modules.pop(k, None)

    sys.path = [p for p in sys.path if "core" not in p and "admin-shell" not in p and "inventory-sales-module" not in p]
    sys.path.insert(0, inv_path)

    from app.main import app as inv_app
    inv_client = TestClient(inv_app)

    # 1. Non-owner request to inventory module delete
    resp = inv_client.post("/inventory/products/99999/delete", headers={"x-auth-is-owner": "0"})
    assert resp.status_code == 403

    # Clean up before testing admin-shell
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            sys.modules.pop(k, None)

    sys.path = [p for p in sys.path if "core" not in p and "admin-shell" not in p and "inventory-sales-module" not in p]
    sys.path.insert(0, admin_path)

    from app.main import app as admin_app
    admin_client = TestClient(admin_app)

    # 2. Non-owner request to admin-shell delete
    resp = admin_client.delete("/admin-api/products/99999", headers={"x-auth-is-owner": "0"})
    assert resp.status_code == 403
    resp_post = admin_client.post("/admin-api/products/99999/delete", headers={"x-auth-is-owner": "0"})
    assert resp_post.status_code == 403

    # 3. Spoofed owner request to admin-shell delete (with x-auth-is-owner: 1 but no cert)
    # The fix ensures admin-shell ignores this header entirely.
    resp = admin_client.delete("/admin-api/products/99999", headers={"x-auth-is-owner": "1"})
    assert resp.status_code == 403

    # 4. Spoofed owner request to inventory-sales-module (with x-auth-is-owner: 1 but NO valid api token)
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            sys.modules.pop(k, None)
    sys.path = [p for p in sys.path if "core" not in p and "admin-shell" not in p and "inventory-sales-module" not in p]
    sys.path.insert(0, inv_path)
    from app.main import app as inv_app
    inv_client2 = TestClient(inv_app)
    resp = inv_client2.post("/inventory/products/99999/delete", headers={"x-auth-is-owner": "1"})
    assert resp.status_code == 403

    # 5. Spoofed owner request to Core API directly
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            sys.modules.pop(k, None)
    sys.path = [p for p in sys.path if "core" not in p and "admin-shell" not in p and "inventory-sales-module" not in p]
    sys.path.insert(0, core_path)
    from app.main import app as core_app
    core_client = TestClient(core_app)
    resp = core_client.delete("/api/products/99999", headers={"x-auth-is-owner": "1"})
    assert resp.status_code == 403
