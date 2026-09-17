import os
import sys
import json
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


def _create_test_product(title: str, price: float, quantity: int = 5, status: str = "in_stock", location: str = "store") -> int:
    with SessionLocal() as db:
        prod = models.Product(
            title=title,
            sale_price=price,
            quantity=quantity,
            status=status,
            storage_location=location
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        return prod.id


def _get_product_data(product_id: int):
    with SessionLocal() as db:
        p = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not p:
            return None
        return {
            "quantity": p.quantity,
            "status": p.status,
            "storage_location": p.storage_location
        }


def _create_test_sale(items: list, payment_method: str = "cash", comment: str = "Test sale"):
    payload = {
        "payment_method": payment_method,
        "comment": comment,
        "items": items
    }
    resp = client.post("/api/sales/", json=payload)
    assert resp.status_code == 200, f"Failed to create sale: {resp.text}"
    return resp.json()


# 1. Payment method only edit
def test_01_payment_method_only():
    p1 = _create_test_product("Товар ПМ-1", 1000.0, 5)
    sale = _create_test_sale([{"product_id": p1, "title": "Товар ПМ-1", "price": 1000.0, "quantity": 1}], payment_method="cash")
    sale_id = sale["id"]

    correct_payload = {
        "payment_method": "transfer",
        "changed_by": "Тест Оператор",
        "comment": "Клиент оплатил переводом",
        "items": [{"product_id": p1, "title": "Товар ПМ-1", "price": 1000.0, "quantity": 1}]
    }
    resp = client.post(f"/api/sales/{sale_id}/correct", json=correct_payload)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["payment_method"] == "transfer"
    assert updated["total_amount"] == 1000.0
    assert updated["revision_count"] == 1

    # Product stock should remain unchanged (was 4 after sale, still 4)
    prod = _get_product_data(p1)
    assert prod["quantity"] == 4

    # Check revision
    revs_resp = client.get(f"/api/sales/{sale_id}/revisions")
    assert revs_resp.status_code == 200
    revs = revs_resp.json()["items"]
    assert len(revs) == 1
    assert revs[0]["revision_no"] == 1
    assert revs[0]["changed_by"] == "Тест Оператор"
    s_diff = json.loads(revs[0]["structured_diff"])
    assert s_diff["payment_method"] == {"old": "cash", "new": "transfer"}


# 2. Amount only edit
def test_02_amount_only():
    p1 = _create_test_product("Товар Цена-1", 2000.0, 5)
    sale = _create_test_sale([{"product_id": p1, "title": "Товар Цена-1", "price": 2000.0, "quantity": 1}])
    sale_id = sale["id"]

    correct_payload = {
        "payment_method": "cash",
        "changed_by": "Владелец",
        "comment": "Скидка постоянному клиенту",
        "items": [{"product_id": p1, "title": "Товар Цена-1", "price": 1800.0, "quantity": 1}]
    }
    resp = client.post(f"/api/sales/{sale_id}/correct", json=correct_payload)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["total_amount"] == 1800.0
    assert updated["revision_count"] == 1

    prod = _get_product_data(p1)
    assert prod["quantity"] == 4  # stock unaffected


# 3. Remove item -> stock restored
def test_03_remove_item_restores_stock():
    p1 = _create_test_product("Товар Удал-1", 1500.0, 2)
    p2 = _create_test_product("Товар Удал-2", 3000.0, 1)  # after sale will be 0 and sold

    sale = _create_test_sale([
        {"product_id": p1, "title": "Товар Удал-1", "price": 1500.0, "quantity": 1},
        {"product_id": p2, "title": "Товар Удал-2", "price": 3000.0, "quantity": 1}
    ])
    sale_id = sale["id"]

    # Verify p2 was sold out
    p2_db = _get_product_data(p2)
    assert p2_db["quantity"] == 0
    assert p2_db["status"] == "sold"

    # Remove p2 from sale
    correct_payload = {
        "items": [{"product_id": p1, "title": "Товар Удал-1", "price": 1500.0, "quantity": 1}]
    }
    resp = client.post(f"/api/sales/{sale_id}/correct", json=correct_payload)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["total_amount"] == 1500.0
    assert len(updated["items"]) == 1

    # Verify p2 stock is restored to 1 and status back to in_stock
    p2_restored = _get_product_data(p2)
    assert p2_restored["quantity"] == 1
    assert p2_restored["status"] == "in_stock"
    assert p2_restored["storage_location"] == "store"


# 4. Add item -> stock deducted
def test_04_add_item_deducts_stock():
    p1 = _create_test_product("Товар Доб-1", 1000.0, 5)
    p2 = _create_test_product("Товар Доб-2", 2500.0, 3)

    sale = _create_test_sale([{"product_id": p1, "title": "Товар Доб-1", "price": 1000.0, "quantity": 1}])
    sale_id = sale["id"]

    assert _get_product_data(p2)["quantity"] == 3

    # Add p2 (qty 2) to sale
    correct_payload = {
        "items": [
            {"product_id": p1, "title": "Товар Доб-1", "price": 1000.0, "quantity": 1},
            {"product_id": p2, "title": "Товар Доб-2", "price": 2500.0, "quantity": 2}
        ]
    }
    resp = client.post(f"/api/sales/{sale_id}/correct", json=correct_payload)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["total_amount"] == 6000.0
    assert len(updated["items"]) == 2

    # Verify p2 stock deducted: 3 - 2 = 1
    assert _get_product_data(p2)["quantity"] == 1


# 5. Replace item -> both reconciled
def test_05_replace_item_reconciles_both():
    p_old = _create_test_product("Старый Товар", 4000.0, 1)
    p_new = _create_test_product("Новый Товар", 4500.0, 5)

    sale = _create_test_sale([{"product_id": p_old, "title": "Старый Товар", "price": 4000.0, "quantity": 1}])
    sale_id = sale["id"]

    assert _get_product_data(p_old)["quantity"] == 0
    assert _get_product_data(p_old)["status"] == "sold"

    # Replace p_old with p_new
    correct_payload = {
        "items": [{"product_id": p_new, "title": "Новый Товар", "price": 4500.0, "quantity": 1}]
    }
    resp = client.post(f"/api/sales/{sale_id}/correct", json=correct_payload)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["total_amount"] == 4500.0

    # Old product returned to stock
    assert _get_product_data(p_old)["quantity"] == 1
    assert _get_product_data(p_old)["status"] == "in_stock"

    # New product deducted
    assert _get_product_data(p_new)["quantity"] == 4


# 6. Insufficient stock -> full rollback
def test_06_insufficient_stock_full_rollback():
    p1 = _create_test_product("Товар База", 1000.0, 5)
    p_short = _create_test_product("Товар Дефицит", 500.0, 1)

    sale = _create_test_sale([{"product_id": p1, "title": "Товар База", "price": 1000.0, "quantity": 1}])
    sale_id = sale["id"]

    # Try to add 5 of p_short (only 1 available)
    correct_payload = {
        "items": [
            {"product_id": p1, "title": "Товар База", "price": 1000.0, "quantity": 1},
            {"product_id": p_short, "title": "Товар Дефицит", "price": 500.0, "quantity": 5}
        ]
    }
    resp = client.post(f"/api/sales/{sale_id}/correct", json=correct_payload)
    assert resp.status_code == 400
    assert "Недостаточно товара" in resp.json()["detail"]

    # Verify sale is untouched
    current_sale = client.get(f"/api/sales/{sale_id}").json()
    assert current_sale["total_amount"] == 1000.0
    assert current_sale["revision_count"] == 0

    # Verify no revisions created
    revs = client.get(f"/api/sales/{sale_id}/revisions").json()["items"]
    assert len(revs) == 0

    # Verify stock untouched
    assert _get_product_data(p_short)["quantity"] == 1


# 7. One edit -> exactly one revision
def test_07_one_edit_one_revision():
    p = _create_test_product("Товар Рев-1", 700.0, 3)
    sale = _create_test_sale([{"product_id": p, "title": "Товар Рев-1", "price": 700.0, "quantity": 1}])
    sale_id = sale["id"]

    resp = client.post(f"/api/sales/{sale_id}/correct", json={
        "payment_method": "sbp",
        "items": [{"product_id": p, "title": "Товар Рев-1", "price": 700.0, "quantity": 1}]
    })
    assert resp.status_code == 200

    revs = client.get(f"/api/sales/{sale_id}/revisions").json()["items"]
    assert len(revs) == 1
    assert revs[0]["revision_no"] == 1
    assert revs[0]["sale_id"] == sale_id


# 8. Two edits -> revisions 1 and 2
def test_08_two_edits_revisions_1_and_2():
    p = _create_test_product("Товар Двойной", 500.0, 10)
    sale = _create_test_sale([{"product_id": p, "title": "Товар Двойной", "price": 500.0, "quantity": 1}])
    sale_id = sale["id"]

    # 1st edit: change price to 550
    resp1 = client.post(f"/api/sales/{sale_id}/correct", json={
        "items": [{"product_id": p, "title": "Товар Двойной", "price": 550.0, "quantity": 1}]
    })
    assert resp1.status_code == 200
    assert resp1.json()["revision_count"] == 1

    # 2nd edit: change quantity to 2 and payment to card
    resp2 = client.post(f"/api/sales/{sale_id}/correct", json={
        "payment_method": "card",
        "items": [{"product_id": p, "title": "Товар Двойной", "price": 550.0, "quantity": 2}]
    })
    assert resp2.status_code == 200
    assert resp2.json()["revision_count"] == 2
    assert resp2.json()["total_amount"] == 1100.0

    revs = client.get(f"/api/sales/{sale_id}/revisions").json()["items"]
    assert len(revs) == 2
    assert revs[0]["revision_no"] == 1
    assert revs[1]["revision_no"] == 2


# 9. Failed edit -> no revision
def test_09_failed_edit_no_revision():
    p = _create_test_product("Товар Провал", 300.0, 2)
    sale = _create_test_sale([{"product_id": p, "title": "Товар Провал", "price": 300.0, "quantity": 1}])
    sale_id = sale["id"]

    # Invalid payment method
    resp = client.post(f"/api/sales/{sale_id}/correct", json={
        "payment_method": "crypto_invalid",
        "items": [{"product_id": p, "title": "Товар Провал", "price": 300.0, "quantity": 1}]
    })
    assert resp.status_code == 400

    revs = client.get(f"/api/sales/{sale_id}/revisions").json()["items"]
    assert len(revs) == 0


# 10. Reports use corrected amount/payment without duplicate revenue
def test_10_reports_use_corrected_state_no_double_revenue():
    p = _create_test_product("Товар Отчёт", 10000.0, 5)
    sale = _create_test_sale([{"product_id": p, "title": "Товар Отчёт", "price": 10000.0, "quantity": 1}], payment_method="cash")
    sale_id = sale["id"]

    # Check report before edit
    rep_before = client.get("/api/reports/sales?period=today").json()
    initial_total = rep_before["total_amount"]

    # Correct sale: discount to 8000 and switch to sbp
    resp = client.post(f"/api/sales/{sale_id}/correct", json={
        "payment_method": "sbp",
        "items": [{"product_id": p, "title": "Товар Отчёт", "price": 8000.0, "quantity": 1}]
    })
    assert resp.status_code == 200

    # Check report after edit
    rep_after = client.get("/api/reports/sales?period=today").json()
    # Total should have decreased by 2000 (from 10000 to 8000), not increased by 8000!
    expected_total = initial_total - 2000.0
    assert abs(rep_after["total_amount"] - expected_total) < 0.01
    assert rep_after["sales_count"] == rep_before["sales_count"]  # No duplicate sale counted!


# 11. Receipt uses corrected state
def test_11_receipt_uses_corrected_state():
    p = _create_test_product("Товар Чек", 1200.0, 4)
    sale = _create_test_sale([{"product_id": p, "title": "Товар Чек", "price": 1200.0, "quantity": 1}])
    sale_id = sale["id"]

    client.post(f"/api/sales/{sale_id}/correct", json={
        "payment_method": "transfer",
        "items": [{"product_id": p, "title": "Товар Чек", "price": 1100.0, "quantity": 2}]
    })

    # Query sale from API (used by receipt)
    sale_data = client.get(f"/api/sales/{sale_id}").json()
    assert sale_data["total_amount"] == 2200.0
    assert sale_data["payment_method"] == "transfer"
    assert sale_data["revision_count"] == 1
    assert sale_data["items"][0]["quantity"] == 2
    assert sale_data["items"][0]["price"] == 1100.0


# 12. Canceled sale cannot be directly corrected
def test_12_canceled_sale_cannot_be_directly_corrected():
    p = _create_test_product("Товар Отмена", 800.0, 2)
    sale = _create_test_sale([{"product_id": p, "title": "Товар Отмена", "price": 800.0, "quantity": 1}])
    sale_id = sale["id"]

    # Cancel sale
    cancel_resp = client.post(f"/api/sales/{sale_id}/cancel", json={"reason": "Возврат клиентом"})
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "canceled"

    # Attempt correction
    correct_resp = client.post(f"/api/sales/{sale_id}/correct", json={
        "items": [{"product_id": p, "title": "Товар Отмена", "price": 700.0, "quantity": 1}]
    })
    assert correct_resp.status_code == 400
    assert "cannot be corrected" in correct_resp.json()["detail"]


# 13. Automatic Avito deactivation still disabled
def test_13_automatic_avito_deactivation_still_disabled():
    import app.routers.avito_post_sale as avito_module
    assert avito_module.OFFICIAL_API_AVAILABLE is False


# 14. Manual Avito task handling remains canonical
def test_14_manual_avito_task_handling_remains_canonical():
    import uuid
    uid = uuid.uuid4().hex[:8]
    p = _create_test_product("Товар Авито Задача", 3500.0, 2)
    with SessionLocal() as db:
        ext = models.ProductExternalListing(
            product_id=p,
            marketplace="avito",
            external_account_key="test_acc",
            external_item_id=f"avito_{uid}",
            remote_status="active"
        )
        db.add(ext)
        db.commit()

    sale = _create_test_sale([{"product_id": p, "title": "Товар Авито Задача", "price": 3500.0, "quantity": 1}])
    sale_id = sale["id"]

    # Inspect avito tasks endpoint
    tasks_resp = client.get(f"/api/sales/{sale_id}/avito-tasks")
    assert tasks_resp.status_code == 200
    data = tasks_resp.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["status"] == "suggested"

    # Remove product from sale -> task canceled
    p_dummy = _create_test_product("Товар Замена", 500.0, 5)
    resp = client.post(f"/api/sales/{sale_id}/correct", json={
        "items": [{"product_id": p_dummy, "title": "Товар Замена", "price": 500.0, "quantity": 1}]
    })
    assert resp.status_code == 200

    with SessionLocal() as db:
        task_in_db = db.query(models.AvitoPostSaleTask).filter(
            models.AvitoPostSaleTask.sale_id == sale_id,
            models.AvitoPostSaleTask.product_id == p
        ).first()
        assert task_in_db.status == "canceled"


# 15. Production-synced existing sales remain readable
def test_15_production_synced_existing_sales_remain_readable():
    resp = client.get("/api/sales/?limit=10")
    assert resp.status_code == 200
    sales = resp.json()["items"]
    assert isinstance(sales, list)
    for s in sales:
        assert "id" in s
        assert "total_amount" in s
        assert "revision_count" in s
        assert s["revision_count"] >= 0
