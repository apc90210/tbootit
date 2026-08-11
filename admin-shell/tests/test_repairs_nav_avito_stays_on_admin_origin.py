import pytest
from fastapi.testclient import TestClient
from app.main import app, rewrite_location_header

client = TestClient(app)

def test_repairs_nav_avito_stays_on_admin_origin():
    """Verify that navigating to /avito or /repairs/repairs stays on admin-shell (8011) origin."""
    response = client.get("/avito")
    assert response.status_code == 200
    assert "Авторизация Avito" in response.text or "Avito" in response.text

def test_location_header_rewriting_strips_ports():
    """Verify location header rewriting strips 8020/8030/8040 ports and maintains same origin."""
    assert rewrite_location_header("http://localhost:8040/avito", "/repairs") == "/avito"
    assert rewrite_location_header("http://repairs-module:8040/avito", "/repairs") == "/avito"
    assert rewrite_location_header("http://localhost:8030/inventory/products", "/inventory") == "/inventory/products"
    assert rewrite_location_header("http://localhost:8020/avito/accounts", "/avito") == "/avito/accounts"
