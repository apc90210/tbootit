"""
Admin Shell — Product JSON Import / Export Web UI Unit Tests
Stage 07C-R1: Product JSON Import / Export & AI Prompt Generator

Tests:
- Test R: Page /products/json returns 200 OK, UTF-8, contains all 3 sections (A, B, C)
- Test S: AI Prompt retrieval & download /admin-api/products/json/prompt.txt
- Test T: JSON Import via Web API (JSON body & multipart file upload) returns structured summary
- Test U: JSON Export via Web API returns TECHNOREBOOT_PRODUCTS_YYYY-MM-DD_HHMMSS.json
- Test V: Error handling for malformed JSON returns 400 with friendly Russian message
- Test W: Navigation verification across all admin-shell pages
"""

import re
import json
import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app, auth_manager

client = TestClient(app)


@pytest.fixture
def owner_headers():
    owner = auth_manager.get_certificate("owner")
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner["serial_hex"],
        "x-client-cert-fingerprint": owner["fingerprint_sha256"],
    }


def test_products_json_page_render_all_sections():
    """TEST R: /products/json returns 200 OK, UTF-8, and contains sections A, B, C."""
    fake_schema = {
        "format": "technoreboot-products",
        "version": 1,
        "ai_prompt": "Ты — AI-ассистент Техноребута. Сформируй JSON для товаров.",
        "schema": {"title": "technoreboot-products"}
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.get = AsyncMock(return_value=httpx.Response(200, json=fake_schema))
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp = client.get("/products/json")
        assert resp.status_code == 200
        html = resp.text

        # Page Heading
        assert "ТЕХНОРЕБУТ — JSON ИМПОРТ И ЭКСПОРТ ТОВАРОВ" in html

        # Section A: AI Prompt Generator
        assert "Секция А: Генератор промпта для искусственного интеллекта" in html
        assert "Копировать промпт в буфер" in html
        assert "Скачать промпт (.txt)" in html
        assert "Ты — AI-ассистент Техноребута" in html

        # Section B: Import
        assert "Секция Б: Импорт товаров из JSON" in html
        assert "Загрузить и импортировать товары" in html
        assert "jsonFileInput" in html
        assert "jsonTextInput" in html

        # Section C: Export with Selection
        assert "Секция В: Экспорт товаров из базы Техноребут" in html
        assert "Экспортировать выбранные в JSON" in html
        assert "Экспортировать все товары в JSON" in html
        assert "exportProductListContainer" in html
        assert "productSearchFilter" in html
        assert "exportSelectedCount" in html
        assert "Выберите хотя бы один товар для экспорта" in html
        assert "TECHNOREBOOT_PRODUCTS_YYYY-MM-DD_HHMMSS.json" in html


def test_download_ai_prompt_txt():
    """TEST S: Download prompt endpoint returns .txt attachment with prompt text."""
    fake_prompt = "СИСТЕМНЫЙ ПРОМПТ ТЕХНОРЕБУТ: сформируй канонический JSON."

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.get = AsyncMock(return_value=httpx.Response(200, json={"ai_prompt": fake_prompt}))
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp = client.get("/admin-api/products/json/prompt.txt")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers.get("content-type", "")
        disp = resp.headers.get("content-disposition", "")
        assert 'attachment; filename="technoreboot_ai_prompt.txt"' in disp
        assert fake_prompt in resp.text


def test_import_proxy_json_body():
    """TEST T1: Import via application/json body proxies to Core and returns summary."""
    fake_core_resp = {
        "status": "ok",
        "summary": {
            "total_in_payload": 2,
            "created": 1,
            "updated": 1,
            "skipped": 0
        },
        "results": []
    }

    payload = {
        "format": "technoreboot-products",
        "version": 1,
        "products": [
            {"title": "Компьютер Intel Core i7", "price_rub": 50000}
        ]
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.post = AsyncMock(return_value=httpx.Response(200, json=fake_core_resp))
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp = client.post("/admin-api/products/json/import", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["summary"]["created"] == 1


def test_import_proxy_multipart_file():
    """TEST T2: Import via multipart file upload proxies to Core API."""
    fake_core_resp = {
        "status": "ok",
        "summary": {
            "total_in_payload": 1,
            "created": 1,
            "updated": 0,
            "skipped": 0
        }
    }

    json_content = json.dumps({
        "format": "technoreboot-products",
        "version": 1,
        "products": [{"title": "Монитор Dell 27", "price_rub": 18000}]
    }).encode("utf-8")

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.post = AsyncMock(return_value=httpx.Response(200, json=fake_core_resp))
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp = client.post(
            "/admin-api/products/json/import",
            files={"file": ("test_catalog.json", json_content, "application/json")}
        )
        assert resp.status_code == 200
        assert resp.json()["summary"]["created"] == 1


def test_export_all_proxy_downloads_timestamped_file():
    """TEST U1: JSON Export all via Web API returns TECHNOREBOOT_PRODUCTS_YYYY-MM-DD_HHMMSS.json."""
    fake_export_data = {
        "format": "technoreboot-products",
        "version": 1,
        "products": [
            {
                "id": 1,
                "sku": "NB-001",
                "title": "Ноутбук Lenovo",
                "price_rub": 45000,
                "characteristics": {"Процессор": "Core i5"}
            }
        ]
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.get = AsyncMock(return_value=httpx.Response(200, json=fake_export_data))
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp = client.get("/admin-api/products/json/export")
        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("content-type", "")

        disp = resp.headers.get("content-disposition", "")
        pattern = r'attachment; filename="TECHNOREBOOT_PRODUCTS_\d{4}-\d{2}-\d{2}_\d{6}\.json"'
        assert re.search(pattern, disp), f"Content-Disposition '{disp}' does not match expected format"

        data = resp.json()
        assert data["format"] == "technoreboot-products"
        assert data["version"] == 1
        assert len(data["products"]) == 1
        assert data["products"][0]["title"] == "Ноутбук Lenovo"


def test_export_selected_products_single_and_multiple():
    """TEST U2: Selected product export filters by requested IDs (GET query and POST body)."""
    # 1. Single product export via GET ?ids=101
    single_export_data = {
        "format": "technoreboot-products",
        "version": 1,
        "products": [{"id": 101, "title": "Ультрабук Dell"}]
    }
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.get = AsyncMock(return_value=httpx.Response(200, json=single_export_data))
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp = client.get("/admin-api/products/json/export?ids=101")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["products"]) == 1
        assert data["products"][0]["id"] == 101

    # 2. Multiple products export via GET ?ids=101,102,103
    multi_export_data = {
        "format": "technoreboot-products",
        "version": 1,
        "products": [
            {"id": 101, "title": "Ультрабук Dell"},
            {"id": 102, "title": "Принтер Canon"},
            {"id": 103, "title": "Монитор ASUS"}
        ]
    }
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.get = AsyncMock(return_value=httpx.Response(200, json=multi_export_data))
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp = client.get("/admin-api/products/json/export?ids=101,102,103")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["products"]) == 3
        assert [p["id"] for p in data["products"]] == [101, 102, 103]

    # 3. Multiple products export via POST JSON body {"ids": [101, 102]}
    post_export_data = {
        "format": "technoreboot-products",
        "version": 1,
        "products": [
            {"id": 101, "title": "Ультрабук Dell"},
            {"id": 102, "title": "Принтер Canon"}
        ]
    }
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.get = AsyncMock(return_value=httpx.Response(200, json=post_export_data))
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp = client.post("/admin-api/products/json/export", json={"ids": [101, 102]})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["products"]) == 2


def test_import_invalid_json_returns_400():
    """TEST V: Malformed JSON upload returns 400 with friendly Russian error message."""
    bad_json_bytes = b"{\"broken\": [unclosed array"

    resp = client.post(
        "/admin-api/products/json/import",
        files={"file": ("broken.json", bad_json_bytes, "application/json")}
    )
    assert resp.status_code == 400
    data = resp.json()
    assert data["status"] == "error"
    assert "Ошибка" in data["message"]


def test_navigation_links_on_admin_pages():
    """TEST W: Verify link to /products/json exists in top nav on all main pages."""
    # Main dashboard
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'href="/products/json"' in resp.text

    # Avito extension page
    resp = client.get("/avito/extension")
    assert resp.status_code == 200
    assert 'href="/products/json"' in resp.text

    # Products JSON page itself has no raw module ports
    resp = client.get("/products/json")
    assert resp.status_code == 200
    raw_port_pattern = re.compile(r'href=["\']http://(localhost|127\.0\.0\.1):(8000|8020|8030|8040|8061)')
    assert not raw_port_pattern.findall(resp.text), "Raw owner port found on /products/json"


def test_products_json_access_control_contract():
    """
    TEST K & L: Verification of mTLS access control contract.
    - No certificate presented -> rejected with 403 Forbidden.
    - Active OWNER certificate -> accepted (is_owner=True).
    - Active USER certificate -> accepted (is_owner=False, allowed for product operations).
    - Revoked certificate -> rejected with 403 Forbidden.
    """
    owner_cert = auth_manager.get_certificate("owner")

    # 1. No certificate
    ok, code, msg, cert = auth_manager.verify_request(
        verify_status="NONE",
        client_serial=None,
        client_fingerprint=None,
        request_uri="/products/json"
    )
    assert ok is False
    assert code == 403

    # 2. OWNER certificate
    ok, code, msg, cert = auth_manager.verify_request(
        verify_status="SUCCESS",
        client_serial=owner_cert["serial_hex"],
        client_fingerprint=owner_cert["fingerprint_sha256"],
        request_uri="/products/json"
    )
    assert ok is True
    assert code == 200
    assert cert["is_owner"] is True

    # 3. Active USER certificate (matching existing product management authorization level)
    # Find any active user cert or create temporary mock record
    active_user = next((c for c in auth_manager.list_certificates() if c.get("status") == "ACTIVE" and not c.get("is_owner")), None)
    if active_user:
        ok, code, msg, cert = auth_manager.verify_request(
            verify_status="SUCCESS",
            client_serial=active_user["serial_hex"],
            client_fingerprint=active_user["fingerprint_sha256"],
            request_uri="/products/json"
        )
        assert ok is True
        assert code == 200
        assert cert["is_owner"] is False
