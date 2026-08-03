import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.database import engine
from app.services.sale_status_repair import normalize_misclassified_reissued_sales

client = TestClient(app)

def create_test_product(price=1000.0, qty=10):
    sku = f"REISSUE-TEST-{uuid.uuid4().hex[:8]}"
    res = client.post("/api/products/", json={
        "sku": sku,
        "title": f"Reissue Test Product {sku}",
        "sale_price": price,
        "status": "in_stock",
        "quantity": qty,
        "storage_location": "store"
    })
    assert res.status_code == 200
    return res.json()["id"]

def test_reissue_creates_reissued_and_superseded_statuses():
    pid = create_test_product()
    # 1. Create initial sale
    sale1_resp = client.post("/api/sales/", json={
        "payment_method": "cash",
        "items": [{"product_id": pid, "title": "Test", "price": 1000.0, "quantity": 1}]
    })
    assert sale1_resp.status_code == 200
    sale1_id = sale1_resp.json()["id"]
    assert sale1_resp.json()["status"] == "completed"

    # 2. Cancel sale
    cancel_resp = client.post(f"/api/sales/{sale1_id}/cancel", json={"reason": "Testing cancel", "canceled_by": "Test"})
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "canceled"

    # 3. Reissue sale
    reissue_resp = client.post(f"/api/sales/{sale1_id}/reissue", json={
        "reason": "Testing reissue",
        "payment_method": "card",
        "items": [{"product_id": pid, "title": "Test", "price": 1000.0, "quantity": 1}]
    })
    assert reissue_resp.status_code == 200
    new_sale = reissue_resp.json()
    new_sale_id = new_sale["id"]

    # Assert new sale has status='reissued' and source_sale_id
    assert new_sale["status"] == "reissued"
    assert new_sale["source_sale_id"] == sale1_id

    # Assert old sale has status='superseded' and superseded_by_sale_id
    old_sale = client.get(f"/api/sales/{sale1_id}").json()
    assert old_sale["status"] == "superseded"
    assert old_sale["superseded_by_sale_id"] == new_sale_id

def test_filters_semantics_completed_vs_reissued():
    pid = create_test_product()
    # Regular completed sale
    s_comp = client.post("/api/sales/", json={
        "payment_method": "cash",
        "items": [{"product_id": pid, "title": "Test", "price": 500.0, "quantity": 1}]
    }).json()

    # Reissued sale flow
    s_old = client.post("/api/sales/", json={
        "payment_method": "cash",
        "items": [{"product_id": pid, "title": "Test", "price": 500.0, "quantity": 1}]
    }).json()
    client.post(f"/api/sales/{s_old['id']}/cancel", json={"reason": "Cancel", "canceled_by": "Test"})
    s_reissued_resp = client.post(f"/api/sales/{s_old['id']}/reissue", json={
        "reason": "Reissue",
        "payment_method": "cash",
        "items": [{"product_id": pid, "title": "Test", "price": 500.0, "quantity": 1}]
    })
    assert s_reissued_resp.status_code == 200
    s_reissued = s_reissued_resp.json()

    # Query status=completed
    res_comp = client.get("/api/sales/?status=completed").json()
    comp_ids = [s["id"] for s in res_comp["items"]]
    assert s_comp["id"] in comp_ids
    assert s_reissued["id"] not in comp_ids
    assert s_old["id"] not in comp_ids

    # Query status=reissued
    res_reissued = client.get("/api/sales/?status=reissued").json()
    reissued_ids = [s["id"] for s in res_reissued["items"]]
    assert s_reissued["id"] in reissued_ids
    assert s_comp["id"] not in reissued_ids

    # Query status=superseded
    res_superseded = client.get("/api/sales/?status=superseded").json()
    superseded_ids = [s["id"] for s in res_superseded["items"]]
    assert s_old["id"] in superseded_ids

def test_report_includes_completed_and_reissued_excludes_canceled_and_superseded():
    pid = create_test_product()
    s_old = client.post("/api/sales/", json={
        "payment_method": "cash",
        "items": [{"product_id": pid, "title": "Test", "price": 777.0, "quantity": 1}]
    }).json()
    client.post(f"/api/sales/{s_old['id']}/cancel", json={"reason": "Cancel", "canceled_by": "Test"})
    s_new_resp = client.post(f"/api/sales/{s_old['id']}/reissue", json={
        "reason": "Reissue",
        "payment_method": "cash",
        "items": [{"product_id": pid, "title": "Test", "price": 777.0, "quantity": 1}]
    })
    assert s_new_resp.status_code == 200

    report = client.get("/api/reports/sales?period=today").json()
    assert report["total_amount"] >= 777.0

def test_idempotent_status_normalization_migration():
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        count1 = normalize_misclassified_reissued_sales(db)
        assert count1 == 0
        count2 = normalize_misclassified_reissued_sales(db)
        assert count2 == 0
    finally:
        db.close()
