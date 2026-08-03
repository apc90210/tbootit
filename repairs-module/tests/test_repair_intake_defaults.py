import pytest
from httpx import Response

def test_repair_intake_defaults_initial_and_edit_behavior(client, mock_core):
    """
    Test intake defaults behavior on GET /repairs/new, edit form, and form submit errors.
    """
    # Mock Core API options response
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [{"value": "received", "label": "Принят"}],
        "priorities": [{"value": "normal", "label": "Обычный"}],
        "device_types": ["Ноутбук", "Телефон"]
    }))

    # 1. GET /repairs/new returns 200 OK and pre-populated values
    res_new = client.get("/repairs/new")
    assert res_new.status_code == 200
    html = res_new.text
    assert 'value="Ноутбук, зарядка, чехол..."' in html
    assert 'value="Потёртости, царпины..."' in html

    # 2. Form submit error preserves modified or cleared fields without restoring defaults
    mock_core.post("/api/repairs/").mock(return_value=Response(400, json={
        "error": True,
        "detail": "Ошибка валидации клиента"
    }))

    res_post_err = client.post("/repairs/new", data={
        "customer_name": "Тест Ошибки",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Не включается",
        "completeness": "Только мышка",
        "appearance": ""
    })
    assert res_post_err.status_code == 200
    html_err = res_post_err.text
    assert "Ошибка создания заказа" in html_err
    assert 'value="Только мышка"' in html_err
    assert 'value=""' in html_err
    assert 'value="Ноутбук, зарядка, чехол..."' not in html_err

    # 3. GET /repairs/{id}/edit shows exact saved values without overlaying defaults
    mock_core.get("/api/repairs/100").mock(return_value=Response(200, json={
        "id": 100,
        "number": "R-EDIT-001",
        "status": "received",
        "customer_name": "Тест Спасённого",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест редактирования",
        "completeness": "Особый чехол",
        "appearance": None
    }))

    res_edit = client.get("/repairs/100/edit")
    assert res_edit.status_code == 200
    html_edit = res_edit.text
    assert 'value="Особый чехол"' in html_edit
    assert 'value=""' in html_edit or 'value="None"' not in html_edit
    assert 'value="Ноутбук, зарядка, чехол..."' not in html_edit
