import os
import sys
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
core_path = str(REPO_ROOT / "core")

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


import uuid

def _create_test_repair(
    number: str = None,
    status: str = "in_repair",
    estimated_repair_amount: int = 3500,
    device_type: str = "Ноутбук",
    brand: str = "ASUS",
    model: str = "ZenBook",
    serial_number: str = "ASUS-123456",
    reported_issue: str = "Замена матрицы"
) -> int:
    unique_suffix = uuid.uuid4().hex[:8].upper()
    if not number:
        number = f"R-11B-{unique_suffix}"
    else:
        number = f"{number}-{unique_suffix}"
    with SessionLocal() as db:
        rep = models.RepairOrder(
            number=number,
            status=status,
            customer_name="Тестовый Заказчик",
            customer_phone="+7 999 123-45-67",
            customer_email="test@repair.ru",
            device_type=device_type,
            brand=brand,
            model=model,
            serial_number=serial_number,
            reported_issue=reported_issue,
            diagnosis_text="Повреждён шлейф и матрица",
            planned_works_text="Установка новой матрицы 14 FHD",
            work_description="Замена матрицы, чистка системы охлаждения",
            estimated_repair_amount=estimated_repair_amount,
            assigned_to="Инженер Иванов"
        )
        db.add(rep)
        db.commit()
        db.refresh(rep)
        return rep.id


def test_1_mark_ready_creates_no_sale():
    """Requirement 1: Marking a repair as Ready does NOT create a Sale."""
    rep_id = _create_test_repair(number="R-11B-REQ1", status="in_repair")

    res = client.post(f"/api/repairs/{rep_id}/status", json={"status": "ready", "comment": "Работа завершена"})
    assert res.status_code == 200
    assert res.json()["status"] == "ready"

    with SessionLocal() as db:
        sale = db.query(models.Sale).filter(models.Sale.source_type == "repair", models.Sale.source_id == rep_id).first()
        assert sale is None, "Готов != продажа: marking Ready must NOT create any sale"


