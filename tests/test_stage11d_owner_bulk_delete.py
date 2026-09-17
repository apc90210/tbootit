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


# ----------------------------------------------------------------------
# 1. CORE TESTS: Hard Delete Invariants & Business Logic
# ----------------------------------------------------------------------

def test_core_sale_bulk_delete_and_inventory_restoration():
    """Test Invariant A: Deleting an ordinary completed sale restores stock exactly once."""
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

    # Create a sale selling this product
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

    # Call bulk-delete
    del_resp = client.post("/api/sales/bulk-delete", json={"sale_ids": [sale_id]})
    assert del_resp.status_code == 200
    del_data = del_resp.json()
    assert del_data["status"] == "ok"
    assert del_data["deleted_count"] == 1
    assert sale_id in del_data["deleted_ids"]

    # Verify sale is gone
    get_sale_resp = client.get(f"/api/sales/{sale_id}")
    assert get_sale_resp.status_code == 404

    # Verify product was restored to in_stock with quantity=1 exactly
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


def test_canceled_sale_delete_does_not_restore_stock_twice():
    """Test Invariant B: Deleting a canceled sale does not restore stock twice."""
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        prod = models.Product(
            title="Test Laptop for Cancel Delete",
            sku=f"TEST-CDEL-{uid}",
            sale_price=20000.0,
            quantity=1,
            status="in_stock",
            storage_location="store"
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        prod_id = prod.id

    create_resp = client.post("/api/sales/", json={
        "items": [{"product_id": prod_id, "title": "Test Laptop for Cancel Delete", "price": 20000.0, "quantity": 1}],
        "total_amount": 20000.0,
        "payment_method": "cash"
    })
    assert create_resp.status_code == 200
    sale_id = create_resp.json()["id"]

    with SessionLocal() as db:
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        assert p.quantity == 0

    # Cancel the sale (first restore)
    cancel_resp = client.post(f"/api/sales/{sale_id}/cancel", json={"reason": "Клиент отказался"})
    assert cancel_resp.status_code == 200

    with SessionLocal() as db:
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        assert p.quantity == 1

    # Delete the canceled sale (must NOT restore again to 2)
    del_resp = client.post("/api/sales/bulk-delete", json={"sale_ids": [sale_id]})
    assert del_resp.status_code == 200

    with SessionLocal() as db:
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        assert p.quantity == 1
        assert p.status == "in_stock"


def test_repair_linked_sale_delete_resets_repair_to_ready():
    """Test Invariant C: Deleting a repair-linked sale resets repair to coherent 'ready' state."""
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        repair = models.RepairOrder(
            number=f"R-LNK-{uid}",
            customer_name="Тест Связи",
            customer_phone="+7 999 555-55-55",
            device_type="Смартфон",
            brand="Samsung",
            model="Galaxy S21",
            reported_issue="Замена батареи",
            status="ready",
            estimated_repair_amount=4000
        )
        db.add(repair)
        db.commit()
        db.refresh(repair)
        rep_id = repair.id

    issue_resp = client.post(
        f"/api/repairs/{rep_id}/status",
        json={
            "status": "issued",
            "final_amount": 4500.0,
            "payment_method": "cash",
            "warranty_days": 30,
            "comment": "Выдан клиенту"
        }
    )
    assert issue_resp.status_code == 200
    issued_data = issue_resp.json()
    assert issued_data["status"] == "issued"
    assert issued_data["sale_id"] is not None
    linked_sale_id = issued_data["sale_id"]

    # Delete the linked sale
    del_sale_resp = client.post("/api/sales/bulk-delete", json={"sale_ids": [linked_sale_id]})
    assert del_sale_resp.status_code == 200

    # Verify repair is reset to coherent 'ready' state
    rep_check = client.get(f"/api/repairs/{rep_id}").json()
    assert rep_check["status"] == "ready"
    assert rep_check["sale_id"] is None
    assert rep_check["final_amount"] is None
    assert rep_check["payment_method"] is None
    assert rep_check["warranty_days"] is None

    # Verify status history documents this
    with SessionLocal() as db:
        hist = db.query(models.RepairStatusHistory).filter(
            models.RepairStatusHistory.repair_id == rep_id
        ).order_by(models.RepairStatusHistory.changed_at.desc()).first()
        assert hist.new_status == "ready"
        assert "безвозвратно удалена владельцем" in hist.comment


def test_repair_with_active_linked_sale_cannot_be_deleted():
    """Test Invariant D: Repair with linked active sale cannot be deleted without deleting sale first."""
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        repair = models.RepairOrder(
            number=f"R-ACT-{uid}",
            customer_name="Тест Блокировки",
            customer_phone="+7 999 444-44-44",
            device_type="Планшет",
            brand="Apple",
            model="iPad Air",
            reported_issue="Чистка разъёма",
            status="ready",
            estimated_repair_amount=2000
        )
        db.add(repair)
        db.commit()
        db.refresh(repair)
        rep_id = repair.id

    issue_resp = client.post(
        f"/api/repairs/{rep_id}/status",
        json={
            "status": "issued",
            "final_amount": 2000.0,
            "payment_method": "card",
            "warranty_days": 14,
            "comment": "Выдан клиенту"
        }
    )
    assert issue_resp.status_code == 200
    linked_sale_id = issue_resp.json()["sale_id"]

    # Attempt to delete the repair -> MUST be blocked with 400
    del_rep_resp = client.post("/api/repairs/bulk-delete", json={"repair_ids": [rep_id]})
    assert del_rep_resp.status_code == 400
    detail = del_rep_resp.json().get("detail", "")
    assert f"сначала удалите связанную продажу №{linked_sale_id}" in detail

    del_single = client.delete(f"/api/repairs/{rep_id}")
    assert del_single.status_code == 400
    assert f"сначала удалите связанную продажу №{linked_sale_id}" in del_single.json().get("detail", "")

    # Verify repair still exists intact
    get_rep = client.get(f"/api/repairs/{rep_id}")
    assert get_rep.status_code == 200


def test_atomic_bulk_delete_validation_prevents_partial_corruption():
    """Test Invariant E: Bulk delete validation is atomic; if 1 of 2 is ineligible, neither is deleted."""
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        rep1 = models.RepairOrder(
            number=f"R-CLN-{uid}",
            customer_name="Чистый Ремонт",
            customer_phone="+7 999 111-11-11",
            device_type="ПК",
            status="received"
        )
        rep2 = models.RepairOrder(
            number=f"R-BLOCKED-{uid}",
            customer_name="Блокированный Ремонт",
            customer_phone="+7 999 222-22-22",
            device_type="ПК",
            status="ready",
            estimated_repair_amount=1000
        )
        db.add_all([rep1, rep2])
        db.commit()
        db.refresh(rep1)
        db.refresh(rep2)
        r1_id = rep1.id
        r2_id = rep2.id

    client.post(
        f"/api/repairs/{r2_id}/status",
        json={"status": "issued", "final_amount": 1000.0, "payment_method": "cash", "warranty_days": 14}
    )

    # Attempt to bulk delete both
    resp = client.post("/api/repairs/bulk-delete", json={"repair_ids": [r1_id, r2_id]})
    assert resp.status_code == 400
    assert "сначала удалите связанную продажу" in resp.json()["detail"]

    # Verify NEITHER was deleted
    assert client.get(f"/api/repairs/{r1_id}").status_code == 200
    assert client.get(f"/api/repairs/{r2_id}").status_code == 200


def test_core_repair_bulk_delete():
    """Test that bulk deleting an unlinked repair deletes status history."""
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

        hist = models.RepairStatusHistory(
            repair_id=repair_id,
            old_status=None,
            new_status="received",
            comment="Принят в ремонт"
        )
        db.add(hist)
        db.commit()

    del_resp = client.post("/api/repairs/bulk-delete", json={"repair_ids": [repair_id]})
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] == 1
    assert repair_id in del_resp.json()["deleted_ids"]

    get_rep_resp = client.get(f"/api/repairs/{repair_id}")
    assert get_rep_resp.status_code == 404

    with SessionLocal() as db:
        hists = db.query(models.RepairStatusHistory).filter(models.RepairStatusHistory.repair_id == repair_id).all()
        assert len(hists) == 0


