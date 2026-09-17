import os
import sys
import uuid
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
core_path = str(REPO_ROOT / "core")

# Clean sys.modules to ensure core app is imported cleanly
for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        sys.modules.pop(k, None)

if core_path in sys.path:
    sys.path.remove(core_path)
sys.path.insert(0, core_path)

from app.main import app as core_app
from app.database import SessionLocal
from app import models

client = TestClient(core_app)


def test_core_sale_bulk_delete_and_inventory_restoration():
    """Test that bulk deleting a sale restores sold products to in_stock and cleans revisions/movements."""
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        prod = models.Product(
            title="Test Laptop for Delete",
            sku=f"TEST-DEL-{uid}",
            sale_price=35000.0,
            quantity=1,
            status="in_stock",
            storage_location="store"
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        prod_id = prod.id

    # 2. Create a sale selling this product
    sale_payload = {
        "items": [
            {"product_id": prod_id, "title": "Test Laptop for Delete", "price": 35000.0, "quantity": 1}
        ],
        "total_amount": 35000.0,
        "payment_method": "cash",
        "comment": "Test sale to be deleted"
    }
    create_resp = client.post("/api/sales/", json=sale_payload)
    assert create_resp.status_code == 200
    sale_id = create_resp.json()["id"]

    # Verify product is now sold
    with SessionLocal() as db:
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        assert p.quantity == 0
        assert p.status == "sold"

    # Add a revision to the sale
    rev_payload = {
        "payment_method": "card",
        "comment": "Correction test",
        "items": [{"product_id": prod_id, "title": "Test Laptop", "price": 34000.0, "quantity": 1}]
    }
    rev_resp = client.post(f"/api/sales/{sale_id}/correct", json=rev_payload)
    assert rev_resp.status_code == 200

    # 3. Call bulk-delete
    del_resp = client.post("/api/sales/bulk-delete", json={"sale_ids": [sale_id]})
    assert del_resp.status_code == 200
    del_data = del_resp.json()
    assert del_data["status"] == "ok"
    assert del_data["deleted_count"] == 1
    assert sale_id in del_data["deleted_ids"]

    # 4. Verify sale is gone
    get_sale_resp = client.get(f"/api/sales/{sale_id}")
    assert get_sale_resp.status_code == 404

    # 5. Verify product was restored to in_stock with quantity=1
    with SessionLocal() as db:
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        assert p.quantity == 1
        assert p.status == "in_stock"
        assert p.storage_location == "store"

        # Verify revisions are deleted
        revs = db.query(models.SaleRevision).filter(models.SaleRevision.sale_id == sale_id).all()
        assert len(revs) == 0

        # Verify items are deleted
        items = db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).all()
        assert len(items) == 0


def test_core_repair_bulk_delete():
    """Test that bulk deleting a repair deletes status history and decouples any linked sale."""
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        repair = models.RepairOrder(
            number=f"R-DEL-{uid}",
            customer_name="Иван Тестовый",
            customer_phone="+7 999 123-45-67",
            device_type="Смартфон",
            brand="Apple",
            model="iPhone 13",
            reported_issue="Замена экрана",
            status="received"
        )
        db.add(repair)
        db.commit()
        db.refresh(repair)
        repair_id = repair.id

        # Add history
        hist = models.RepairStatusHistory(
            repair_id=repair_id,
            old_status=None,
            new_status="received",
            comment="Принят в ремонт"
        )
        db.add(hist)
        db.commit()

    # 2. Call bulk-delete
    del_resp = client.post("/api/repairs/bulk-delete", json={"repair_ids": [repair_id]})
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] == 1
    assert repair_id in del_resp.json()["deleted_ids"]

    # 3. Verify repair is gone
    get_rep_resp = client.get(f"/api/repairs/{repair_id}")
    assert get_rep_resp.status_code == 404

    # Verify history is deleted
    with SessionLocal() as db:
        hists = db.query(models.RepairStatusHistory).filter(models.RepairStatusHistory.repair_id == repair_id).all()
        assert len(hists) == 0


def test_inventory_sales_module_rbac():
    """Test inventory-sales-module owner RBAC enforcement."""
    # Clean sys.modules to load inventory-sales-module
    inv_path = str(REPO_ROOT / "inventory-sales-module")
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            sys.modules.pop(k, None)

    if core_path in sys.path:
        sys.path.remove(core_path)
    if inv_path not in sys.path:
        sys.path.insert(0, inv_path)

    from app.main import app as inv_app
    inv_client = TestClient(inv_app)

    # 1. Non-owner request to POST /sales/bulk-delete -> 403 Forbidden
    resp_del_unauth = inv_client.post("/sales/bulk-delete", json={"sale_ids": [1]})
    assert resp_del_unauth.status_code == 403
    detail = resp_del_unauth.json().get("detail", "")
    assert "Только владелец" in detail or "Доступ запрещён" in detail

    # 2. Owner request with empty list should be 400 (not 403)
    resp_del_auth = inv_client.post(
        "/sales/bulk-delete",
        json={"sale_ids": []},
        headers={"x-auth-is-owner": "1"}
    )
    assert resp_del_auth.status_code == 400


def test_repairs_module_rbac():
    """Test repairs-module owner RBAC enforcement."""
    # Clean sys.modules to load repairs-module
    rep_path = str(REPO_ROOT / "repairs-module")
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            sys.modules.pop(k, None)

    inv_path = str(REPO_ROOT / "inventory-sales-module")
    if inv_path in sys.path:
        sys.path.remove(inv_path)
    if rep_path not in sys.path:
        sys.path.insert(0, rep_path)

    from app.main import app as rep_app
    rep_client = TestClient(rep_app)

    # 1. Non-owner request to POST /repairs/repairs/bulk-delete -> 403 Forbidden
    resp_del_unauth = rep_client.post("/repairs/repairs/bulk-delete", json={"repair_ids": [1]})
    assert resp_del_unauth.status_code == 403
    detail = resp_del_unauth.json().get("detail", "")
    assert "Только владелец" in detail or "Доступ запрещён" in detail

    # 2. Owner request with empty list should be 400 (not 403)
    resp_del_auth = rep_client.post(
        "/repairs/repairs/bulk-delete",
        json={"repair_ids": []},
        headers={"x-auth-is-owner": "1"}
    )
    assert resp_del_auth.status_code == 400