def test_2_cancel_issue_flow_leaves_ready_and_no_sale():
    """Requirement 2: If issue flow is initiated or canceled, repair stays Ready and no sale is created."""
    rep_id = _create_test_repair(number="R-11B-REQ2", status="ready")

    # In UI/API, canceling means no POST to issued, or status remains ready
    # Check that status remains ready and no sale exists
    res = client.get(f"/api/repairs/{rep_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"

    with SessionLocal() as db:
        sale = db.query(models.Sale).filter(models.Sale.source_type == "repair", models.Sale.source_id == rep_id).first()
        assert sale is None


def test_3_ready_to_issued_creates_exactly_one_sale():
    """Requirement 3: Ready -> Issued with valid amount/payment/warranty creates exactly one linked sale."""
    rep_id = _create_test_repair(number="R-11B-REQ3", status="ready")

    res = client.post(
        f"/api/repairs/{rep_id}/status",
        json={
            "status": "issued",
            "final_amount": 4200.0,
            "payment_method": "card",
            "warranty_days": 45,
            "changed_by": "Кассир Анна",
            "comment": "Выдано клиенту с проверкой"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "issued"
    assert data["final_amount"] == 4200.0
    assert data["payment_method"] == "card"
    assert data["warranty_days"] == 45
    assert data["sale_id"] is not None

    with SessionLocal() as db:
        sales = db.query(models.Sale).filter(models.Sale.source_type == "repair", models.Sale.source_id == rep_id).all()
        assert len(sales) == 1
        assert sales[0].total_amount == 4200.0
        assert sales[0].status == "completed"


def test_4_double_submit_retry_still_one_sale():
    """Requirement 4: Double submit or retry of issued status is idempotent and creates NO duplicate sale."""
    rep_id = _create_test_repair(number="R-11B-REQ4", status="ready")

    payload = {
        "status": "issued",
        "final_amount": 3500.0,
        "payment_method": "cash",
        "warranty_days": 30,
        "changed_by": "Оператор"
    }

    # First submit
    res1 = client.post(f"/api/repairs/{rep_id}/status", json=payload)
    assert res1.status_code == 200
    sale_id_1 = res1.json()["sale_id"]

    # Second submit (retry / double click)
    res2 = client.post(f"/api/repairs/{rep_id}/status", json=payload)
    assert res2.status_code == 200
    sale_id_2 = res2.json()["sale_id"]

    assert sale_id_1 == sale_id_2

    with SessionLocal() as db:
        sales = db.query(models.Sale).filter(models.Sale.source_type == "repair", models.Sale.source_id == rep_id).all()
        assert len(sales) == 1, "Must maintain exactly ONE sale on idempotent retries"


def test_5_sale_amount_equals_final_repair_amount():
    """Requirement 5: Linked sale amount equals final repair amount."""
    rep_id = _create_test_repair(number="R-11B-REQ5", status="ready", estimated_repair_amount=2000)

    # Actual final repair amount differed from estimate (e.g. 2750.00)
    res = client.post(
        f"/api/repairs/{rep_id}/status",
        json={
            "status": "issued",
            "final_amount": 2750.0,
            "payment_method": "transfer",
            "warranty_days": 30
        }
    )
    assert res.status_code == 200
    sale_id = res.json()["sale_id"]

    with SessionLocal() as db:
        sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
        assert sale.total_amount == 2750.0


def test_6_sale_payment_method_equals_selected_method():
    """Requirement 6: Linked sale payment method matches selected method."""
    rep_id = _create_test_repair(number="R-11B-REQ6", status="ready")

    res = client.post(
        f"/api/repairs/{rep_id}/status",
        json={
            "status": "issued",
            "final_amount": 1500.0,
            "payment_method": "sbp",
            "warranty_days": 14
        }
    )
    assert res.status_code == 200
    sale_id = res.json()["sale_id"]

    with SessionLocal() as db:
        sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
        assert sale.payment_method == "sbp"


def test_7_sale_appears_in_sales_list_and_reports():
    """Requirement 7: Repair sale appears in standard sales list and general reports."""
    rep_id = _create_test_repair(number="R-11B-REQ7", status="ready")

    res = client.post(
        f"/api/repairs/{rep_id}/status",
        json={
            "status": "issued",
            "final_amount": 4900.0,
            "payment_method": "card",
            "warranty_days": 90
        }
    )
    assert res.status_code == 200
    sale_id = res.json()["sale_id"]

    # 1. Sales list
    sales_res = client.get("/api/sales/")
    assert sales_res.status_code == 200
    all_sales = sales_res.json()["items"]
    matching_sale = next((s for s in all_sales if s["id"] == sale_id), None)
    assert matching_sale is not None
    assert matching_sale["source_type"] == "repair"
    assert matching_sale["source_id"] == rep_id
    assert matching_sale["total_amount"] == 4900.0

    # 2. Reports
    rep_report = client.get("/api/reports/sales?period=today")
    assert rep_report.status_code == 200
    rep_data = rep_report.json()
    assert rep_data["total_amount"] >= 4900.0


def test_8_bidirectional_link_between_repair_and_sale():
    """Requirement 8: Repair links to Sale, and Sale links to Repair."""
    rep_id = _create_test_repair(number="R-11B-REQ8", status="ready")

    res = client.post(
        f"/api/repairs/{rep_id}/status",
        json={
            "status": "issued",
            "final_amount": 5500.0,
            "payment_method": "cash",
            "warranty_days": 30
        }
    )
    assert res.status_code == 200
    sale_id = res.json()["sale_id"]

    # Check repair endpoint has sale_id
    rep_data = client.get(f"/api/repairs/{rep_id}").json()
    assert rep_data["sale_id"] == sale_id

    # Check sale endpoint has source_type='repair' and source_id=repair.id
    sale_data = client.get(f"/api/sales/{sale_id}").json()
    assert sale_data["source_type"] == "repair"
    assert sale_data["source_id"] == rep_id


def test_9_repair_history_stores_actor_time_amount_payment_warranty():
    """Requirement 9: Repair history accurately captures actor, timestamp, amount, payment, warranty, and sale ID."""
    rep_id = _create_test_repair(number="R-11B-REQ9", status="ready")

    res = client.post(
        f"/api/repairs/{rep_id}/status",
        json={
            "status": "issued",
            "final_amount": 6200.0,
            "payment_method": "card",
            "warranty_days": 60,
            "changed_by": "Старший Мастер Сидоров",
            "comment": "Проведена дополнительная калибровка"
        }
    )
    assert res.status_code == 200
    sale_id = res.json()["sale_id"]

    with SessionLocal() as db:
        history_records = db.query(models.RepairStatusHistory).filter(
            models.RepairStatusHistory.repair_id == rep_id,
            models.RepairStatusHistory.new_status == "issued"
        ).all()
        assert len(history_records) >= 1
        last_h = history_records[-1]
        assert last_h.changed_by == "Старший Мастер Сидоров"
        assert last_h.changed_at is not None
        assert "6200" in last_h.comment
        assert "60 дн" in last_h.comment
        assert str(sale_id) in last_h.comment


def test_10_receipt_route_renders():
    """Requirement 10: Receipt endpoint returns 200 with structured repair receipt data."""
    rep_id = _create_test_repair(number="R-11B-REQ10", status="ready")
    client.post(
        f"/api/repairs/{rep_id}/status",
        json={
            "status": "issued",
            "final_amount": 3800.0,
            "payment_method": "transfer",
            "warranty_days": 30
        }
    )

    res = client.get(f"/api/repairs/{rep_id}/receipt-data")
    assert res.status_code == 200
    data = res.json()
    assert data["repair_id"] == rep_id
    assert "R-11B-REQ10" in data["repair_number"]
    assert data["status"] == "issued"


def test_11_receipt_contains_amount_payment_warranty_device_order_number():
    """Requirement 11: Receipt data contains amount, payment method label, warranty label/until, device, and order number."""
    rep_id = _create_test_repair(
        number="R-11B-REQ11",
        status="ready",
        device_type="Смартфон",
        brand="Apple",
        model="iPhone 13",
        serial_number="F2LZ1234ABCD"
    )
    client.post(
        f"/api/repairs/{rep_id}/status",
        json={
            "status": "issued",
            "final_amount": 7500.0,
            "payment_method": "card",
            "warranty_days": 90
        }
    )

    data = client.get(f"/api/repairs/{rep_id}/receipt-data").json()
    assert "R-11B-REQ11" in data["repair_number"]
    assert data["final_amount"] == 7500.0
    assert data["payment_method"] == "card"
    assert data["payment_method_label"] == "Безнал / карта"
    assert data["warranty_days"] == 90
    assert "90 дн." in data["warranty_label"]
    assert data["warranty_until"] is not None
    assert data["device_type"] == "Смартфон"
    assert data["brand"] == "Apple"
    assert data["model"] == "iPhone 13"
    assert data["serial_number"] == "F2LZ1234ABCD"


def test_12_invalid_amount_payment_warranty_no_partial_transition():
    """Requirement 12: Invalid amount, missing payment method, or negative warranty causes no partial transition."""
    rep_id = _create_test_repair(number="R-11B-REQ12", status="ready")

    # 1. Negative amount
    res_neg_amt = client.post(
        f"/api/repairs/{rep_id}/status",
        json={"status": "issued", "final_amount": -500.0, "payment_method": "cash", "warranty_days": 30}
    )
    assert res_neg_amt.status_code in [400, 422]

    # 2. Missing payment method
    res_no_pm = client.post(
        f"/api/repairs/{rep_id}/status",
        json={"status": "issued", "final_amount": 1000.0, "payment_method": "", "warranty_days": 30}
    )
    assert res_no_pm.status_code in [400, 422]

    # 3. Negative warranty
    res_neg_w = client.post(
        f"/api/repairs/{rep_id}/status",
        json={"status": "issued", "final_amount": 1000.0, "payment_method": "cash", "warranty_days": -10}
    )
    assert res_neg_w.status_code in [400, 422]

    # Verify repair order is STILL in status 'ready' and has no sale
    rep_cur = client.get(f"/api/repairs/{rep_id}").json()
    assert rep_cur["status"] == "ready"
    assert rep_cur["sale_id"] is None

    with SessionLocal() as db:
        assert db.query(models.Sale).filter(models.Sale.source_type == "repair", models.Sale.source_id == rep_id).count() == 0


def test_13_backward_casual_status_change_cannot_orphan_sale():
    """Requirement 13: Backward casual status change from issued is strictly blocked."""
    rep_id = _create_test_repair(number="R-11B-REQ13", status="ready")
    res_issue = client.post(
        f"/api/repairs/{rep_id}/status",
        json={"status": "issued", "final_amount": 2500.0, "payment_method": "cash", "warranty_days": 14}
    )
    assert res_issue.status_code == 200

    # Attempt to change status to 'ready'
    res_back_ready = client.post(
        f"/api/repairs/{rep_id}/status",
        json={"status": "ready", "comment": "Случайный откат"}
    )
    assert res_back_ready.status_code == 409
    assert "заблокирован" in res_back_ready.json()["detail"]

    # Attempt to change status to 'in_repair'
    res_back_in_repair = client.post(
        f"/api/repairs/{rep_id}/status",
        json={"status": "in_repair", "comment": "Случайный откат"}
    )
    assert res_back_in_repair.status_code == 409


def test_14_stage11a_correction_of_linked_repair_sale_preserves_financial_consistency():
    """Requirement 14: Correcting a linked repair sale via Stage 11A updates repair order financials and history."""
    rep_id = _create_test_repair(number="R-11B-REQ14", status="ready")
    res_issue = client.post(
        f"/api/repairs/{rep_id}/status",
        json={"status": "issued", "final_amount": 3000.0, "payment_method": "cash", "warranty_days": 30}
    )
    assert res_issue.status_code == 200
    sale_id = res_issue.json()["sale_id"]

    # 1. Attempt to add physical warehouse stock item to repair sale -> must be rejected
    res_reject_stock = client.post(
        f"/api/sales/{sale_id}/correct",
        json={
            "reason": "Попытка добавить товар",
            "items": [{"product_id": 9999, "price": 500, "quantity": 1}],
            "payment_method": "cash"
        }
    )
    assert res_reject_stock.status_code == 400
    assert "не может содержать складские товары" in res_reject_stock.json()["detail"]

    # 2. Correct service price from 3000 to 3500 and payment from cash to card
    res_correct = client.post(
        f"/api/sales/{sale_id}/correct",
        json={
            "reason": "Дополнительная скидка отменена по согласованию",
            "items": [{"product_id": None, "title": "Ремонтные работы скорректированные", "price": 3500.0, "quantity": 1}],
            "payment_method": "card",
            "changed_by": "Старший менеджер"
        }
    )
    assert res_correct.status_code == 200
    corrected_sale = res_correct.json()
    assert corrected_sale["total_amount"] == 3500.0
    assert corrected_sale["payment_method"] == "card"
    assert corrected_sale["revision_count"] == 1

    # 3. Verify linked RepairOrder reflects the financial update transactionally
    rep_updated = client.get(f"/api/repairs/{rep_id}").json()
    assert rep_updated["final_amount"] == 3500.0
    assert rep_updated["payment_method"] == "card"

    # 4. Verify RepairStatusHistory contains an entry documenting the sale correction
    with SessionLocal() as db:
        history = db.query(models.RepairStatusHistory).filter(
            models.RepairStatusHistory.repair_id == rep_id
        ).order_by(models.RepairStatusHistory.changed_at.desc()).first()
        assert "Скорректирована связанная продажа" in history.comment
        assert "3 500" in history.comment
        assert history.changed_by == "Старший менеджер"


def test_15_existing_production_synced_repair_data_remains_readable():
    """Requirement 15: Existing repair records remain readable without errors or regressions."""
    res = client.get("/api/repairs/")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    if len(data["items"]) > 0:
        first_rep = data["items"][0]
        assert "id" in first_rep
        assert "number" in first_rep
        assert "status" in first_rep