def test_permanent_delete_audit_logging():
    """Test Section 7: Audit log records permanent_delete actions with entity details."""
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        prod = models.Product(
            title="Audit Test Product",
            sku=f"AUDIT-{uid}",
            sale_price=1500.0,
            quantity=1,
            status="in_stock",
            storage_location="store"
        )
        db.add(prod)
        db.commit()
        prod_id = prod.id

    s_resp = client.post("/api/sales/", json={
        "items": [{"product_id": prod_id, "title": "Audit Test Product", "price": 1500.0, "quantity": 1}],
        "total_amount": 1500.0,
        "payment_method": "cash"
    })
    sale_id = s_resp.json()["id"]
    client.post("/api/sales/bulk-delete", json={"sale_ids": [sale_id]})

    with SessionLocal() as db:
        audit = db.query(models.AuditLog).filter(
            models.AuditLog.entity_type == "sale",
            models.AuditLog.entity_id == sale_id,
            models.AuditLog.action == "permanent_delete"
        ).first()
        assert audit is not None
        assert "Permanent delete by owner" in audit.comment


# ----------------------------------------------------------------------
# 2. MODULE RBAC & UI TESTS
# ----------------------------------------------------------------------

def test_inventory_sales_module_rbac():
    """Test inventory-sales-module owner RBAC enforcement and UI controls."""
    from unittest.mock import patch, AsyncMock
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

    # 3. Non-owner GET /sales -> UI bulk delete bar hidden
    mock_sales = {
        "items": [
            {"id": 1, "created_at": "2026-09-17T10:00:00", "total_amount": 1000.0, "payment_method": "cash", "status": "completed", "revision_count": 0, "items": []}
        ],
        "total": 1
    }
    with patch("app.core_client.core_client.get_sales", new_callable=AsyncMock) as mock_get_sales:
        mock_get_sales.return_value = mock_sales
        resp_ui_non_owner = inv_client.get("/sales")
        assert resp_ui_non_owner.status_code == 200
        assert 'id="ownerBulkBar"' not in resp_ui_non_owner.text

        # 4. Owner GET /sales -> UI bulk delete bar present
        resp_ui_owner = inv_client.get("/sales", headers={"x-auth-is-owner": "1"})
        assert resp_ui_owner.status_code == 200
        assert 'id="ownerBulkBar"' in resp_ui_owner.text


