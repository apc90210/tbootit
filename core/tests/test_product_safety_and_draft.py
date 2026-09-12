import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app import models

client = TestClient(app)


def test_product_soft_delete_preserves_row_and_writes_off():
    """Ensure that DELETE /api/products/{id} does NOT drop the database row and marks it written_off."""
    db = SessionLocal()
    sku = f"TEST-SOFTDEL-{uuid.uuid4().hex[:8]}"
    try:
        p = models.Product(
            sku=sku,
            title="Soft Delete Integrity Test Item",
            status="in_stock",
            quantity=1,
            sale_price=500.0,
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        pid = p.id

        # Delete product via API
        resp = client.delete(f"/api/products/{pid}")
        assert resp.status_code == 200
        assert "written_off" in resp.json()["message"]

        # Ensure database row still exists and is marked written_off
        db.expire_all()
        persisted = db.query(models.Product).filter(models.Product.id == pid).first()
        assert persisted is not None, "Product row must NEVER be deleted from the database!"
        assert persisted.status == "written_off"

        # Check audit log
        audit = db.query(models.AuditLog).filter(
            models.AuditLog.entity_type == "product",
            models.AuditLog.entity_id == pid,
            models.AuditLog.action == "delete_soft"
        ).first()
        assert audit is not None, "Soft delete must create an audit record!"

        # Clean up test row
        db.delete(persisted)
        db.commit()
    finally:
        db.close()


def test_seller_draft_workflow():
    """Ensure that products can be moved to and from draft, but cannot be permanently deleted."""
    db = SessionLocal()
    sku = f"TEST-DRAFT-{uuid.uuid4().hex[:8]}"
    try:
        p = models.Product(
            sku=sku,
            title="Draft State Workflow Item",
            status="draft",
            quantity=2,
            sale_price=1200.0,
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        pid = p.id

        # 1. Draft to in_stock
        r1 = client.post(f"/api/products/{pid}/status", json={"status": "in_stock"})
        assert r1.status_code == 200
        assert r1.json()["status"] == "in_stock"

        # 2. In_stock back to draft (seller hiding / putting into draft)
        r2 = client.post(f"/api/products/{pid}/status", json={"status": "draft"})
        assert r2.status_code == 200
        assert r2.json()["status"] == "draft"

        # 3. PATCH status endpoint also works
        r3 = client.patch(f"/api/products/{pid}/status", json={"status": "in_stock"})
        assert r3.status_code == 200
        assert r3.json()["status"] == "in_stock"

        # 4. Draft item deleted is soft deleted
        r4 = client.post(f"/api/products/{pid}/status", json={"status": "draft"})
        assert r4.status_code == 200
        r5 = client.delete(f"/api/products/{pid}")
        assert r5.status_code == 200
        
        db.expire_all()
        persisted = db.query(models.Product).filter(models.Product.id == pid).first()
        assert persisted is not None
        assert persisted.status == "written_off"

        # Clean up
        db.delete(persisted)
        db.commit()
    finally:
        db.close()


def test_no_destructive_delete_endpoints_for_business_entities():
    """Ensure that Sales, Repairs, Customers, and Categories have NO delete endpoints (404 Not Found or 405 Method Not Allowed)."""
    assert client.delete("/api/sales/1").status_code in (404, 405)
    assert client.delete("/api/repairs/1").status_code in (404, 405)
    assert client.delete("/api/customers/1").status_code in (404, 405)
    assert client.delete("/api/categories/1").status_code in (404, 405)
    # dev-reset in core was permanently removed
    assert client.post("/api/admin/dev-reset").status_code == 404


def test_draft_lifecycle_strict_transitions():
    """Verify that only in_stock <-> draft is allowed.
    All transitions reserved->draft, written_off->draft, sold->draft, archived->draft, imported->draft are FORBIDDEN (400).
    """
    db = SessionLocal()
    try:
        # Create products in various statuses
        forbidden_sources = ["reserved", "written_off", "sold", "archived", "imported"]
        for st in forbidden_sources:
            sku = f"TEST-STRICT-{st}-{uuid.uuid4().hex[:6]}"
            p = models.Product(sku=sku, title=f"Test {st}", status=st, quantity=1, sale_price=100.0)
            db.add(p)
            db.commit()
            db.refresh(p)
            pid = p.id

            try:
                # 1. POST /status must reject
                resp_post = client.post(f"/api/products/{pid}/status", json={"status": "draft"})
                assert resp_post.status_code == 400, f"Transition from {st} to draft via POST must return 400, got {resp_post.status_code}"
                assert "Invalid transition" in resp_post.json()["detail"]

                # 2. PATCH /status must reject
                resp_patch = client.patch(f"/api/products/{pid}/status", json={"status": "draft"})
                assert resp_patch.status_code == 400, f"Transition from {st} to draft via PATCH must return 400, got {resp_patch.status_code}"

                # 3. PUT /{id} full update bypass must reject
                resp_put = client.put(f"/api/products/{pid}", json={
                    "title": f"Test {st} updated",
                    "status": "draft"
                })
                assert resp_put.status_code == 400, f"Bypass via PUT from {st} to draft must return 400, got {resp_put.status_code}"

                # 4. Status in DB remains unchanged
                db.expire_all()
                p_db = db.query(models.Product).filter(models.Product.id == pid).first()
                assert p_db.status == st, f"Product status must remain {st}"
            finally:
                db.delete(p)
                db.commit()
    finally:
        db.close()


def test_batch_status_update_does_not_bypass_draft_rules():
    """Verify batch status update skips invalid transitions to draft."""
    db = SessionLocal()
    try:
        p_stock = models.Product(sku=f"TB-IN-{uuid.uuid4().hex[:6]}", title="In Stock", status="in_stock", quantity=1)
        p_written = models.Product(sku=f"TB-WO-{uuid.uuid4().hex[:6]}", title="Written Off", status="written_off", quantity=1)
        db.add_all([p_stock, p_written])
        db.commit()
        db.refresh(p_stock)
        db.refresh(p_written)

        res = client.post("/api/products/batch", json={
            "product_ids": [p_stock.id, p_written.id],
            "status": "draft"
        })
        assert res.status_code == 200

        db.expire_all()
        p_stock_after = db.query(models.Product).filter(models.Product.id == p_stock.id).first()
        p_written_after = db.query(models.Product).filter(models.Product.id == p_written.id).first()

        # in_stock -> draft was ALLOWED
        assert p_stock_after.status == "draft"
        # written_off -> draft was REJECTED/SKIPPED
        assert p_written_after.status == "written_off"

        db.delete(p_stock_after)
        db.delete(p_written_after)
        db.commit()
    finally:
        db.close()

