import pytest
from httpx import Response

def test_ui_diagnostics_to_ready_blocked_when_amount_none(client, mock_core):
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [
            {"value": "diagnostics", "label": "Диагностика"},
            {"value": "ready", "label": "Готов"}
        ],
        "priorities": [{"value": "normal", "label": "Обычный"}],
        "device_types": ["Ноутбук"]
    }))

    # Repair in diagnostics status with estimated_repair_amount = None
    mock_core.get("/api/repairs/901").mock(return_value=Response(200, json={
        "id": 901,
        "number": "R-20260805-0901",
        "status": "diagnostics",
        "customer_name": "Тест UI Пустая Сумма",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "estimated_repair_amount": None
    }))

    # 1. Option 'ready' is visible in status dropdown
    res_get = client.get("/repairs/901")
    assert res_get.status_code == 200
    assert 'value="ready"' in res_get.text

    # 2. Submit status transition to ready -> blocked with new error & link
    res_post = client.post("/repairs/901/status", data={
        "status": "ready",
        "comment": ""
    })
    assert res_post.status_code == 200
    html = res_post.text
    assert "Для выхода из статуса «Диагностика» укажите стоимость ремонта" in html
    assert "Можно указать 0 ₽" in html
    assert "требуется указать комментарий" not in html
    assert "Указать стоимость ремонта" in html
    assert 'href="/repairs/901/edit"' in html


def test_ui_diagnostics_to_ready_success_with_amount_0(client, mock_core):
    mock_core.get("/api/repairs/902").mock(return_value=Response(200, json={
        "id": 902,
        "number": "R-20260805-0902",
        "status": "diagnostics",
        "customer_name": "Тест UI Сумма 0",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "estimated_repair_amount": 0
    }))

    mock_core.post("/api/repairs/902/status").mock(return_value=Response(200, json={
        "id": 902,
        "number": "R-20260805-0902",
        "status": "ready",
        "status_label": "Готов"
    }))

    # Transition without comment
    res_post = client.post("/repairs/902/status", data={
        "status": "ready",
        "comment": ""
    }, follow_redirects=False)
    assert res_post.status_code == 303
    assert "/repairs/902?msg=" in res_post.headers["location"]


def test_ui_diagnostics_to_ready_success_with_amount_2800(client, mock_core):
    mock_core.get("/api/repairs/903").mock(return_value=Response(200, json={
        "id": 903,
        "number": "R-20260805-0903",
        "status": "diagnostics",
        "customer_name": "Тест UI Сумма 2800",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "estimated_repair_amount": 2800
    }))

    mock_core.post("/api/repairs/903/status").mock(return_value=Response(200, json={
        "id": 903,
        "number": "R-20260805-0903",
        "status": "ready",
        "status_label": "Готов"
    }))

    # Transition with optional comment
    res_post = client.post("/repairs/903/status", data={
        "status": "ready",
        "comment": "Всё сделано"
    }, follow_redirects=False)
    assert res_post.status_code == 303
    assert "/repairs/903?msg=" in res_post.headers["location"]
