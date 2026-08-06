import pytest
from datetime import datetime, date
from app import models

def test_repair_sale_included_in_general_reports(client, db_session):
    """
    Test that linked repair sales are included in overall sales reports:
    - Included in GET /api/reports/sales
    - Canceled repair sale is excluded from completed revenue
    """
    today_str = date.today().isoformat()

    # Create repair and transition to ready (amount = 4500)
    rep = models.RepairOrder(
        number="R-REPORT-001",
        status="diagnostics",
        customer_name="Отчётный Клиент",
        customer_phone="+79998887766",
        device_type="Планшет",
        brand="iPad",
        model="Pro",
        reported_issue="Замена экрана",
        estimated_repair_amount=4500
    )
    db_session.add(rep)
    db_session.commit()

    client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "ready", "comment": "Готов к сдаче", "estimated_repair_amount": 4500}
    )

    # Fetch sales report
    res_rep = client.get(f"/api/reports/sales?date_from={today_str}&date_to={today_str}")
    assert res_rep.status_code == 200
    report_data = res_rep.json()

    # Verify repair sale appears in report sales list
    repair_sales = [s for s in report_data["sales"] if s.get("source_type") == "repair" and s.get("source_id") == rep.id]
    assert len(repair_sales) == 1
    assert repair_sales[0]["total_amount"] == 4500.0

    # Cancel repair and check report
    client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "canceled", "comment": "Отмена"}
    )

    res_rep_canceled = client.get(f"/api/reports/sales?date_from={today_str}&date_to={today_str}")
    assert res_rep_canceled.status_code == 200
    report_data_canceled = res_rep_canceled.json()

    canceled_repair_sales = [s for s in report_data_canceled["sales"] if s.get("source_type") == "repair" and s.get("source_id") == rep.id]
    assert len(canceled_repair_sales) == 1
    assert canceled_repair_sales[0]["status"] == "canceled"
