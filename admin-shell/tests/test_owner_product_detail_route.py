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
    assert "Редактировать товар" in res.text
    assert "/inventory/products/58/edit" in res.text


def test_owner_product_new_and_edit_routes():
    """Verify owner product creation and editing routes proxy and redirect correctly."""
    # Product list has manual create button
    res_list = client.get("/inventory/products")
    assert res_list.status_code == 200
    assert "Создать товар вручную" in res_list.text
    assert "/inventory/products/new" in res_list.text

    # /inventory/products/new proxies cleanly
    res_new = client.get("/inventory/products/new")
    assert res_new.status_code == 200
    assert "Создание товара вручную" in res_new.text

    # /products/new shortcut redirects to /inventory/products/new
    res_new_redirect = client.get("/products/new", follow_redirects=False)
    assert res_new_redirect.status_code == 302
    assert res_new_redirect.headers["location"] == "/inventory/products/new"

    # /inventory/products/58/edit proxies cleanly
    res_edit = client.get("/inventory/products/58/edit")
    assert res_edit.status_code == 200
    assert "Редактирование товара" in res_edit.text

    # /products/58/edit shortcut redirects to /inventory/products/58/edit
    res_edit_redirect = client.get("/products/58/edit", follow_redirects=False)
    assert res_edit_redirect.status_code == 302
    assert res_edit_redirect.headers["location"] == "/inventory/products/58/edit"

