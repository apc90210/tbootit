import pytest
from fastapi.testclient import TestClient
from app.main import app, auth_manager
import re
from pathlib import Path

client = TestClient(app)

@pytest.fixture
def owner_headers():
    owner = auth_manager.get_certificate("owner")
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner["serial_hex"] if owner else "test_serial",
        "x-client-cert-fingerprint": owner["fingerprint_sha256"] if owner else "test_fp",
        "x-auth-is-owner": "true",
    }

EXPECTED_LINKS = [
    ("/", "Панель управления"),
    ("/inventory/products", "Товары"),
    ("/products/json", "JSON импорт / экспорт"),
    ("/inventory/sales", "Продажи"),
    ("/inventory/cart", "Корзина"),
    ("/inventory/reports/sales", "Отчёты"),
    ("/repairs/repairs", "Ремонты"),
    ("/avito/extension", "Расширение Avito"),
    ("/inventory/settings/organization", "Настройки"),
    ("/backups", "Резервные копии"),
    ("/certificates", "Доступ (mTLS)"),
]

def assert_unified_navbar_in_html(html: str, context: str = ""):
    assert '<nav class="main-nav"' in html, f"Missing main-nav in {context}"
    assert "Техноребут" in html, f"Missing brand text in {context}"
    assert ">TR</span>" in html, f"Missing TR badge in {context}"
    
    for href, title in EXPECTED_LINKS:
        assert f'href="{href}"' in html, f"Missing link href '{href}' ({title}) in {context}"
        assert title in html, f"Missing link text '{title}' in {context}"
    
    assert "window.location.pathname" in html, f"Missing active navigation highlighter script in {context}"


def test_admin_shell_index_unified_navbar(owner_headers):
    resp = client.get("/", headers=owner_headers)
    assert resp.status_code == 200
    assert_unified_navbar_in_html(resp.text, "admin-shell index")


def test_admin_shell_backups_unified_navbar(owner_headers):
    resp = client.get("/backups", headers=owner_headers)
    assert resp.status_code == 200
    assert_unified_navbar_in_html(resp.text, "admin-shell backups")
    # Verify nav is placed outside narrow container
    nav_pos = resp.text.find('<nav class="main-nav"')
    container_pos = resp.text.find('<div class="container">')
    assert nav_pos != -1 and container_pos != -1
    assert nav_pos < container_pos, "main-nav must be placed before narrow container in backups.html"


def test_admin_shell_certificates_unified_navbar(owner_headers):
    resp = client.get("/certificates", headers=owner_headers)
    assert resp.status_code == 200
    assert_unified_navbar_in_html(resp.text, "admin-shell certificates")
    # Verify nav is placed outside narrow container
    nav_pos = resp.text.find('<nav class="main-nav"')
    container_pos = resp.text.find('<div class="container">')
    assert nav_pos != -1 and container_pos != -1
    assert nav_pos < container_pos, "main-nav must be placed before narrow container in certificates.html"


def test_admin_shell_products_json_unified_navbar():
    resp = client.get("/products/json")
    assert resp.status_code == 200
    assert_unified_navbar_in_html(resp.text, "admin-shell products_json")
    # Verify nav is placed outside narrow container
    nav_pos = resp.text.find('<nav class="main-nav"')
    container_pos = resp.text.find('<div class="container">')
    assert nav_pos != -1 and container_pos != -1
    assert nav_pos < container_pos, "main-nav must be placed before narrow container in products_json.html"


def test_admin_shell_avito_extension_unified_navbar():
    resp = client.get("/avito/extension")
    assert resp.status_code == 200
    assert_unified_navbar_in_html(resp.text, "admin-shell avito_extension")


def test_admin_shell_avito_unified_navbar():
    resp = client.get("/avito")
    assert resp.status_code == 200
    assert_unified_navbar_in_html(resp.text, "admin-shell avito")


def test_admin_shell_avito_accounts_unified_navbar():
    resp = client.get("/avito/accounts")
    assert resp.status_code == 200
    assert_unified_navbar_in_html(resp.text, "admin-shell avito_accounts")


def test_inventory_base_template_unified_navbar():
    repo_root = Path(__file__).resolve().parents[2]
    template_path = repo_root / "inventory-sales-module" / "app" / "templates" / "base.html"
    assert template_path.exists(), f"Template not found: {template_path}"
    content = template_path.read_text(encoding="utf-8")
    assert_unified_navbar_in_html(content, "inventory base.html")
    # Ensure disparate header banner is gone
    assert "Техноребут — Рабочее место магазина" not in content


def test_repairs_base_template_unified_navbar():
    repo_root = Path(__file__).resolve().parents[2]
    template_path = repo_root / "repairs-module" / "app" / "templates" / "base.html"
    assert template_path.exists(), f"Template not found: {template_path}"
    content = template_path.read_text(encoding="utf-8")
    assert_unified_navbar_in_html(content, "repairs base.html")
    # Ensure disparate header banner is gone
    assert "Техноребут — Модуль ремонтов" not in content
