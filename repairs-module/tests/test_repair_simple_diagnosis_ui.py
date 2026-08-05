import pytest
from httpx import Response

def test_repair_simple_diagnosis_absent_in_new_form(client, mock_core):
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [{"value": "received", "label": "Принят"}],
        "priorities": [{"value": "normal", "label": "Обычный"}],
        "device_types": ["Ноутбук"],
        "default_diagnostic_fee": 500
    }))

    res = client.get("/repairs/new")
    assert res.status_code == 200
    html = res.text
    assert 'name="diagnosis_text"' not in html
    assert 'name="planned_works_text"' not in html
    assert 'name="planned_parts_text"' not in html
    assert 'name="estimated_repair_amount"' not in html


def test_repair_simple_diagnosis_edit_form_and_detail_display(client, mock_core):
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [{"value": "received", "label": "Принят"}],
        "priorities": [{"value": "normal", "label": "Обычный"}],
        "device_types": ["Ноутбук"]
    }))

    # 1. GET edit form with saved diagnosis data
    mock_core.get("/api/repairs/801").mock(return_value=Response(200, json={
        "id": 801,
        "number": "R-20260805-0801",
        "status": "diagnostics",
        "customer_name": "Тест Сметы UI",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 500,
        "diagnosis_text": "Неисправен разъём питания",
        "planned_works_text": "1. Замена - 1500 ₽",
        "planned_parts_text": "1. Разъём - 800 ₽",
        "estimated_repair_amount": 2300
    }))

    res_edit = client.get("/repairs/801/edit")
    assert res_edit.status_code == 200
    html_edit = res_edit.text
    assert 'name="diagnosis_text"' in html_edit
    assert 'name="planned_works_text"' in html_edit
    assert 'name="planned_parts_text"' in html_edit
    assert 'name="estimated_repair_amount"' in html_edit
    assert "Неисправен разъём питания" in html_edit
    assert 'value="2300"' in html_edit

    # 2. GET detail card with saved diagnosis data
    res_detail = client.get("/repairs/801")
    assert res_detail.status_code == 200
    html_detail = res_detail.text
    assert "Диагностика и предварительная стоимость" in html_detail
    assert "Неисправен разъём питания" in html_detail
    assert "1. Замена - 1500 ₽" in html_detail
    assert "1. Разъём - 800 ₽" in html_detail
    assert "2300 ₽" in html_detail


def test_repair_simple_diagnosis_empty_fields_show_not_specified(client, mock_core):
    mock_core.get("/api/repairs/802").mock(return_value=Response(200, json={
        "id": 802,
        "number": "R-20260805-0802",
        "status": "received",
        "customer_name": "Тест Пустых Полей",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 500,
        "diagnosis_text": None,
        "planned_works_text": None,
        "planned_parts_text": None,
        "estimated_repair_amount": None
    }))

    res = client.get("/repairs/802")
    assert res.status_code == 200
    html = res.text
    assert "Диагностика и предварительная стоимость" in html
    assert "Не указано" in html
    assert "None" not in html
    assert "null" not in html


def test_repair_simple_diagnosis_zero_amount_display(client, mock_core):
    mock_core.get("/api/repairs/803").mock(return_value=Response(200, json={
        "id": 803,
        "number": "R-20260805-0803",
        "status": "diagnostics",
        "customer_name": "Тест Бесплатного Ремонта",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 500,
        "diagnosis_text": "Гарантийный случай",
        "estimated_repair_amount": 0
    }))

    res = client.get("/repairs/803")
    assert res.status_code == 200
    assert "0 ₽" in res.text


def test_repair_simple_diagnosis_html_escaping_and_form_error(client, mock_core):
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [{"value": "received", "label": "Принят"}],
        "priorities": [{"value": "normal", "label": "Обычный"}],
        "device_types": ["Ноутбук"]
    }))

    mock_core.get("/api/repairs/804").mock(return_value=Response(200, json={
        "id": 804,
        "number": "R-20260805-0804",
        "status": "received",
        "customer_name": "Тест Экранирования",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "<script>alert('xss')</script>"
    }))

    # Submit negative estimated_repair_amount -> error form preserves input
    res_neg = client.post("/repairs/804/edit", data={
        "customer_name": "Тест Экранирования",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnosis_text": "<script>alert('xss')</script>",
        "estimated_repair_amount": "-100"
    })
    assert res_neg.status_code == 200
    html = res_neg.text
    assert "Предполагаемая стоимость ремонта не может быть отрицательной" in html
    assert "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in html or "&lt;script&gt;alert('xss')&lt;/script&gt;" in html or "alert('xss')" not in html


def test_repair_simple_diagnosis_terminal_edit_blocked(client, mock_core):
    mock_core.get("/api/repairs/805").mock(return_value=Response(200, json={
        "id": 805,
        "number": "R-20260805-0805",
        "status": "issued",
        "customer_name": "Тест Закрыт UI",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест"
    }))

    res = client.get("/repairs/805/edit")
    assert res.status_code == 200
    assert "Запрещено редактировать" in res.text
