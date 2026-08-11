import pytest
import respx
from httpx import Response
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)
CORE_URL = settings.core_api_base_url.rstrip("/")

@pytest.fixture
def mock_core():
    with respx.mock(base_url=CORE_URL) as respx_mock:
        yield respx_mock

def test_products_list_empty_cart_button_hidden(mock_core):
    mock_core.get("/api/products/").mock(return_value=Response(200, json={
        "items": [],
        "total": 0,
        "page": 1,
        "size": 50,
        "pages": 0
    }))
    mock_core.get("/api/products/filter-options").mock(return_value=Response(200, json={}))

    res = client.get("/products")
    assert res.status_code == 200
    html = res.text
    assert 'id="go-to-cart-button"' in html
    assert 'display: none;' in html

def test_products_list_quick_add_form_elements(mock_core):
    mock_core.get("/api/products/").mock(return_value=Response(200, json={
        "items": [{
            "id": 200,
            "title": "Sample Product",
            "price": 1500.0,
            "quantity": 2,
            "status": "in_stock",
            "storage_location": "store",
            "barcode": "123456789"
        }],
        "total": 1,
        "page": 1,
        "size": 50,
        "pages": 1
    }))
    mock_core.get("/api/products/filter-options").mock(return_value=Response(200, json={}))

    res = client.get("/products")
    assert res.status_code == 200
    html = res.text
    assert 'class="quick-add-form"' in html
    assert 'class="btn btn-danger quick-add-btn"' in html
    assert 'cart_quick_add.js' in html

def test_non_js_fallback_redirect(mock_core):
    mock_core.get("/api/products/201").mock(return_value=Response(200, json={
        "id": 201,
        "title": "Fallback Item",
        "price": 2000.0,
        "quantity": 5,
        "status": "in_stock",
        "storage_location": "store"
    }))

    res = client.post("/cart/add", data={
        "product_id": 201,
        "quantity": 1,
        "return_url": "/products?brand=Apple"
    }, follow_redirects=False)

    assert res.status_code == 303
    assert res.headers["location"] == "/products?brand=Apple"
