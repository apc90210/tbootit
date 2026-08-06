import pytest
from datetime import datetime, timedelta
from app import models, schemas

def test_repairs_status_filter_complete(client, db_session):
    """
    Comprehensive tests for repair status filtering in Core API (GET /api/repairs).
    Covering:
    - Every existing status contract value (received, diagnostics, waiting_customer, waiting_parts, in_repair, ready, unrepairable, issued, canceled)
    - Exact match (no partial/substring status matching)
    - Combination with q, priority, device_type, assigned_to, date range, pagination, sort
    - Empty result handling
    - Unknown status handling without HTTP 500
    """
    now = datetime.utcnow()
    past_date = now - timedelta(days=5)

    # 1. Create a repair order for each status
    created_repairs = {}
    for idx, (status_code, status_label) in enumerate(schemas.REPAIR_STATUSES.items(), start=1):
        repair = models.RepairOrder(
            number=f"R-ST-{idx:03d}",
            status=status_code,
            customer_name=f"Клиент {status_code}",
            customer_phone=f"+7 900 000-00-{idx:02d}",
            device_type="Ноутбук" if idx % 2 == 1 else "Телефон",
            brand="ASUS" if idx % 2 == 1 else "Samsung",
            model=f"Model-{idx}",
            serial_number=f"SN-{status_code.upper()}",
            reported_issue=f"Проблема {status_label}",
            assigned_to="Мастер Иван" if idx % 2 == 1 else "Мастер Петр",
            priority="urgent" if idx % 2 == 1 else "normal",
            accepted_at=past_date if idx % 2 == 1 else now,
            created_at=past_date if idx % 2 == 1 else now
        )
        db_session.add(repair)
        created_repairs[status_code] = repair

    db_session.commit()

    # 2. Test filtering by EVERY existing status
    for status_code in schemas.REPAIR_STATUSES.keys():
        res = client.get(f"/api/repairs?status={status_code}")
        assert res.status_code == 200, f"Failed for status {status_code}"
        body = res.json()
        assert body["total"] >= 1
        items = body["items"]
        assert all(item["status"] == status_code for item in items)
        numbers = [item["number"] for item in items]
        assert created_repairs[status_code].number in numbers

    # 3. Exact matching test (substring of status like "diag" or "in" must not match unless exact)
    res_partial = client.get("/api/repairs?status=diag")
    assert res_partial.status_code == 200
    assert res_partial.json()["total"] == 0

    # 4. Combination: status + q
    res_st_q = client.get("/api/repairs?status=diagnostics&q=ASUS")
    assert res_st_q.status_code == 200
    for item in res_st_q.json()["items"]:
        assert item["status"] == "diagnostics"
        assert "ASUS" in (item["brand"] or "") or "ASUS" in (item["model"] or "") or "ASUS" in (item["reported_issue"] or "")

    # 5. Combination: status + priority
    res_st_pr = client.get("/api/repairs?status=diagnostics&priority=urgent")
    assert res_st_pr.status_code == 200
    for item in res_st_pr.json()["items"]:
        assert item["status"] == "diagnostics"
        assert item["priority"] == "urgent"

    # 6. Combination: status + device_type
    res_st_dt = client.get("/api/repairs?status=diagnostics&device_type=Ноутбук")
    assert res_st_dt.status_code == 200
    for item in res_st_dt.json()["items"]:
        assert item["status"] == "diagnostics"
        assert item["device_type"] == "Ноутбук"

    # 7. Combination: status + assigned_to
    res_st_as = client.get("/api/repairs?status=diagnostics&assigned_to=Иван")
    assert res_st_as.status_code == 200
    for item in res_st_as.json()["items"]:
        assert item["status"] == "diagnostics"
        assert "Иван" in item["assigned_to"]

    # 8. Combination: status + date range
    date_str = past_date.isoformat()[:10]
    res_st_date = client.get(f"/api/repairs?status=diagnostics&date_from={date_str}&date_to={date_str}")
    assert res_st_date.status_code == 200
    for item in res_st_date.json()["items"]:
        assert item["status"] == "diagnostics"

    # 9. Combination: status + pagination
    res_page = client.get("/api/repairs?status=diagnostics&page=1&page_size=10")
    assert res_page.status_code == 200
    assert res_page.json()["page"] == 1
    assert res_page.json()["page_size"] == 10

    # 10. Combination: status + sort
    res_sort = client.get("/api/repairs?status=diagnostics&sort=accepted_at_asc")
    assert res_sort.status_code == 200
    assert "items" in res_sort.json()

    # 11. Empty result (non-existent matching criteria)
    res_empty = client.get("/api/repairs?status=diagnostics&q=NONEXISTENT_QUERY_999")
    assert res_empty.status_code == 200
    assert res_empty.json()["total"] == 0
    assert len(res_empty.json()["items"]) == 0

    # 12. Unknown status without HTTP 500
    res_unknown = client.get("/api/repairs?status=unknown_invalid_status_xyz")
    assert res_unknown.status_code == 200
    assert res_unknown.json()["total"] == 0
    assert res_unknown.json()["items"] == []
