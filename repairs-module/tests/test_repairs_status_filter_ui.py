import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_OPTIONS = {
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
    "priorities": [
        {"value": "normal", "label": "Обычный"},
        {"value": "urgent", "label": "Срочный"}
    ],
    "device_types": ["Ноутбук", "Телефон"]
}

MOCK_REPAIRS_RESPONSE = {
    "items": [
        {
            "id": 1,
            "number": "R-202608-001",
            "status": "diagnostics",
            "status_label": "Диагностика",
            "customer_name": "Иван Тестов",
            "customer_phone": "+79991112233",
            "device_type": "Ноутбук",
            "brand": "Asus",
            "model": "ROG",
            "reported_issue": "Не включается",
            "priority": "normal",
            "priority_label": "Обычный",
            "assigned_to": "Мастер",
            "accepted_at": "2026-08-05T10:00:00"
        }
    ],
    "total": 1,
    "page": 1,
    "page_size": 50
}

def test_repairs_status_filter_ui_elements_and_persistence():
    """
    Test UI rendering of repair status filter:
    - Visible <select name="status">
    - Option "Все статусы"
    - All status options with Russian labels from Core
    - Persistence of selected status in HTML
    - Preservation of other query parameters in hidden inputs and links
    """
    with patch("app.routers.repairs.core_client.get_repair_options", new_callable=AsyncMock) as mock_opts, \
         patch("app.routers.repairs.core_client.get_repairs", new_callable=AsyncMock) as mock_repairs:

        mock_opts.return_value = MOCK_OPTIONS
        mock_repairs.return_value = MOCK_REPAIRS_RESPONSE

        # Request with status=diagnostics & q=Asus
        response = client.get("/repairs?status=diagnostics&q=Asus&priority=normal")
        assert response.status_code == 200
        html = response.text

        # Verify Core API called with correct status parameter
        mock_repairs.assert_called_once()
        called_params = mock_repairs.call_args[0][0]
        assert called_params.get("status") == "diagnostics"
        assert called_params.get("q") == "Asus"
        assert called_params.get("priority") == "normal"

        # Verify select element exists
        assert '<select name="status"' in html
        assert 'id="status"' in html
        assert 'onchange="this.form.submit()"' in html
        assert '<option value="">Все статусы</option>' in html

        # Verify all options and Russian labels rendered
        for st in MOCK_OPTIONS["statuses"]:
            assert f'value="{st["value"]}"' in html
            assert st["label"] in html

        # Verify selected status has selected attribute
        assert '<option value="diagnostics" selected>' in html

        # Verify reset button link
        assert 'href="/repairs"' in html
        assert 'Сбросить фильтры' in html

def test_repairs_status_filter_ui_empty_result():
    """
    Test empty result rendering when status filter returns 0 records:
    - Clear explanatory message: "Ремонты с выбранным статусом не найдены."
    - Reset filters button
    """
    with patch("app.routers.repairs.core_client.get_repair_options", new_callable=AsyncMock) as mock_opts, \
         patch("app.routers.repairs.core_client.get_repairs", new_callable=AsyncMock) as mock_repairs:

        mock_opts.return_value = MOCK_OPTIONS
        mock_repairs.return_value = {"items": [], "total": 0, "page": 1, "page_size": 50}

        response = client.get("/repairs?status=unrepairable")
        assert response.status_code == 200
        html = response.text

        assert "Ремонты с выбранным статусом не найдены." in html
        assert 'href="/repairs"' in html
        assert "Сбросить фильтры" in html

def test_repairs_status_filter_pagination_preserves_query_params():
    """
    Test that pagination links preserve status and all active query parameters.
    """
    many_items = {
        "items": [MOCK_REPAIRS_RESPONSE["items"][0]],
        "total": 120,
        "page": 1,
        "page_size": 50
    }
    with patch("app.routers.repairs.core_client.get_repair_options", new_callable=AsyncMock) as mock_opts, \
         patch("app.routers.repairs.core_client.get_repairs", new_callable=AsyncMock) as mock_repairs:

        mock_opts.return_value = MOCK_OPTIONS
        mock_repairs.return_value = many_items

        response = client.get("/repairs?status=ready&q=HP&page=1")
        assert response.status_code == 200
        html = response.text

        # Verify page 2 link contains status=ready and q=HP
        assert 'page=2' in html
        assert 'status=ready' in html
        assert 'q=HP' in html

def test_no_direct_db_imports_in_repairs_module():
    """
    Verify that repairs-module contains zero direct DB imports or connections.
    """
    import os, glob
    files = glob.glob("app/**/*.py", recursive=True)
    forbidden_terms = ["create_engine", "SessionLocal", "sqlite", "technoreboot.db", "sqlalchemy"]
    for filePath in files:
        with open(filePath, "r", encoding="utf-8") as f:
            content = f.read()
            for term in forbidden_terms:
                assert term not in content, f"Forbidden direct DB term '{term}' found in {filePath}"
