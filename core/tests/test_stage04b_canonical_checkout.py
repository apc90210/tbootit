import uuid
import concurrent.futures
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import models
from app.database import Base, engine, SessionLocal

client = TestClient(app)


def _create_product(
    title: str = "Test Product",
    price: float = 1000.0,
    qty: int = 5,
    status: str = "in_stock",
    storage_location: str = "store"
) -> int:
    sku = f"SKU-{uuid.uuid4().hex[:8]}"
    resp = client.post("/api/products/", json={
        "sku": sku,
        "title": title,
        "sale_price": price,
        "quantity": qty,
        "status": status,
        "storage_location": storage_location
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def test_01_one_item_sale_succeeds():
    p_id = _create_product(qty=3, price=1500.0)
    checkout_id = str(uuid.uuid4())

    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 1, "unit_price": 1500.0}],
        "payment_method": "cash"
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["sale_id"] > 0
    assert data["receipt_number"] == f"REC-{data['sale_id']:06d}"
    assert data["total_amount"] == 1500.0
    assert data["payment_method"] == "cash"
    assert data["client_checkout_id"] == checkout_id
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == p_id
    assert data["items"][0]["quantity"] == 1
    assert data["items"][0]["unit_price"] == 1500.0


def test_02_multi_item_sale_succeeds():
    p1 = _create_product(title="Item 1", qty=5, price=400.0)
    p2 = _create_product(title="Item 2", qty=10, price=250.0)
    checkout_id = str(uuid.uuid4())

    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [
            {"product_id": p1, "quantity": 2, "unit_price": 400.0},
            {"product_id": p2, "quantity": 3, "unit_price": 250.0}
        ],
        "payment_method": "card"
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_amount"] == 1550.0  # 2*400 + 3*250 = 800 + 750 = 1550
    assert len(data["items"]) == 2


def test_03_canonical_sale_row_created():
    p_id = _create_product(qty=4, price=1200.0)
    checkout_id = str(uuid.uuid4())

    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 1, "unit_price": 1200.0}],
        "payment_method": "transfer",
        "comment": "Mobile sale test"
    })
    assert resp.status_code == 200
    sale_id = resp.json()["sale_id"]

    db = SessionLocal()
    try:
        db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
        assert db_sale is not None
        assert db_sale.total_amount == 1200.0
        assert db_sale.payment_method == "transfer"
        assert db_sale.status == "completed"
        assert db_sale.client_checkout_id == checkout_id
        assert db_sale.comment == "Mobile sale test"
    finally:
        db.close()


def test_04_canonical_sale_items_created():
    p1 = _create_product(title="Monitor", qty=2, price=9000.0)
    p2 = _create_product(title="Cable", qty=10, price=300.0)
    checkout_id = str(uuid.uuid4())

    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [
            {"product_id": p1, "quantity": 1, "unit_price": 9000.0},
            {"product_id": p2, "quantity": 2, "unit_price": 300.0}
        ],
        "payment_method": "sbp"
    })
    assert resp.status_code == 200
    sale_id = resp.json()["sale_id"]

    db = SessionLocal()
    try:
        items = db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).all()
        assert len(items) == 2
        p_ids = {it.product_id for it in items}
        assert p_ids == {p1, p2}
        for it in items:
            if it.product_id == p1:
                assert it.quantity == 1
                assert it.price == 9000.0
            elif it.product_id == p2:
                assert it.quantity == 2
                assert it.price == 300.0
    finally:
        db.close()


def test_05_stock_decremented_exactly():
    p_id = _create_product(qty=4, price=500.0)
    checkout_id = str(uuid.uuid4())

    client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 3, "unit_price": 500.0}],
        "payment_method": "cash"
    })

    db = SessionLocal()
    try:
        prod = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert prod.quantity == 1
        assert prod.status == "in_stock"
    finally:
        db.close()

    # Sell the remaining 1
    checkout_id2 = str(uuid.uuid4())
    client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id2,
        "items": [{"product_id": p_id, "quantity": 1, "unit_price": 500.0}],
        "payment_method": "cash"
    })

    db = SessionLocal()
    try:
        prod = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert prod.quantity == 0
        assert prod.status == "sold"
        assert prod.storage_location == "archive"
    finally:
        db.close()


