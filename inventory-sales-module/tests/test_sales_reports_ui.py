import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_reports_sales_ui_renders():
    mock_get_report = AsyncMock(return_value={
        "period": "today",
        "date_from": "2026-07-03",
        "date_to": "2026-07-03",
        "total_amount": 10000.0,
        "sales_count": 2,
        "items_count": 5,
        "payment_breakdown": [
            {
                "payment_method": "legal_entity_account",
                "label": "Счёт юрлица",
                "amount": 10000.0,
                "sales_count": 2
            }
        ],
        "sales": [
            {
                "id": 1,
                "created_at": "2026-07-03T10:00:00",
                "total_amount": 10000.0,
                "items_count": 5,
                "payment_method": "legal_entity_account",
                "payment_method_label": "Счёт юрлица",
                "customer_label": None
            }
        ]
    })

    with patch("app.routers.reports.core_client.get_sales_report", mock_get_report):
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
    mock_get_report = AsyncMock(return_value={
        "period": "today",
        "date_from": "2026-07-03",
        "date_to": "2026-07-03",
        "total_amount": 0.0,
        "sales_count": 0,
        "items_count": 0,
        "payment_breakdown": [],
        "sales": []
    })

    with patch("app.routers.reports.core_client.get_sales_report", mock_get_report):
        response = client.get("/reports/sales")
        assert response.status_code == 200
        html = response.text
        assert "period=today" in html
        assert "period=week" in html
        assert "period=month" in html
        assert "period=year" in html
