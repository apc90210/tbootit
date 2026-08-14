import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_owner_product_list_has_product_detail_links():
    """Verify owner product list at /inventory/products contains links to product details."""
    res = client.get("/inventory/products")
    assert res.status_code == 200
    assert "href=\"/inventory/products/" in res.text
    assert "Ошибка Core API" not in res.text

def test_owner_product_link_opens_product_detail():
    """Verify navigating to product detail route returns 200 without Core API error."""
    res = client.get("/inventory/products/58")
    assert res.status_code == 200
    assert "Ошибка Core API" not in res.text
    assert "Товар не найден" not in res.text

def test_product_detail_58_returns_200():
    """Verify Product 58 detail page returns 200 OK and valid page structure."""
    res = client.get("/inventory/products/58")
    assert res.status_code == 200
    assert "Ошибка Core API" not in res.text
