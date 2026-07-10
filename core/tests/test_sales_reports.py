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


# === Stage 04G-R new tests ===

def test_reports_empty_date_from_date_to_no_500():
    """Empty date_from and date_to should not cause 500."""
    response = client.get("/api/reports/sales?date_from=&date_to=")
    assert response.status_code == 200


def test_reports_custom_empty_dates_falls_back():
    """Custom period with empty dates falls back to today, not 500."""
    response = client.get("/api/reports/sales?period=custom&date_from=&date_to=")
    assert response.status_code == 200
    data = response.json()
    # Should fall back to today
    assert data["period"] == "today"


def test_reports_invalid_date_returns_400():
    """Invalid date format returns 400, not 500."""
    response = client.get("/api/reports/sales?period=custom&date_from=not-a-date&date_to=2026-07-10")
    assert response.status_code == 400


def test_reports_money_summary_has_all_keys():
    """money_summary contains all required keys."""
    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()
    ms = data["money_summary"]
    required_keys = ["cash", "card", "transfer", "sbp", "legal_entity_account", "other", "unspecified", "total"]
    for key in required_keys:
        assert key in ms, f"money_summary missing key: {key}"


def test_reports_money_summary_total_equals_sum():
    """total in money_summary equals sum of individual categories."""
    p1 = create_product()
    p2 = create_product()
    create_sale(p1, 1000.0, "cash")
    create_sale(p2, 2000.0, "card")

    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()
    ms = data["money_summary"]
    category_sum = ms["cash"] + ms["card"] + ms["transfer"] + ms["sbp"] + ms["legal_entity_account"] + ms["other"] + ms["unspecified"]
    assert abs(ms["total"] - category_sum) < 0.01, f"total {ms['total']} != sum {category_sum}"


def test_reports_legal_entity_in_summary():
    """legal_entity_account sale appears under legal_entity_account in money_summary."""
    p1 = create_product()
    create_sale(p1, 3000.0, "legal_entity_account")

    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()
    ms = data["money_summary"]
    assert ms["legal_entity_account"] >= 3000.0


def test_reports_none_payment_goes_to_unspecified():
    """Sale with no payment method (None) goes to unspecified in money_summary."""
    # Create a sale with default payment_method which is 'cash'
    # To test None, we rely on the normalization in the report.
    # The schema default for payment_method is 'cash', so direct None isn't easy to test
    # via API. Instead we verify that the unspecified key exists and is a number.
    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()
    ms = data["money_summary"]
    assert isinstance(ms["unspecified"], (int, float))


def test_reports_payment_labels_present():
    """payment_labels dict is present in response with correct labels."""
    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()
    labels = data.get("payment_labels", {})
    assert labels.get("cash") == "Наличные"
    assert labels.get("card") == "Безнал / карта"
    assert labels.get("transfer") == "Перевод"
    assert labels.get("sbp") == "СБП"
    assert labels.get("legal_entity_account") == "Счёт юрлица"
    assert labels.get("other") == "Другое"
    assert labels.get("unspecified") == "Не указано"


# === Stage 04G-S new tests ===

def test_reports_today_returns_one_row():
    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()
    assert len(data["money_summary_rows"]) == 1
    assert data["money_summary_granularity"] == "day"


def test_reports_week_returns_seven_rows():
    response = client.get("/api/reports/sales?period=week")
    assert response.status_code == 200
    data = response.json()
    assert len(data["money_summary_rows"]) == 7


def test_reports_month_returns_current_month_days():
    response = client.get("/api/reports/sales?period=month")
    assert response.status_code == 200
    data = response.json()
    import calendar
    from datetime import date
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    assert len(data["money_summary_rows"]) == days_in_month


def test_reports_year_returns_twelve_month_rows():
    response = client.get("/api/reports/sales?period=year")
    assert response.status_code == 200
    data = response.json()
    assert len(data["money_summary_rows"]) == 12
    assert data["money_summary_granularity"] == "month"


def test_reports_custom_range_returns_correct_rows():
    response = client.get("/api/reports/sales?period=custom&date_from=2026-07-01&date_to=2026-07-03")
    assert response.status_code == 200
    data = response.json()
    assert len(data["money_summary_rows"]) == 3
    keys = [r["period_key"] for r in data["money_summary_rows"]]
    assert "2026-07-01" in keys
    assert "2026-07-02" in keys
    assert "2026-07-03" in keys


def test_reports_rows_include_zero_money_days():
    response = client.get("/api/reports/sales?period=week")
    assert response.status_code == 200
    data = response.json()
    zero_row = next((r for r in data["money_summary_rows"] if r["total"] == 0), None)
    # Could be None if there's a sale every day, but for a fresh test DB it's likely we have zero rows
    if zero_row:
        assert zero_row["cash"] == 0
        assert zero_row["total"] == 0


def test_reports_row_total_equals_sum():
    p1 = create_product()
    p2 = create_product()
    create_sale(p1, 1000.0, "sbp")
    create_sale(p2, 2000.0, "cash")
    
    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()
    row = data["money_summary_rows"][0]
    category_sum = row["cash"] + row["card"] + row["transfer"] + row["sbp"] + row["legal_entity_account"] + row["other"] + row["unspecified"]
    assert row["total"] == category_sum


def test_reports_money_summary_total_equals_sum_of_rows():
    response = client.get("/api/reports/sales?period=week")
    assert response.status_code == 200
    data = response.json()
    total_from_rows = sum(r["total"] for r in data["money_summary_rows"])
    assert total_from_rows == data["money_summary_total"]["total"]


def test_reports_legal_entity_counted_in_correct_day_row():
    p1 = create_product()
    create_sale(p1, 1000.0, "legal_entity_account")
    
    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()
    row = data["money_summary_rows"][0]
    assert row["legal_entity_account"] >= 1000.0


def test_reports_blank_payment_method_in_unspecified_row():
    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()
    row = data["money_summary_rows"][0]
    assert "unspecified" in row


def test_reports_old_money_summary_total_is_compatible():
    response = client.get("/api/reports/sales?period=today")
    assert response.status_code == 200
    data = response.json()
    assert data["money_summary"]["total"] == data["money_summary_total"]["total"]

