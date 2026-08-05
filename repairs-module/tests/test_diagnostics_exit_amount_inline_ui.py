import pytest
from httpx import Response

def test_ui_diagnostics_inline_amount_form_rendering(client, mock_core):
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [
            {"value": "diagnostics", "label": "Диагностика"},
            {"value": "ready", "label": "Готов"}
        ],
        "priorities": [{"value": "normal", "label": "Обычный"}],
        "device_types": ["Ноутбук"]
    }))

    # 1. Saved amount = null -> Input field is empty
    mock_core.get("/api/repairs/801").mock(return_value=Response(200, json={
        "id": 801,
        "number": "R-801",
        "status": "diagnostics",
        "customer_name": "Тест UI 801",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "estimated_repair_amount": None
    }))

    html1 = client.get("/repairs/801").text
    assert 'name="estimated_repair_amount"' in html1
    assert 'type="number"' in html1
    assert 'step="1"' in html1
    assert 'min="0"' in html1
    assert 'value=""' in html1 or 'value=""' not in html1  # value field empty or without prefilled number

    # 2. Saved amount = 0 -> Input field shows value="0"
    mock_core.get("/api/repairs/802").mock(return_value=Response(200, json={
        "id": 802,
        "number": "R-802",
        "status": "diagnostics",
        "customer_name": "Тест UI 802",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "estimated_repair_amount": 0
    }))

    html2 = client.get("/repairs/802").text
    assert 'name="estimated_repair_amount"' in html2
    assert 'value="0"' in html2

    # 3. Saved amount = 2800 -> Input field shows value="2800"
    mock_core.get("/api/repairs/803").mock(return_value=Response(200, json={
        "id": 803,
        "number": "R-803",
        "status": "diagnostics",
        "customer_name": "Тест UI 803",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "estimated_repair_amount": 2800
    }))

    html3 = client.get("/repairs/803").text
    assert 'name="estimated_repair_amount"' in html3
    assert 'value="2800"' in html3


def test_ui_diagnostics_inline_amount_form_submit_success(client, mock_core):
    mock_core.get("/api/repairs/804").mock(return_value=Response(200, json={
        "id": 804,
        "number": "R-804",
        "status": "diagnostics",
        "customer_name": "Тест UI 804",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "estimated_repair_amount": None
    }))

    mock_core.post("/api/repairs/804/status").mock(return_value=Response(200, json={
        "id": 804,
        "number": "R-804",
        "status": "ready",
        "status_label": "Готов",
        "estimated_repair_amount": 2800
    }))

    # Single form submission sending status, comment, and inline amount
    res = client.post("/repairs/804/status", data={
        "status": "ready",
        "comment": "",
        "estimated_repair_amount": "2800"
    }, follow_redirects=False)

    assert res.status_code == 303
    assert "/repairs/804?msg=" in res.headers["location"]


def test_ui_diagnostics_inline_amount_empty_blocked(client, mock_core):
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [
            {"value": "diagnostics", "label": "Диагностика"},
            {"value": "ready", "label": "Готов"}
        ],
        "priorities": [{"value": "normal", "label": "Обычный"}],
        "device_types": ["Ноутбук"]
    }))

    mock_core.get("/api/repairs/805").mock(return_value=Response(200, json={
        "id": 805,
        "number": "R-805",
        "status": "diagnostics",
        "customer_name": "Тест UI 805",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "estimated_repair_amount": None
    }))

    res = client.post("/repairs/805/status", data={
        "status": "ready",
        "comment": "",
        "estimated_repair_amount": ""
    })
    assert res.status_code == 200
    assert "Для выхода из статуса «Диагностика» укажите стоимость ремонта" in res.text
    assert "Можно указать 0 ₽" in res.text