def test_repairs_module_rbac():
    """Test repairs-module owner RBAC enforcement and UI controls."""
    from unittest.mock import patch, AsyncMock
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

    # 3. Non-owner GET /repairs -> UI bulk delete bar hidden
    mock_repairs = {
        "items": [
            {"id": 1, "number": "R-1", "customer_name": "Иван", "device_type": "Ноутбук", "status": "received", "created_at": "2026-09-17T10:00:00"}
        ],
        "total": 1
    }
    with patch("app.core_client.core_client.get_repairs", new_callable=AsyncMock) as mock_get_repairs:
        mock_get_repairs.return_value = mock_repairs
        resp_ui_non_owner = rep_client.get("/repairs")
        assert resp_ui_non_owner.status_code == 200
        assert 'id="ownerBulkBar"' not in resp_ui_non_owner.text

        # 4. Owner GET /repairs -> UI bulk delete bar present
        resp_ui_owner = rep_client.get("/repairs", headers={"x-auth-is-owner": "1"})
        assert resp_ui_owner.status_code == 200
        assert 'id="ownerBulkBar"' in resp_ui_owner.text


# ----------------------------------------------------------------------
# 3. SECURITY & ANTI-SPOOFING TESTS
# ----------------------------------------------------------------------

def test_spoofed_x_auth_is_owner_header_with_non_owner_cert():
    """Test Section 5: A client cannot grant itself owner privileges by sending X-Auth-Is-Owner: 1."""
    admin_path = str(REPO_ROOT / "admin-shell")
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            sys.modules.pop(k, None)

    rep_path = str(REPO_ROOT / "repairs-module")
    if rep_path in sys.path:
        sys.path.remove(rep_path)
    if admin_path not in sys.path:
        sys.path.insert(0, admin_path)

    from app.main import app as admin_app, _is_owner, _require_owner
    from starlette.requests import Request
    from starlette.datastructures import Headers

    # Mock non-owner certificate verification
    # When request has non-owner serial, _is_owner must return False even if X-Auth-Is-Owner: 1 is sent
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/admin-api/dev-reset",
        "headers": [
            (b"x-client-cert-verify", b"SUCCESS"),
            (b"x-client-cert-serial", b"1002"),  # Non-owner certificate serial
            (b"x-auth-is-owner", b"1"),          # Spoofed header
        ],
    }
    req = Request(scope)

    # In admin-shell, if cert serial 1002 is not owner, _is_owner must evaluate to False
    is_owner = _is_owner(req)
    assert is_owner is False

    with pytest.raises(Exception) as exc_info:
        _require_owner(req)
    assert exc_info.value.status_code == 403
