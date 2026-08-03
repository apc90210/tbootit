import pytest
from httpx import Response

def test_repair_diagnostics_to_ready_ui_flow(client, mock_core):
    """
    Test UI rendering and comment validation for diagnostics -> ready transition in repairs-module.
    """
    mock_core.get("/api/repairs/200").mock(return_value=Response(200, json={
        "id": 200,
        "number": "R-DIAG-001",
        "status": "diagnostics",
        "status_label": "Диагностика",
        "customer_name": "Иван Диагностический",
        "customer_phone": "+7 900 555-44-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест диагностики"
    }))

    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [
            {"value": "waiting_customer", "label": "Ожидает клиента"},
            {"value": "waiting_parts", "label": "Ожидает запчасти"},
            {"value": "in_repair", "label": "В ремонте"},
            {"value": "ready", "label": "Готов"},
            {"value": "unrepairable", "label": "Ремонт невозможен"},
            {"value": "canceled", "label": "Отменён"}
        ],
        "priorities": [{"value": "normal", "label": "Обычный"}],
        "device_types": ["Ноутбук"]
    }))

    # 1. GET /repairs/200 renders 'Готов' option in allowed statuses for 'diagnostics'
    res_detail = client.get("/repairs/200")
    assert res_detail.status_code == 200
    html = res_detail.text
    assert '<option value="ready">Готов</option>' in html

    # 2. Attempting status change to 'ready' with empty comment is blocked with error message
    res_empty_comment = client.post("/repairs/200/status", data={
        "status": "ready",
        "comment": "   "
    })
    assert res_empty_comment.status_code == 200
    assert "требуется указать комментарий" in res_empty_comment.text

    # 3. Valid status change to 'ready' with comment succeeds and redirects
    mock_core.post("/api/repairs/200/status").mock(return_value=Response(200, json={
        "id": 200,
        "number": "R-DIAG-001",
        "status": "ready",
        "status_label": "Готов"
    }))

    res_valid_submit = client.post("/repairs/200/status", data={
        "status": "ready",
        "comment": "Неисправность устранена во время диагностики"
    }, follow_redirects=False)
    assert res_valid_submit.status_code == 303
    assert "msg=" in res_valid_submit.headers["location"]
