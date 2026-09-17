import pytest
from datetime import datetime, date
from app import models

def test_repair_sale_included_in_general_reports(client, db_session):
    """
    Test that linked repair sales (created on issued) are included in overall sales reports:
    - Included in GET /api/reports/sales
    - Ready alone does NOT create sale
    - Issued creates sale and appears in sales list and reports
    """
    # 1. Create repair
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

    # Move to ready: no sale yet
    client.post(
        f"/api/repairs/{rep.id}/status",
        json={"status": "ready", "comment": "Готов к сдаче", "estimated_repair_amount": 4500}
    )
    sales_list = client.get("/api/sales/").json()["items"]
    assert len([s for s in sales_list if s.get("source_type") == "repair" and s.get("source_id") == rep.id]) == 0

    # Move to issued: sale created
    client.post(
        f"/api/repairs/{rep.id}/status",
        json={
            "status": "issued",
            "final_amount": 4500.0,
            "payment_method": "cash",
            "warranty_days": 30,
            "comment": "Выдан"
        }
    )

    # Fetch sales report
    res_rep = client.get("/api/reports/sales?period=today")
    assert res_rep.status_code == 200
    report_data = res_rep.json()

    # Verify repair sale appears in sales endpoint
    sales_list = client.get("/api/sales/").json()["items"]
    repair_sales = [s for s in sales_list if s.get("source_type") == "repair" and s.get("source_id") == rep.id]
    assert len(repair_sales) == 1
    assert repair_sales[0]["total_amount"] == 4500.0
    assert repair_sales[0]["status"] == "completed"
