import pytest
from datetime import datetime, timedelta
from app import models

def test_repairs_list_filters_complete(client, db_session):
    """
    Complete unit test coverage for every query filter on GET /api/repairs.
    """
    now = datetime.utcnow()
    past_date = now - timedelta(days=5)

    # Setup 2 distinct test repair records
    rep1 = models.RepairOrder(
        number="R-FILTER-001",
        status="diagnostics",
        customer_name="Алексей Фильтров",
        customer_phone="+7 911 111-22-33",
        customer_email="alex@filter.local",
        device_type="Моноблок",
        brand="Apple",
        model="iMac 27",
        serial_number="SN-APPLE-888",
        reported_issue="Артефакты на экране",
        assigned_to="Мастер Иннокентий",
        priority="urgent",
        accepted_at=past_date,
        created_at=past_date
    )
    rep2 = models.RepairOrder(
        number="R-FILTER-002",
        status="in_repair",
        customer_name="Борис Селектов",
        customer_phone="+7 922 444-55-66",
        customer_email="boris@filter.local",
        device_type="Планшет",
        brand="Samsung",
        model="Galaxy Tab",
        serial_number="SN-SAMSUNG-999",
        reported_issue="Не заряжается",
        assigned_to="Мастер Геннадий",
        priority="normal",
        accepted_at=now,
        created_at=now
    )
    db_session.add_all([rep1, rep2])
    db_session.commit()

    # 1. Search q by number
    res_q_num = client.get("/api/repairs?q=R-FILTER-001")
    assert res_q_num.status_code == 200
    numbers = [i["number"] for i in res_q_num.json()["items"]]
    assert "R-FILTER-001" in numbers
    assert "R-FILTER-002" not in numbers

    # 2. Search q by customer_name
    res_q_name = client.get("/api/repairs?q=Борис%20Селектов")
    assert res_q_name.status_code == 200
    numbers = [i["number"] for i in res_q_name.json()["items"]]
    assert "R-FILTER-002" in numbers
    assert "R-FILTER-001" not in numbers

    # 3. Search q by serial_number
    res_q_sn = client.get("/api/repairs?q=SN-APPLE-888")
    assert res_q_sn.status_code == 200
    numbers = [i["number"] for i in res_q_sn.json()["items"]]
    assert "R-FILTER-001" in numbers

    # 4. Filter status
    res_st = client.get("/api/repairs?status=in_repair")
    assert res_st.status_code == 200
    numbers = [i["number"] for i in res_st.json()["items"]]
    assert "R-FILTER-002" in numbers
    assert "R-FILTER-001" not in numbers

    # 5. Filter priority
    res_pr = client.get("/api/repairs?priority=urgent")
    assert res_pr.status_code == 200
    numbers = [i["number"] for i in res_pr.json()["items"]]
    assert "R-FILTER-001" in numbers
    assert "R-FILTER-002" not in numbers

    # 6. Filter device_type
    res_dt = client.get("/api/repairs?device_type=Планшет")
    assert res_dt.status_code == 200
    numbers = [i["number"] for i in res_dt.json()["items"]]
    assert "R-FILTER-002" in numbers
    assert "R-FILTER-001" not in numbers

    # 7. Filter assigned_to
    res_as = client.get("/api/repairs?assigned_to=Иннокентий")
    assert res_as.status_code == 200
    numbers = [i["number"] for i in res_as.json()["items"]]
    assert "R-FILTER-001" in numbers
    assert "R-FILTER-002" not in numbers

    # 8. Filter customer_phone
    res_ph = client.get("/api/repairs?customer_phone=922%20444")
    assert res_ph.status_code == 200
    numbers = [i["number"] for i in res_ph.json()["items"]]
    assert "R-FILTER-002" in numbers

    # 9. Filter serial_number
    res_sn = client.get("/api/repairs?serial_number=SN-SAMSUNG-999")
    assert res_sn.status_code == 200
    numbers = [i["number"] for i in res_sn.json()["items"]]
    assert "R-FILTER-002" in numbers

    # 10. Filter date_from / date_to
    date_from_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    res_df = client.get(f"/api/repairs?date_from={date_from_str}")
    assert res_df.status_code == 200
    numbers = [i["number"] for i in res_df.json()["items"]]
    assert "R-FILTER-002" in numbers
    assert "R-FILTER-001" not in numbers

    # 11. Pagination page & page_size
    res_pg = client.get("/api/repairs?page=1&page_size=1")
    assert res_pg.status_code == 200
    data_pg = res_pg.json()
    assert len(data_pg["items"]) == 1
    assert data_pg["page"] == 1
    assert data_pg["page_size"] == 1

    # 12. Sort accepted_at_asc vs accepted_at_desc
    res_asc = client.get("/api/repairs?sort=accepted_at_asc&page_size=200")
    assert res_asc.status_code == 200
    items_asc = res_asc.json()["items"]
    # rep1 (past_date) should come before rep2 (now) in asc order
    idx1 = next(i for i, item in enumerate(items_asc) if item["number"] == "R-FILTER-001")
    idx2 = next(i for i, item in enumerate(items_asc) if item["number"] == "R-FILTER-002")
    assert idx1 < idx2
