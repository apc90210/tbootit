"""
Stage02B — Canonical Core Sales Reports (Month Period) Tests.
Verifies:
1. Section 1 & 2: Core canonical period=month implementation:
   - start = first calendar day of current month
   - end = current date/time boundary
   - only sales inside current calendar month
   - not "last 30 days"
2. Section 6: Deterministic Month Boundary Tests:
   - Current date fixture: 2026-09-28:
     * 2026-09-01 -> INCLUDED
     * 2026-09-15 -> INCLUDED
     * 2026-09-28 -> INCLUDED
     * 2026-08-31 -> EXCLUDED (even though within last 30 days)
   - Year boundary fixture: 2026-01-05:
     * 2026-01-01 -> INCLUDED
     * 2025-12-31 -> EXCLUDED
3. Section 7: Consistency Tests:
   - sales_count == len(sales)
   - total_amount == sum(sales amounts)
   - payment breakdown matches sales list
   - canceled sales strictly excluded
"""

from datetime import datetime, date
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app import models

client = TestClient(app)


def _create_sale(db, amount: float, status: str, payment_method: str, created_at: datetime):
    sale = models.Sale(
        total_amount=amount,
        status=status,
        payment_method=payment_method,
        created_at=created_at,
        comment="test_month_sale"
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def test_core_month_boundary_fixture_sep_2026():
    """
    Section 6 fixture:
    Current date: 2026-09-28
    Sales:
    - 2026-09-01 -> INCLUDED
    - 2026-09-15 -> INCLUDED
    - 2026-09-28 -> INCLUDED
    - 2026-08-31 -> EXCLUDED
    """
    db = next(get_db())
    created_sales = []
    try:
        s_sep01 = _create_sale(db, 1000.0, "completed", "cash", datetime(2026, 9, 1, 9, 0, 0))
        s_sep15 = _create_sale(db, 2000.0, "completed", "card", datetime(2026, 9, 15, 14, 30, 0))
        s_sep28 = _create_sale(db, 3000.0, "completed", "transfer", datetime(2026, 9, 28, 18, 0, 0))
        s_aug31 = _create_sale(db, 4000.0, "completed", "cash", datetime(2026, 8, 31, 23, 59, 59))
        created_sales.extend([s_sep01, s_sep15, s_sep28, s_aug31])

        # Mock current datetime to 2026-09-28 20:00:00
        mock_now = datetime(2026, 9, 28, 20, 0, 0)
        with patch("app.routers.reports._current_datetime", return_value=mock_now):
            resp = client.get("/api/reports/sales?period=month")
            assert resp.status_code == 200, resp.text
            data = resp.json()

            assert data["period"] == "month"
            assert data["date_from"] == "2026-09-01"
            assert data["date_to"] == "2026-09-28"

            sale_ids = [s["id"] for s in data["sales"]]
            assert s_sep01.id in sale_ids, "2026-09-01 sale must be INCLUDED"
            assert s_sep15.id in sale_ids, "2026-09-15 sale must be INCLUDED"
            assert s_sep28.id in sale_ids, "2026-09-28 sale must be INCLUDED"
            assert s_aug31.id not in sale_ids, "2026-08-31 sale must be EXCLUDED"

    finally:
        for s in created_sales:
            db.delete(s)
        db.commit()


def test_core_month_boundary_fixture_jan_year_boundary():
    """
    Section 6 year boundary fixture:
    Current date: 2026-01-05
    - 2026-01-01 -> INCLUDED
    - 2025-12-31 -> EXCLUDED
    """
    db = next(get_db())
    created_sales = []
    try:
        s_jan01 = _create_sale(db, 1500.0, "completed", "cash", datetime(2026, 1, 1, 10, 0, 0))
        s_dec31 = _create_sale(db, 5000.0, "completed", "card", datetime(2025, 12, 31, 23, 50, 0))
        created_sales.extend([s_jan01, s_dec31])

        # Mock current datetime to 2026-01-05 12:00:00
        mock_now = datetime(2026, 1, 5, 12, 0, 0)
        with patch("app.routers.reports._current_datetime", return_value=mock_now):
            resp = client.get("/api/reports/sales?period=month")
            assert resp.status_code == 200, resp.text
            data = resp.json()

            assert data["period"] == "month"
            assert data["date_from"] == "2026-01-01"
            assert data["date_to"] == "2026-01-05"

            sale_ids = [s["id"] for s in data["sales"]]
            assert s_jan01.id in sale_ids, "2026-01-01 sale must be INCLUDED"
            assert s_dec31.id not in sale_ids, "2025-12-31 sale must be EXCLUDED"

    finally:
        for s in created_sales:
            db.delete(s)
        db.commit()


def test_core_month_consistency_and_canceled_exclusion():
    """
    Section 7:
    - sales_count == len(sales[])
    - total_amount == sum(sales amounts)
    - payment-method totals equal sales set
    - canceled sales excluded from list and totals
    """
    db = next(get_db())
    created_sales = []
    try:
        s_cash = _create_sale(db, 1100.0, "completed", "cash", datetime(2026, 9, 10, 10, 0, 0))
        s_card = _create_sale(db, 2200.0, "completed", "card", datetime(2026, 9, 12, 11, 0, 0))
        s_canc = _create_sale(db, 9999.0, "canceled", "cash", datetime(2026, 9, 14, 12, 0, 0))
        created_sales.extend([s_cash, s_card, s_canc])

        mock_now = datetime(2026, 9, 28, 20, 0, 0)
        with patch("app.routers.reports._current_datetime", return_value=mock_now):
            resp = client.get("/api/reports/sales?period=month")
            assert resp.status_code == 200, resp.text
            data = resp.json()

            # Canceled sale must not appear
            sale_ids = [s["id"] for s in data["sales"]]
            assert s_canc.id not in sale_ids, "Canceled sale must not be in report sales"

            # sales_count == len(sales)
            assert data["sales_count"] == len(data["sales"])

            # total_amount == sum of amounts
            sum_amounts = sum(s["total_amount"] for s in data["sales"])
            assert abs(data["total_amount"] - sum_amounts) < 0.001

            # payment breakdown sum equals total_amount
            pb_sum = sum(pb["amount"] for pb in data["payment_breakdown"])
            assert abs(pb_sum - data["total_amount"]) < 0.001

    finally:
        for s in created_sales:
            db.delete(s)
        db.commit()


def test_core_month_not_last_30_days():
    """
    Explicitly prove that period=month does NOT mean "last 30 days".
    On 2026-09-10, 25 days ago was 2026-08-16.
    A sale on 2026-08-16 is within the last 30 days, but is in August, so it MUST be excluded.
    """
    db = next(get_db())
    created_sales = []
    try:
        s_aug16 = _create_sale(db, 777.0, "completed", "cash", datetime(2026, 8, 16, 12, 0, 0))
        s_sep05 = _create_sale(db, 888.0, "completed", "cash", datetime(2026, 9, 5, 12, 0, 0))
        created_sales.extend([s_aug16, s_sep05])

        mock_now = datetime(2026, 9, 10, 12, 0, 0)
        with patch("app.routers.reports._current_datetime", return_value=mock_now):
            resp = client.get("/api/reports/sales?period=month")
            assert resp.status_code == 200
            data = resp.json()

            assert data["date_from"] == "2026-09-01"
            assert data["date_to"] == "2026-09-10"

            sale_ids = [s["id"] for s in data["sales"]]
            assert s_sep05.id in sale_ids
            assert s_aug16.id not in sale_ids, "August sale within 30 days must NOT be included in calendar month report"

    finally:
        for s in created_sales:
            db.delete(s)
        db.commit()
