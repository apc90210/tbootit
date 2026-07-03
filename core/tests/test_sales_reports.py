import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from datetime import date

client = TestClient(app)


def create_product(suffix=None):
    suffix = suffix or str(uuid.uuid4())[:8]
    response = client.post("/api/products/", json={
        "sku": f"RPT-{suffix}",
        "title": f"Report Test Product {suffix}",
        "sale_price": 1000.0,
        "status": "in_stock"
    })
    assert response.status_code == 200
    return response.json()["id"]


def create_sale(product_id, amount, payment_method):
    response = client.post("/api/sales/", json={
        "total_amount": amount,
        "payment_method": payment_method,
        "customer_label": "Test Customer",
        "items": [{"product_id": product_id, "title": "Test Item", "price": amount, "quantity": 1}]
    })
    assert response.status_code == 200
    return response.json()


def test_reports_today_basic():
    """Report today returns correct totals and breakdown."""
    p1 = create_product()
    p2 = create_product()
    p3 = create_product()

    create_sale(p1, 1000.0, "cash")
    create_sale(p2, 2000.0, "legal_entity_account")
    create_sale(p3, 500.0, "sbp")

    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()

    assert data["period"] == "today"
    assert data["date_from"] == date.today().isoformat()
    assert data["date_to"] == date.today().isoformat()

    assert data["total_amount"] >= 3500.0
    assert data["sales_count"] >= 3
    assert data["items_count"] >= 3

    breakdown_dict = {b["payment_method"]: b for b in data["payment_breakdown"]}

    assert "legal_entity_account" in breakdown_dict
    assert breakdown_dict["legal_entity_account"]["label"] == "Счёт юрлица"
    assert breakdown_dict["legal_entity_account"]["amount"] >= 2000.0

    assert "cash" in breakdown_dict
    assert breakdown_dict["cash"]["amount"] >= 1000.0

    assert "sbp" in breakdown_dict
    assert breakdown_dict["sbp"]["label"] == "СБП"
    assert breakdown_dict["sbp"]["amount"] >= 500.0


def test_reports_sales_list_has_payment_labels():
    """Each sale in report has a correct payment_method_label."""
    p1 = create_product()
    create_sale(p1, 1500.0, "legal_entity_account")

    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()

    sales = data["sales"]
    legal_sales = [s for s in sales if s["payment_method"] == "legal_entity_account"]
    assert len(legal_sales) > 0
    assert legal_sales[0]["payment_method_label"] == "Счёт юрлица"


def test_reports_custom_period():
    """Custom period filter works."""
    today = date.today().isoformat()
    response = client.get(f"/api/reports/sales?period=custom&date_from={today}&date_to={today}")
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "custom"
    assert data["date_from"] == today


def test_reports_week():
    response = client.get("/api/reports/sales?period=week")
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "week"
    assert data["sales_count"] >= 0


def test_reports_month():
    response = client.get("/api/reports/sales?period=month")
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "month"


def test_reports_year():
    response = client.get("/api/reports/sales?period=year")
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "year"


def test_reports_invalid_payment_method_rejected():
    """Invalid payment method is still rejected by sales endpoint."""
    p1 = create_product()
    response = client.post("/api/sales/", json={
        "total_amount": 100.0,
        "payment_method": "bitcoin",
        "items": [{"product_id": p1, "title": "X", "price": 100.0, "quantity": 1}]
    })
    assert response.status_code == 400


def test_legal_entity_account_accepted():
    """legal_entity_account is accepted as a payment method."""
    p1 = create_product()
    response = client.post("/api/sales/", json={
        "total_amount": 5000.0,
        "payment_method": "legal_entity_account",
        "items": [{"product_id": p1, "title": "LegalTest", "price": 5000.0, "quantity": 1}]
    })
    assert response.status_code == 200
    assert response.json()["payment_method"] == "legal_entity_account"


def test_sbp_accepted():
    """sbp is accepted as a payment method."""
    p1 = create_product()
    response = client.post("/api/sales/", json={
        "total_amount": 750.0,
        "payment_method": "sbp",
        "items": [{"product_id": p1, "title": "SbpTest", "price": 750.0, "quantity": 1}]
    })
    assert response.status_code == 200
    assert response.json()["payment_method"] == "sbp"
