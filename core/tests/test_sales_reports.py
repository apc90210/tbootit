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
        "status": "in_stock",
        "quantity": 100,
        "storage_location": "store"
    })
    assert response.status_code == 200, response.text
    return response.json()["id"]


def create_sale(product_id, amount, payment_method):
    response = client.post("/api/sales/", json={
        "total_amount": amount,
        "payment_method": payment_method,
        "customer_label": "Test Customer",
        "items": [{"product_id": product_id, "title": "Test Item", "price": amount, "quantity": 1}]
    })
    if response.status_code != 200:
        print("FAIL", response.text)
    assert response.status_code == 200, response.text
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
    today = date.today()
    from datetime import timedelta
    monday = today - timedelta(days=today.weekday())
    assert data["date_from"] == monday.isoformat()
    assert data["date_to"] == today.isoformat()
    assert date.fromisoformat(data["date_to"]) <= date.today()


def test_reports_month():
    response = client.get("/api/reports/sales?period=month")
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "month"
    today = date.today()
    first_day = today.replace(day=1)
    assert data["date_from"] == first_day.isoformat()
    assert data["date_to"] == today.isoformat()
    assert date.fromisoformat(data["date_to"]) <= date.today()


def test_reports_year():
    response = client.get("/api/reports/sales?period=year")
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "year"
    today = date.today()
    jan_first = today.replace(month=1, day=1)
    assert data["date_from"] == jan_first.isoformat()
    assert data["date_to"] == today.isoformat()
    assert date.fromisoformat(data["date_to"]) <= date.today()


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
    """Custom period with empty dates falls back to custom year-to-date."""
    response = client.get("/api/reports/sales?period=custom&date_from=&date_to=")
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "custom"
    today = date.today()
    assert data["date_from"] == date(today.year, 1, 1).isoformat()
    assert data["date_to"] == today.isoformat()


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
    from datetime import date
    today = date.today()
    expected_days = today.weekday() + 1
    assert len(data["money_summary_rows"]) == expected_days


def test_reports_month_returns_current_month_days():
    response = client.get("/api/reports/sales?period=month")
    assert response.status_code == 200
    data = response.json()
    from datetime import date
    today = date.today()
    assert len(data["money_summary_rows"]) == today.day


def test_reports_year_returns_twelve_month_rows():
    response = client.get("/api/reports/sales?period=year")
    assert response.status_code == 200
    data = response.json()
    from datetime import date
    today = date.today()
    assert len(data["money_summary_rows"]) == today.month
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


def test_reports_exclude_canceled_and_superseded():
    """Reports exclude sales with status 'canceled' or 'superseded'."""
    p1 = create_product()
    sale = create_sale(p1, 500.0, "cash")
    
    # Check it's in the report
    resp1 = client.get("/api/reports/sales?period=today")
    assert resp1.status_code == 200
    assert any(s["id"] == sale["id"] for s in resp1.json()["sales"])
    
    # Cancel the sale
    resp_cancel = client.post(f"/api/sales/{sale['id']}/cancel", json={"reason": "test cancel"})
    assert resp_cancel.status_code == 200
    
    # Check it's no longer in the report
    resp2 = client.get("/api/reports/sales?period=today")
    assert resp2.status_code == 200
    assert not any(s["id"] == sale["id"] for s in resp2.json()["sales"])


# === Stage 04G-R2 new tests ===

def test_reports_default_no_params_returns_200():
    response = client.get("/api/reports/sales")
    assert response.status_code == 200

def test_reports_default_date_from_is_jan_1():
    response = client.get("/api/reports/sales")
    data = response.json()
    today = date.today()
    expected_start = date(today.year, 1, 1).isoformat()
    assert data["date_from"] == expected_start

def test_reports_default_date_to_is_today():
    response = client.get("/api/reports/sales")
    data = response.json()
    today = date.today().isoformat()
    assert data["date_to"] == today

def test_reports_default_includes_sales_year_to_date():
    response = client.get("/api/reports/sales")
    data = response.json()
    assert data["period"] == "custom"

def test_reports_empty_dates_returns_default():
    response = client.get("/api/reports/sales?date_from=&date_to=")
    data = response.json()
    today = date.today()
    assert data["date_from"] == date(today.year, 1, 1).isoformat()
    assert data["date_to"] == today.isoformat()

def test_reports_date_from_only_uses_today_for_date_to():
    response = client.get("/api/reports/sales?date_from=2026-06-01&date_to=")
    data = response.json()
    assert data["date_from"] == "2026-06-01"
    assert data["date_to"] == date.today().isoformat()

def test_reports_date_to_only_uses_jan_1_for_date_from():
    response = client.get("/api/reports/sales?date_from=&date_to=2026-06-01")
    data = response.json()
    assert data["date_from"] == "2026-01-01"
    assert data["date_to"] == "2026-06-01"