def test_06_stock_movements_correct():
    p_id = _create_product(qty=8, price=100.0)
    checkout_id = str(uuid.uuid4())

    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 3, "unit_price": 100.0}],
        "payment_method": "cash"
    })
    sale_id = resp.json()["sale_id"]

    db = SessionLocal()
    try:
        mov = db.query(models.StockMovement).filter(
            models.StockMovement.product_id == p_id,
            models.StockMovement.comment == f"Sale {sale_id}"
        ).first()
        assert mov is not None
        assert mov.movement_type == "sale"
        assert mov.quantity_delta == -3
        assert mov.old_quantity == 8
        assert mov.new_quantity == 5
        assert mov.reason == "sale"
    finally:
        db.close()


def test_07_receipt_number_and_result_correct():
    p_id = _create_product(title="Keyboard", qty=5, price=2000.0)
    checkout_id = str(uuid.uuid4())

    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 1, "unit_price": 2000.0}],
        "payment_method": "card",
        "cashier_name": "Павел"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["receipt_number"] == f"REC-{data['sale_id']:06d}"
    assert data["status"] == "completed"
    assert data["payment_label"] == "Безнал / карта"
    assert data["cashier_name"] == "Павел"
    assert data["items"][0]["title"] == "Keyboard"
    assert data["items"][0]["line_total"] == 2000.0


def test_08_payment_methods_persisted_correctly():
    valid_methods = ["cash", "card", "transfer", "sbp", "legal_entity_account", "mixed", "other"]
    for pm in valid_methods:
        p_id = _create_product(qty=2, price=100.0)
        resp = client.post("/api/sales/checkout", json={
            "client_checkout_id": str(uuid.uuid4()),
            "items": [{"product_id": p_id, "quantity": 1, "unit_price": 100.0}],
            "payment_method": pm
        })
        assert resp.status_code == 200, f"Failed on {pm}: {resp.text}"
        assert resp.json()["payment_method"] == pm


def test_09_custom_sale_price_persisted():
    p_id = _create_product(qty=5, price=5000.0)
    # Operator discounts price from 5000 to 4200
    checkout_id = str(uuid.uuid4())
    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 1, "unit_price": 4200.0}],
        "payment_method": "cash"
    })
    assert resp.status_code == 200
    assert resp.json()["total_amount"] == 4200.0
    assert resp.json()["items"][0]["unit_price"] == 4200.0


def test_16_unknown_product_full_rollback():
    checkout_id = str(uuid.uuid4())
    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [{"product_id": 9999999, "quantity": 1, "unit_price": 1000.0}],
        "payment_method": "cash"
    })
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()

    db = SessionLocal()
    try:
        assert db.query(models.Sale).filter(models.Sale.client_checkout_id == checkout_id).count() == 0
        assert db.query(models.CheckoutIdempotency).filter(models.CheckoutIdempotency.client_checkout_id == checkout_id).count() == 0
    finally:
        db.close()


def test_17_zero_stock_full_rollback():
    p_id = _create_product(qty=0, price=1000.0)
    checkout_id = str(uuid.uuid4())

    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 1, "unit_price": 1000.0}],
        "payment_method": "cash"
    })
    assert resp.status_code == 400
    assert "Insufficient quantity" in resp.json()["detail"]


def test_18_insufficient_stock_full_rollback():
    p_id = _create_product(qty=2, price=1000.0)
    checkout_id = str(uuid.uuid4())

    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 5, "unit_price": 1000.0}],
        "payment_method": "cash"
    })
    assert resp.status_code == 400
    assert "Insufficient quantity" in resp.json()["detail"]

    db = SessionLocal()
    try:
        prod = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert prod.quantity == 2  # Unchanged!
    finally:
        db.close()


def test_19_non_sellable_status_full_rollback():
    p1 = _create_product(qty=5, status="draft")
    resp1 = client.post("/api/sales/checkout", json={
        "client_checkout_id": str(uuid.uuid4()),
        "items": [{"product_id": p1, "quantity": 1, "unit_price": 500.0}],
        "payment_method": "cash"
    })
    assert resp1.status_code == 400
    assert "Cannot sell product" in resp1.json()["detail"]

    p2 = _create_product(qty=5, status="in_stock", storage_location="archive")
    resp2 = client.post("/api/sales/checkout", json={
        "client_checkout_id": str(uuid.uuid4()),
        "items": [{"product_id": p2, "quantity": 1, "unit_price": 500.0}],
        "payment_method": "cash"
    })
    assert resp2.status_code == 400
    assert "must be in 'store' location" in resp2.json()["detail"]


