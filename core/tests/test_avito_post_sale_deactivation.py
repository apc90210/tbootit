import uuid
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import models
from app.database import SessionLocal

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_post_sale_tasks():
    db = SessionLocal()
    try:
        db.query(models.AvitoPostSaleTask).delete()
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(models.AvitoPostSaleTask).delete()
        db.commit()
    finally:
        db.close()


def create_product(sku_prefix="AVPOST", qty=5, price=1500.0):
    sku = f"{sku_prefix}-{uuid.uuid4().hex[:8]}"
    resp = client.post("/api/products/", json={
        "sku": sku,
        "title": f"Product {sku}",
        "sale_price": price,
        "quantity": qty,
        "storage_location": "store",
        "status": "in_stock"
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def create_sale(items):
    total = sum(i["price"] * i["quantity"] for i in items)
    resp = client.post("/api/sales/", json={
        "total_amount": total,
        "payment_method": "cash",
        "items": items
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def attach_avito_listing(product_id: int, external_id: str, status: str = "active"):
    db = SessionLocal()
    try:
        listing = models.ProductExternalListing(
            product_id=product_id,
            marketplace="avito",
            external_account_key="test_account_key",
            external_item_id=external_id,
            external_url=f"https://www.avito.ru/moskva/tovary/{external_id}",
            remote_status=status,
            sync_state="synced"
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        return listing.id
    finally:
        db.close()


def test_sale_no_avito_listing():
    """Section 6 & 21: Sale completed with no linked Avito listing -> no prompt, no task."""
    prod = create_product()
    sale = create_sale([{"product_id": prod["id"], "title": prod["title"], "price": 1000.0, "quantity": 1}])

    resp = client.get(f"/api/sales/{sale['id']}/avito-tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert len(data["tasks"]) == 0

    # Ensure nothing persisted
    db = SessionLocal()
    try:
        tasks = db.query(models.AvitoPostSaleTask).filter(models.AvitoPostSaleTask.sale_id == sale["id"]).all()
        assert len(tasks) == 0
    finally:
        db.close()


def test_sale_with_active_avito_listing_creates_suggested_task():
    """Section 6, 7 & 21: Active linked listing -> suggested task created with correct idempotency fields."""
    prod = create_product()
    avito_id = f"av_{uuid.uuid4().hex[:8]}"
    ext_id = attach_avito_listing(prod["id"], avito_id, status="active")

    sale = create_sale([{"product_id": prod["id"], "title": prod["title"], "price": 1500.0, "quantity": 1}])

    resp = client.get(f"/api/sales/{sale['id']}/avito-tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    task = data["tasks"][0]
    assert task["sale_id"] == sale["id"]
    assert task["product_id"] == prod["id"]
    assert task["avito_listing_id"] == avito_id
    assert task["external_listing_id"] == ext_id
    assert task["status"] == "suggested"
    assert task["action"] == "deactivate"
    assert task["attempt_count"] == 0


def test_sale_with_inactive_avito_listing_no_task():
    """Section 6 & 21: Inactive/archived linked listing -> no deactivation task created."""
    prod = create_product()
    avito_id = f"av_arch_{uuid.uuid4().hex[:8]}"
    attach_avito_listing(prod["id"], avito_id, status="archived")

    sale = create_sale([{"product_id": prod["id"], "title": prod["title"], "price": 1500.0, "quantity": 1}])

    resp = client.get(f"/api/sales/{sale['id']}/avito-tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert len(data["tasks"]) == 0


def test_idempotent_task_creation():
    """Section 7 & 21: Duplicate requests return existing task without creating duplicate records."""
    prod = create_product()
    avito_id = f"av_idem_{uuid.uuid4().hex[:8]}"
    attach_avito_listing(prod["id"], avito_id, status="active")

    sale = create_sale([{"product_id": prod["id"], "title": prod["title"], "price": 1500.0, "quantity": 1}])

    # Call twice
    r1 = client.get(f"/api/sales/{sale['id']}/avito-tasks").json()
    r2 = client.get(f"/api/sales/{sale['id']}/avito-tasks").json()
    assert r1["count"] == 1
    assert r2["count"] == 1
    assert r1["tasks"][0]["id"] == r2["tasks"][0]["id"]

    db = SessionLocal()
    try:
        tasks = db.query(models.AvitoPostSaleTask).filter(models.AvitoPostSaleTask.sale_id == sale["id"]).all()
        assert len(tasks) == 1
    finally:
        db.close()


def test_multi_item_sale():
    """Section 14 & 21: Multi-item sale creates one task per active linked listing, ignores unlinked products."""
    p1 = create_product(sku_prefix="P1")
    p2 = create_product(sku_prefix="P2")
    p3 = create_product(sku_prefix="P3")

    av1 = f"av1_{uuid.uuid4().hex[:8]}"
    av2 = f"av2_{uuid.uuid4().hex[:8]}"
    attach_avito_listing(p1["id"], av1, status="active")
    attach_avito_listing(p2["id"], av2, status="active")
    # p3 has no listing

    sale = create_sale([
        {"product_id": p1["id"], "title": p1["title"], "price": 100.0, "quantity": 1},
        {"product_id": p2["id"], "title": p2["title"], "price": 200.0, "quantity": 1},
        {"product_id": p3["id"], "title": p3["title"], "price": 300.0, "quantity": 1}
    ])

    resp = client.get(f"/api/sales/{sale['id']}/avito-tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    task_avito_ids = {t["avito_listing_id"] for t in data["tasks"]}
    assert task_avito_ids == {av1, av2}

    # Queue both
    q_resp = client.post(f"/api/sales/{sale['id']}/avito-deactivate")
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert q_data["queued_count"] == 2
    for t in q_data["tasks"]:
        assert t["status"] == "queued"


def test_task_lifecycle_and_retry_limit():
    """Section 16 & 21: suggested -> queued -> processing -> failed -> retry -> manual_required after 3 attempts."""
    prod = create_product()
    avito_id = f"av_retry_{uuid.uuid4().hex[:8]}"
    attach_avito_listing(prod["id"], avito_id, status="active")

    sale = create_sale([{"product_id": prod["id"], "title": prod["title"], "price": 500.0, "quantity": 1}])

    # 1. Suggested -> Queued
    q_resp = client.post(f"/api/sales/{sale['id']}/avito-deactivate")
    assert q_resp.status_code == 200
    task_id = q_resp.json()["tasks"][0]["id"]

    # 2. Queued -> Processing (Attempt 1)
    pop1 = client.get("/api/avito/post-sale-tasks/next").json()
    assert pop1["task"] is not None
    assert pop1["task"]["task_id"] == task_id
    assert pop1["task"]["attempt_count"] == 1

    # 3. Processing -> Failed (Attempt 1)
    f1 = client.post(f"/api/avito/post-sale-tasks/{task_id}/failed", json={"error": "Network timeout 1"}).json()
    assert f1["status"] == "failed"
    assert f1["last_error"] == "Network timeout 1"

    # Retry manually
    r1 = client.post(f"/api/avito/post-sale-tasks/{task_id}/retry").json()
    assert r1["status"] == "queued"

    # 4. Queued -> Processing (Attempt 2)
    pop2 = client.get("/api/avito/post-sale-tasks/next").json()
    assert pop2["task"]["task_id"] == task_id
    assert pop2["task"]["attempt_count"] == 2

    # 5. Processing -> Failed (Attempt 2)
    f2 = client.post(f"/api/avito/post-sale-tasks/{task_id}/failed", json={"error": "Network timeout 2"}).json()
    assert f2["status"] == "failed"

    # Retry manually
    client.post(f"/api/avito/post-sale-tasks/{task_id}/retry")

    # 6. Queued -> Processing (Attempt 3)
    pop3 = client.get("/api/avito/post-sale-tasks/next").json()
    assert pop3["task"]["task_id"] == task_id
    assert pop3["task"]["attempt_count"] == 3

    # 7. Processing -> manual_required (Attempt 3 reaches max retry limit of 3)
    f3 = client.post(f"/api/avito/post-sale-tasks/{task_id}/failed", json={"error": "Network timeout 3"}).json()
    assert f3["status"] == "manual_required"

    # Next queue check returns None
    pop_none = client.get("/api/avito/post-sale-tasks/next").json()
    assert pop_none["task"] is None


def test_task_cancel():
    """Section 7 & 21: Task can be explicitly canceled."""
    prod = create_product()
    avito_id = f"av_cancel_{uuid.uuid4().hex[:8]}"
    attach_avito_listing(prod["id"], avito_id, status="active")

    sale = create_sale([{"product_id": prod["id"], "title": prod["title"], "price": 500.0, "quantity": 1}])
    client.post(f"/api/sales/{sale['id']}/avito-deactivate")

    task = client.get(f"/api/sales/{sale['id']}/avito-tasks").json()["tasks"][0]
    task_id = task["id"]

    res = client.post(f"/api/avito/post-sale-tasks/{task_id}/cancel").json()
    assert res["status"] == "canceled"


def test_success_semantics_audit_and_stock_preservation():
    """Section 17 & 21: Success updates external listing to archived and writes audit event. Physical stock unchanged."""
    initial_qty = 8
    prod = create_product(qty=initial_qty, price=2000.0)
    avito_id = f"av_succ_{uuid.uuid4().hex[:8]}"
    ext_id = attach_avito_listing(prod["id"], avito_id, status="active")

    # Sale 2 items
    sale = create_sale([{"product_id": prod["id"], "title": prod["title"], "price": 2000.0, "quantity": 2}])

    # Verify stock decremented strictly by the sale
    p_after_sale = client.get(f"/api/products/{prod['id']}").json()
    assert p_after_sale["quantity"] == initial_qty - 2

    # Trigger deactivation
    client.post(f"/api/sales/{sale['id']}/avito-deactivate")
    pop = client.get("/api/avito/post-sale-tasks/next").json()
    task_id = pop["task"]["task_id"]

    # Confirm success externally
    succ_resp = client.post(f"/api/avito/post-sale-tasks/{task_id}/success", json={"confirmed_by": "chrome_extension"})
    assert succ_resp.status_code == 200
    task_data = succ_resp.json()
    assert task_data["status"] == "success"
    assert task_data["finished_at"] is not None

    # Verify ProductExternalListing is now archived
    db = SessionLocal()
    try:
        ext = db.query(models.ProductExternalListing).filter(models.ProductExternalListing.id == ext_id).first()
        assert ext.remote_status == "archived"

        # Verify audit log event written
        audit = db.query(models.AuditLog).filter(
            models.AuditLog.action == "avito_listing_deactivated_after_sale",
            models.AuditLog.entity_id == task_id
        ).first()
        assert audit is not None
        assert str(sale["id"]) in audit.new_value or sale["id"] in json.loads(audit.new_value).values()

        # CRITICAL SAFETY: Physical stock must be COMPLETELY UNCHANGED by Avito task
        p_check = db.query(models.Product).filter(models.Product.id == prod["id"]).first()
        assert p_check.quantity == initial_qty - 2

        # CRITICAL SAFETY: Sale must remain completed
        s_check = db.query(models.Sale).filter(models.Sale.id == sale["id"]).first()
        assert s_check.status == "completed"
    finally:
        db.close()


def test_sale_cancellation_does_not_republish():
    """Section 18 & 21: Canceling a sale after Avito listing was deactivated does NOT republish listing."""
    prod = create_product(qty=1, price=1200.0)
    avito_id = f"av_nocancel_repub_{uuid.uuid4().hex[:8]}"
    ext_id = attach_avito_listing(prod["id"], avito_id, status="active")

    sale = create_sale([{"product_id": prod["id"], "title": prod["title"], "price": 1200.0, "quantity": 1}])
    client.post(f"/api/sales/{sale['id']}/avito-deactivate")
    pop = client.get("/api/avito/post-sale-tasks/next").json()
    client.post(f"/api/avito/post-sale-tasks/{pop['task']['task_id']}/success")

    # Verify listing is archived
    db = SessionLocal()
    try:
        ext = db.query(models.ProductExternalListing).filter(models.ProductExternalListing.id == ext_id).first()
        assert ext.remote_status == "archived"
    finally:
        db.close()

    # Cancel the sale
    cancel_resp = client.post(f"/api/sales/{sale['id']}/cancel", json={"reason": "Возврат покупателем"})
    assert cancel_resp.status_code == 200

    # Verify product stock is restored by standard cancellation logic
    p_after_cancel = client.get(f"/api/products/{prod['id']}").json()
    assert p_after_cancel["quantity"] == 1
    assert p_after_cancel["status"] == "in_stock"

    # Verify listing remains archived (NO AUTOMATIC REPUBLISH)
    db = SessionLocal()
    try:
        ext = db.query(models.ProductExternalListing).filter(models.ProductExternalListing.id == ext_id).first()
        assert ext.remote_status == "archived"
    finally:
        db.close()
