import pytest
from httpx import Response

def test_repair_diagnostic_fee_new_form_and_submit(client, mock_core):
    """
    Test UI rendering, defaults from options, custom submits, zero submits, step=1, and negative validation in new form.
    """
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [{"value": "received", "label": "Принят"}],
        "priorities": [{"value": "normal", "label": "Обычный"}],
        "device_types": ["Ноутбук"],
        "default_diagnostic_fee": 500
    }))

    # 1. GET /repairs/new renders diagnostic_fee field with default 500 as value and step=1
    res_new = client.get("/repairs/new")
    assert res_new.status_code == 200
    html_new = res_new.text
    assert 'name="diagnostic_fee"' in html_new
    assert 'value="500"' in html_new
    assert 'step="1"' in html_new

    # 2. Submit custom 750
    mock_core.post("/api/repairs/").mock(return_value=Response(201, json={
        "id": 601,
        "number": "R-20260803-0601",
        "customer_name": "Тест 750 UI",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 750
    }))

    res_post_750 = client.post("/repairs/new", data={
        "customer_name": "Тест 750 UI",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": "750"
    }, follow_redirects=False)
    assert res_post_750.status_code == 303
    assert "/repairs/601" in res_post_750.headers["location"]

    # 3. Submit zero 0
    mock_core.post("/api/repairs/").mock(return_value=Response(201, json={
        "id": 602,
        "number": "R-20260803-0602",
        "customer_name": "Тест 0 UI",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 0
    }))

    res_post_0 = client.post("/repairs/new", data={
        "customer_name": "Тест 0 UI",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": "0"
    }, follow_redirects=False)
    assert res_post_0.status_code == 303
    assert "/repairs/602" in res_post_0.headers["location"]

    # 4. Negative value displays Russian error message
    res_post_neg = client.post("/repairs/new", data={
        "customer_name": "Тест Отрицательный",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": "-100"
    })
    assert res_post_neg.status_code == 200
    assert "Стоимость диагностики не может быть отрицательной" in res_post_neg.text
    assert 'value="-100"' in res_post_neg.text


def test_repair_diagnostic_fee_edit_and_detail(client, mock_core):
    """
    Test edit form rendering, preservation of zero, detail page display, and terminal block.
    """
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [{"value": "received", "label": "Принят"}],
        "priorities": [{"value": "normal", "label": "Обычный"}],
        "device_types": ["Ноутбук"]
    }))

    # Repair with diagnostic_fee = 800
    mock_core.get("/api/repairs/700").mock(return_value=Response(200, json={
        "id": 700,
        "number": "R-20260803-0700",
        "status": "received",
        "customer_name": "Тест Редактирования",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 800
    }))

    # 1. Edit form shows saved 800
    res_edit = client.get("/repairs/700/edit")
    assert res_edit.status_code == 200
    assert 'value="800"' in res_edit.text

    # 2. Detail page shows saved 800
    res_detail = client.get("/repairs/700")
    assert res_detail.status_code == 200
    assert "Стоимость диагностики:" in res_detail.text
    assert "800 ₽" in res_detail.text

    # Repair with diagnostic_fee = 0
    mock_core.get("/api/repairs/701").mock(return_value=Response(200, json={
        "id": 701,
        "number": "R-20260803-0701",
        "status": "received",
        "customer_name": "Тест Нулевой",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 0
    }))

    res_edit_0 = client.get("/repairs/701/edit")
    assert res_edit_0.status_code == 200
    assert 'value="0"' in res_edit_0.text

    # Terminal closed repair edit blocked
    mock_core.get("/api/repairs/702").mock(return_value=Response(200, json={
        "id": 702,
        "number": "R-20260803-0702",
        "status": "issued",
        "customer_name": "Тест Выдан",
        "customer_phone": "+7 900 111-22-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест",
        "diagnostic_fee": 500
    }))

    res_edit_term = client.get("/repairs/702/edit")
    assert res_edit_term.status_code == 200
    assert "Запрещено редактировать" in res_edit_term.text