def test_20_invalid_quantity_full_rollback():
    p_id = _create_product(qty=5)
    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": str(uuid.uuid4()),
        "items": [{"product_id": p_id, "quantity": 0, "unit_price": 500.0}],
        "payment_method": "cash"
    })
    assert resp.status_code == 400
    assert "Item quantity must be > 0" in resp.json()["detail"]


def test_21_invalid_price_full_rollback():
    p_id = _create_product(qty=5)
    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": str(uuid.uuid4()),
        "items": [{"product_id": p_id, "quantity": 1, "unit_price": -50.0}],
        "payment_method": "cash"
    })
    assert resp.status_code == 400
    assert "Item price must be >= 0" in resp.json()["detail"]


def test_22_invalid_payment_method_full_rollback():
    p_id = _create_product(qty=5)
    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": str(uuid.uuid4()),
        "items": [{"product_id": p_id, "quantity": 1, "unit_price": 500.0}],
        "payment_method": "crypto"
    })
    assert resp.status_code == 400
    assert "Invalid payment method" in resp.json()["detail"]


def test_23_multi_line_one_bad_line_rolls_back_everything():
    p_good = _create_product(title="Good item", qty=10, price=100.0)
    p_bad = _create_product(title="Bad item", qty=1, price=100.0)
    checkout_id = str(uuid.uuid4())

    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [
            {"product_id": p_good, "quantity": 2, "unit_price": 100.0},
            {"product_id": p_bad, "quantity": 5, "unit_price": 100.0}  # Insufficient stock!
        ],
        "payment_method": "cash"
    })
    assert resp.status_code == 400
    assert "Insufficient quantity" in resp.json()["detail"]

    # Verify NOTHING was committed: p_good stock is untouched!
    db = SessionLocal()
    try:
        good_prod = db.query(models.Product).filter(models.Product.id == p_good).first()
        assert good_prod.quantity == 10
        assert db.query(models.Sale).filter(models.Sale.client_checkout_id == checkout_id).count() == 0
        assert db.query(models.StockMovement).filter(
            models.StockMovement.product_id == p_good,
            models.StockMovement.movement_type == "sale"
        ).count() == 0
    finally:
        db.close()


def test_24_same_idempotency_key_same_body_returns_same_sale():
    p_id = _create_product(qty=10, price=300.0)
    checkout_id = str(uuid.uuid4())

    payload = {
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 2, "unit_price": 300.0}],
        "payment_method": "cash"
    }

    resp1 = client.post("/api/sales/checkout", json=payload)
    assert resp1.status_code == 200
    sale1 = resp1.json()

    # Repeat with same key and same body
    resp2 = client.post("/api/sales/checkout", json=payload)
    assert resp2.status_code == 200
    sale2 = resp2.json()

    assert sale1["sale_id"] == sale2["sale_id"]
    assert sale1["receipt_number"] == sale2["receipt_number"]
    assert sale1["total_amount"] == sale2["total_amount"]


def test_25_retry_does_not_mutate_stock_second_time():
    p_id = _create_product(qty=10, price=300.0)
    checkout_id = str(uuid.uuid4())

    payload = {
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 2, "unit_price": 300.0}],
        "payment_method": "cash"
    }

    # First attempt
    resp1 = client.post("/api/sales/checkout", json=payload)
    assert resp1.status_code == 200

    db = SessionLocal()
    try:
        prod1 = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert prod1.quantity == 8
        sales_count1 = db.query(models.Sale).filter(models.Sale.client_checkout_id == checkout_id).count()
        assert sales_count1 == 1
        movs1 = db.query(models.StockMovement).filter(
            models.StockMovement.product_id == p_id,
            models.StockMovement.movement_type == "sale"
        ).count()
        assert movs1 == 1
    finally:
        db.close()

    # Retry with identical body
    resp2 = client.post("/api/sales/checkout", json=payload)
    assert resp2.status_code == 200

    db = SessionLocal()
    try:
        prod2 = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert prod2.quantity == 8  # Still 8! NOT decremented again!
        sales_count2 = db.query(models.Sale).filter(models.Sale.client_checkout_id == checkout_id).count()
        assert sales_count2 == 1  # Still exactly 1 sale!
        movs2 = db.query(models.StockMovement).filter(
            models.StockMovement.product_id == p_id,
            models.StockMovement.movement_type == "sale"
        ).count()
        assert movs2 == 1  # Still exactly 1 sale stock movement!
    finally:
        db.close()


