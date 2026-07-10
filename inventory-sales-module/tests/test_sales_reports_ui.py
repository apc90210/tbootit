import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

# Full mock report data with money_summary and payment_labels
MOCK_REPORT_DATA = {
    "period": "today",
    "date_from": "2026-07-10",
    "date_to": "2026-07-10",
    "total_amount": 6500.0,
    "sales_count": 4,
    "items_count": 7,
    "payment_breakdown": [
        {
            "payment_method": "legal_entity_account",
            "label": "Счёт юрлица",
            "amount": 3000.0,
            "sales_count": 1
        },
        {
            "payment_method": "cash",
            "label": "Наличные",
            "amount": 1000.0,
            "sales_count": 1
        },
        {
            "payment_method": "card",
            "label": "Безнал / карта",
            "amount": 2000.0,
            "sales_count": 1
        },
        {
            "payment_method": "sbp",
            "label": "СБП",
            "amount": 500.0,
            "sales_count": 1
        }
    ],
    "money_summary_rows": [
        {
            "period_key": "2026-07-10",
            "label": "10.07.2026",
            "cash": 1000.0,
            "card": 2000.0,
            "transfer": 0.0,
            "sbp": 500.0,
            "legal_entity_account": 3000.0,
            "other": 0.0,
            "unspecified": 0.0,
            "total": 6500.0
        }
    ],
    "money_summary_total": {
        "cash": 1000.0,
        "card": 2000.0,
        "transfer": 0.0,
        "sbp": 500.0,
        "legal_entity_account": 3000.0,
        "other": 0.0,
        "unspecified": 0.0,
        "total": 6500.0
    },
    "money_summary_granularity": "day",
    "money_summary": {
        "cash": 1000.0,
        "card": 2000.0,
        "transfer": 0.0,
        "sbp": 500.0,
        "legal_entity_account": 3000.0,
        "other": 0.0,
        "unspecified": 0.0,
        "total": 6500.0
    },
    "payment_labels": {
        "cash": "Наличные",
        "card": "Безнал / карта",
        "transfer": "Перевод",
        "sbp": "СБП",
        "legal_entity_account": "Счёт юрлица",
        "other": "Другое",
        "unspecified": "Не указано"
    },
    "sales": [
        {
            "id": 1,
            "created_at": "2026-07-10T10:00:00",
            "total_amount": 3000.0,
            "items_count": 2,
            "payment_method": "legal_entity_account",
            "payment_method_label": "Счёт юрлица",
            "comment": None
        },
        {
            "id": 2,
            "created_at": "2026-07-10T11:00:00",
            "total_amount": 1000.0,
            "items_count": 1,
            "payment_method": "cash",
            "payment_method_label": "Наличные",
            "comment": None
        }
    ]
}

MOCK_EMPTY_REPORT = {
    "period": "today",
    "date_from": "2026-07-10",
    "date_to": "2026-07-10",
    "total_amount": 0.0,
    "sales_count": 0,
    "items_count": 0,
    "payment_breakdown": [],
    "money_summary_rows": [],
    "money_summary_total": {
        "cash": 0.0,
        "card": 0.0,
        "transfer": 0.0,
        "sbp": 0.0,
        "legal_entity_account": 0.0,
        "other": 0.0,
        "unspecified": 0.0,
        "total": 0.0
    },
    "money_summary_granularity": "day",
    "money_summary": {
        "cash": 0.0,
        "card": 0.0,
        "transfer": 0.0,
        "sbp": 0.0,
        "legal_entity_account": 0.0,
        "other": 0.0,
        "unspecified": 0.0,
        "total": 0.0
    },
    "payment_labels": {
        "cash": "Наличные",
        "card": "Безнал / карта",
        "transfer": "Перевод",
        "sbp": "СБП",
        "legal_entity_account": "Счёт юрлица",
        "other": "Другое",
        "unspecified": "Не указано"
    },
    "sales": []
}


def _patch_report(mock_data):
    return patch("app.routers.reports.core_client.get_sales_report", AsyncMock(return_value=mock_data))


@pytest.mark.asyncio
async def test_reports_sales_ui_renders():
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales?period=today")
        assert response.status_code == 200
        html = response.text
        assert "Отчёт по продажам" in html
        assert "Сегодня" in html
        assert "Неделя" in html
        assert "Месяц" in html
        assert "Год" in html
        assert "Выручка" in html
        assert "Счёт юрлица" in html


def test_reports_sales_ui_period_links():
    """All quick-period links are present and point to correct URLs."""
    with _patch_report(MOCK_EMPTY_REPORT):
        response = client.get("/reports/sales")
        assert response.status_code == 200
        html = response.text
        assert "period=today" in html
        assert "period=week" in html
        assert "period=month" in html
        assert "period=year" in html


def test_reports_sales_default_200():
    """/reports/sales opens 200."""
    with _patch_report(MOCK_EMPTY_REPORT):
        response = client.get("/reports/sales")
        assert response.status_code == 200


def test_reports_sales_today_200():
    """/reports/sales?period=today opens 200."""
    with _patch_report(MOCK_EMPTY_REPORT):
        response = client.get("/reports/sales?period=today")
        assert response.status_code == 200


