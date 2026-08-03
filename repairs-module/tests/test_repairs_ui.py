import pytest
from httpx import Response
import urllib.parse

def test_health_check(client, mock_core):
    mock_core.get("/health").mock(return_value=Response(200, json={"status": "ok"}))

    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["module"] == "repairs-module"
    assert data["core_available"] is True

def test_repairs_list_rendering(client, mock_core):
    mock_core.get("/api/repairs/").mock(return_value=Response(200, json={
        "items": [
            {
                "id": 1,
                "number": "R-20260803-0001",
                "customer_name": "Иванов И.И.",
                "customer_phone": "+7 900 111-22-33",
                "device_type": "Ноутбук",
                "brand": "Lenovo",
                "model": "T480",
                "reported_issue": "Не включается",
                "status": "received",
                "status_label": "Принят",
                "priority": "normal",
                "priority_label": "Обычный",
                "assigned_to": "Мастер 1",
                "accepted_at": "2026-08-03T10:00:00"
            }
        ],
        "total": 1, "page": 1, "page_size": 50, "total_pages": 1
    }))
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [{"value": "received", "label": "Принят"}],
        "priorities": [{"value": "normal", "label": "Обычный"}],
        "device_types": ["Ноутбук"]
    }))

    res = client.get("/repairs")
    assert res.status_code == 200
    html = res.text
    assert "R-20260803-0001" in html
    assert "Иванов И.И." in html
    assert "Ноутбук" in html
    assert "Принят" in html

def test_new_repair_form_submit(client, mock_core):
    mock_core.post("/api/repairs/").mock(return_value=Response(201, json={
        "id": 99,
        "number": "R-20260803-0099",
        "customer_name": "Петров П.П.",
        "customer_phone": "+7 999 888-77-66",
        "device_type": "Телефон",
        "reported_issue": "Разбит экран",
        "status": "received"
    }))

    res = client.post("/repairs/new", data={
        "customer_name": "Петров П.П.",
        "customer_phone": "+7 999 888-77-66",
        "device_type": "Телефон",
        "reported_issue": "Разбит экран"
    }, follow_redirects=False)

    assert res.status_code == 303
    loc = urllib.parse.unquote(res.headers["location"])
    assert loc == "/repairs/99?msg=Ремонт+R-20260803-0099+успешно+принят"

def test_repair_detail_rendering(client, mock_core):
    mock_core.get("/api/repairs/50").mock(return_value=Response(200, json={
        "id": 50,
        "number": "R-20260803-0050",
        "customer_name": "Сидоров С.С.",
        "customer_phone": "+7 900 555-44-33",
        "device_type": "Монитор",
        "brand": "Dell",
        "model": "U2412M",
        "reported_issue": "Гаснет экран",
        "status": "diagnostics",
        "status_label": "Диагностика",
        "priority": "urgent",
        "priority_label": "Срочный",
        "access_code_provided": True,
        "history": [
            {"id": 1, "repair_id": 50, "old_status": "received", "new_status": "diagnostics", "comment": "Начата диагностика", "changed_at": "2026-08-03T10:30:00"}
        ]
    }))
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [
            {"value": "diagnostics", "label": "Диагностика"},
            {"value": "in_repair", "label": "В ремонте"}
        ],
        "priorities": [],
        "device_types": []
    }))

    res = client.get("/repairs/50")
    assert res.status_code == 200
    html = res.text
    assert "R-20260803-0050" in html
    assert "Сидоров С.С." in html
    assert "Гаснет экран" in html
    assert "Начата диагностика" in html

def test_status_transition_submit(client, mock_core):
    mock_core.post("/api/repairs/50/status").mock(return_value=Response(200, json={
        "id": 50,
        "number": "R-20260803-0050",
        "status": "in_repair",
        "status_label": "В ремонте"
    }))

    res = client.post("/repairs/50/status", data={
        "status": "in_repair",
        "comment": "Запчасть получена"
    }, follow_redirects=False)

    assert res.status_code == 303
    loc = urllib.parse.unquote(res.headers["location"])
    assert loc == "/repairs/50?msg=Статус+успешно+изменён+на+«В ремонте»"

def test_core_unavailable_shows_friendly_error(client, mock_core):
    mock_core.get("/api/repairs/").mock(return_value=Response(500, json={"detail": "Internal Server Error"}))
    mock_core.get("/api/repairs/options").mock(return_value=Response(500, json={"detail": "Error"}))

    res = client.get("/repairs")
    assert res.status_code == 200
    assert "Ошибка связи с Core API" in res.text

def test_all_nine_status_filters_rendered_in_ui(client, mock_core):
    mock_core.get("/api/repairs/").mock(return_value=Response(200, json={"items": [], "total": 0, "page": 1, "page_size": 50}))
    mock_core.get("/api/repairs/options").mock(return_value=Response(200, json={
        "statuses": [
            {"value": "received", "label": "Принят"},
            {"value": "diagnostics", "label": "Диагностика"},
            {"value": "waiting_customer", "label": "Ожидает клиента"},
            {"value": "waiting_parts", "label": "Ожидает запчасти"},
            {"value": "in_repair", "label": "В ремонте"},
            {"value": "ready", "label": "Готов"},
            {"value": "unrepairable", "label": "Ремонт невозможен"},
            {"value": "issued", "label": "Выдан"},
            {"value": "canceled", "label": "Отменён"}
        ],
        "priorities": [],
        "device_types": []
    }))

    res = client.get("/repairs")
    assert res.status_code == 200
    html = res.text
    assert "Принят" in html
    assert "Диагностика" in html
    assert "Ожидает клиента" in html
    assert "Ожидает запчасти" in html
    assert "В ремонте" in html
    assert "Готов" in html
    assert "Ремонт невозможен" in html
    assert "Выдан" in html
    assert "Отменён" in html