def test_26_same_key_different_body_rejected_409():
    p1 = _create_product(qty=5, price=100.0)
    p2 = _create_product(qty=5, price=200.0)
    checkout_id = str(uuid.uuid4())

    payload1 = {
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p1, "quantity": 1, "unit_price": 100.0}],
        "payment_method": "cash"
    }
    resp1 = client.post("/api/sales/checkout", json=payload1)
    assert resp1.status_code == 200

    # Tampered / different body with same idempotency key
    payload2 = {
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p2, "quantity": 1, "unit_price": 200.0}],
        "payment_method": "cash"
    }
    resp2 = client.post("/api/sales/checkout", json=payload2)
    assert resp2.status_code == 409
    assert "Idempotency key reused with different request payload" in resp2.json()["detail"]


def test_27_simulated_lost_response_retry():
    p_id = _create_product(qty=6, price=700.0)
    checkout_id = str(uuid.uuid4())

    payload = {
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 2, "unit_price": 700.0}],
        "payment_method": "sbp"
    }

    # First request committed by server
    resp1 = client.post("/api/sales/checkout", json=payload)
    assert resp1.status_code == 200
    sale1_id = resp1.json()["sale_id"]

    # Client simulates having lost response, retries same request
    resp2 = client.post("/api/sales/checkout", json=payload)
    assert resp2.status_code == 200
    assert resp2.json()["sale_id"] == sale1_id

    db = SessionLocal()
    try:
        prod = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert prod.quantity == 4  # decremented only once: 6 - 2 = 4
        all_sales = db.query(models.Sale).filter(models.Sale.client_checkout_id == checkout_id).all()
        assert len(all_sales) == 1
    finally:
        db.close()


def test_28_concurrent_one_unit_checkout_exactly_one_succeeds():
    p_id = _create_product(qty=1, price=1000.0)
    cid1 = str(uuid.uuid4())
    cid2 = str(uuid.uuid4())

    def do_checkout(cid):
        # Create a fresh TestClient per thread
        c = TestClient(app)
        return c.post("/api/sales/checkout", json={
            "client_checkout_id": cid,
            "items": [{"product_id": p_id, "quantity": 1, "unit_price": 1000.0}],
            "payment_method": "cash"
        })

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(do_checkout, cid1)
        f2 = executor.submit(do_checkout, cid2)
        r1 = f1.result()
        r2 = f2.result()

    statuses = [r1.status_code, r2.status_code]
    assert 200 in statuses, f"Expected one 200 OK, got: {statuses}"
    assert 400 in statuses, f"Expected one 400 Bad Request, got: {statuses}"

    db = SessionLocal()
    try:
        prod = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert prod.quantity == 0
        assert prod.status == "sold"
    finally:
        db.close()


def test_29_canceled_sale_logic_unaffected():
    p_id = _create_product(qty=5, price=800.0)
    checkout_id = str(uuid.uuid4())

    resp = client.post("/api/sales/checkout", json={
        "client_checkout_id": checkout_id,
        "items": [{"product_id": p_id, "quantity": 2, "unit_price": 800.0}],
        "payment_method": "cash"
    })
    assert resp.status_code == 200
    sale_id = resp.json()["sale_id"]

    db = SessionLocal()
    try:
        prod = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert prod.quantity == 3
    finally:
        db.close()

    # Cancel sale
    cancel_resp = client.post(f"/api/sales/{sale_id}/cancel", json={
        "reason": "Customer changed mind",
        "canceled_by": "Administrator"
    })
    assert cancel_resp.status_code == 200

    db = SessionLocal()
    try:
        canceled_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
        assert canceled_sale.status == "canceled"
        prod_restored = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert prod_restored.quantity == 5  # Restored!
    finally:
        db.close()


def test_30_desktop_sale_regression_unaffected():
    p_id = _create_product(qty=4, price=1100.0)
    resp = client.post("/api/sales/", json={
        "payment_method": "cash",
        "items": [{"product_id": p_id, "quantity": 1, "price": 1100.0}]
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_amount"] == 1100.0
    assert data["status"] == "completed"

    db = SessionLocal()
    try:
        prod = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert prod.quantity == 3
    finally:
        db.close()