def test_reports_sales_week_200():
    """/reports/sales?period=week opens 200."""
    with _patch_report(MOCK_EMPTY_REPORT):
        response = client.get("/reports/sales?period=week")
        assert response.status_code == 200


def test_reports_sales_year_200():
    """/reports/sales?period=year opens 200."""
    with _patch_report(MOCK_EMPTY_REPORT):
        response = client.get("/reports/sales?period=year")
        assert response.status_code == 200


def test_reports_sales_empty_dates_200():
    """/reports/sales?date_from=&date_to= opens 200, no Internal Server Error."""
    with _patch_report(MOCK_EMPTY_REPORT):
        response = client.get("/reports/sales?date_from=&date_to=")
        assert response.status_code == 200
        assert "Internal Server Error" not in response.text


def test_reports_sales_custom_dates_200():
    """/reports/sales?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD opens 200."""
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales?date_from=2026-07-01&date_to=2026-07-10")
        assert response.status_code == 200


def test_reports_sales_contains_summary_title():
    """Page contains 'Сводка денег за период'."""
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales")
        assert response.status_code == 200
        assert "Сводка денег за период" in response.text


def test_reports_sales_contains_cash():
    """Page contains 'Наличные'."""
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales")
        assert "Наличные" in response.text


def test_reports_sales_contains_card():
    """Page contains 'Безнал / карта'."""
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales")
        assert "Безнал / карта" in response.text


def test_reports_sales_contains_transfer():
    """Page contains 'Перевод'."""
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales")
        assert "Перевод" in response.text


def test_reports_sales_contains_sbp():
    """Page contains 'СБП'."""
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales")
        assert "СБП" in response.text


def test_reports_sales_contains_legal_entity():
    """Page contains 'Счёт юрлица'."""
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales")
        assert "Счёт юрлица" in response.text


def test_reports_sales_contains_total():
    """Page contains 'Итого'."""
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales")
        assert "Итого" in response.text


def test_summary_table_before_sales_table():
    """Summary table is before detailed sales table in the HTML."""
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales")
        html = response.text
        summary_pos = html.find("Сводка денег за период")
        detail_pos = html.find("Детализация продаж")
        assert summary_pos != -1
        assert detail_pos != -1
        assert summary_pos < detail_pos


def test_core_error_does_not_crash_template():
    """Invalid Core response does not crash template; shows safe empty state."""
    mock_error = AsyncMock(return_value={"error": True, "status_code": 500, "detail": "Test error"})
    with patch("app.routers.reports.core_client.get_sales_report", mock_error):
        response = client.get("/reports/sales")
        assert response.status_code == 200
        html = response.text
        # Should still render the page, not crash
        assert "Отчёт по продажам" in html
        assert "Сводка денег за период" in html


# === Stage 04G-S new tests ===

def test_reports_today_renders_at_least_one_row():
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales?period=today")
        assert response.status_code == 200
        # Check for row label '10.07.2026'
        assert "10.07.2026" in response.text


def test_reports_week_renders_multiple_rows():
    mock_data = MOCK_REPORT_DATA.copy()
    mock_data["period"] = "week"
    mock_data["money_summary_rows"] = [{"label": f"day{i}", "cash": 0, "card": 0, "transfer": 0, "sbp": 0, "legal_entity_account": 0, "other": 0, "unspecified": 0, "total": 0} for i in range(7)]
    with _patch_report(mock_data):
        response = client.get("/reports/sales?period=week")
        assert response.status_code == 200
        for i in range(7):
            assert f"day{i}" in response.text


def test_reports_month_renders_multiple_rows():
    mock_data = MOCK_REPORT_DATA.copy()
    mock_data["period"] = "month"
    mock_data["money_summary_rows"] = [{"label": f"mday{i}", "cash": 0, "card": 0, "transfer": 0, "sbp": 0, "legal_entity_account": 0, "other": 0, "unspecified": 0, "total": 0} for i in range(28)]
    with _patch_report(mock_data):
        response = client.get("/reports/sales?period=month")
        assert response.status_code == 200
        for i in range(28):
            assert f"mday{i}" in response.text


def test_reports_year_renders_multiple_rows():
    mock_data = MOCK_REPORT_DATA.copy()
    mock_data["period"] = "year"
    mock_data["money_summary_rows"] = [{"label": f"month{i}", "cash": 0, "card": 0, "transfer": 0, "sbp": 0, "legal_entity_account": 0, "other": 0, "unspecified": 0, "total": 0} for i in range(12)]
    with _patch_report(mock_data):
        response = client.get("/reports/sales?period=year")
        assert response.status_code == 200
        for i in range(12):
            assert f"month{i}" in response.text


def test_reports_table_contains_columns():
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales")
        text = response.text
        assert "Дата / Период" in text
        assert "Наличные" in text
        assert "Безнал / карта" in text
        assert "Перевод" in text
        assert "СБП" in text
        assert "Счёт юрлица" in text
        assert "Итого" in text


def test_reports_table_contains_itogo_za_period():
    with _patch_report(MOCK_REPORT_DATA):
        response = client.get("/reports/sales")
        assert "Итого за период" in response.text
