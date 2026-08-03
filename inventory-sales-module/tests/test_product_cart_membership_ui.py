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

def test_products_list_empty_cart_no_local_cart_links(mock_core):
    mock_core.get("/api/products/").mock(return_value=Response(200, json={
        "items": [
            {"id": 10, "title": "Item A", "price": 100.0, "quantity": 5, "status": "in_stock", "storage_location": "store"},
            {"id": 20, "title": "Item B", "price": 200.0, "quantity": 5, "status": "in_stock", "storage_location": "store"}
        ],
        "total": 2, "page": 1, "size": 50, "pages": 1
    }))
    mock_core.get("/api/products/filter-options").mock(return_value=Response(200, json={}))

    res = client.get("/products")
    assert res.status_code == 200
    html = res.text
    # Both items have display: none for per-product cart link and quantity badge
    assert html.count('class="btn btn-success product-go-to-cart"') == 2
    assert html.count('display: none;') >= 4  # Top button (1) + per-product links (2) + quantity badges (2)

def test_products_list_one_item_in_cart_renders_local_cart_link(mock_core):
    mock_core.get("/api/products/10").mock(return_value=Response(200, json={
        "id": 10, "title": "Item A", "price": 100.0, "quantity": 5, "status": "in_stock", "storage_location": "store"
    }))
    mock_core.get("/api/products/").mock(return_value=Response(200, json={
        "items": [
            {"id": 10, "title": "Item A", "price": 100.0, "quantity": 5, "status": "in_stock", "storage_location": "store"},
            {"id": 20, "title": "Item B", "price": 200.0, "quantity": 5, "status": "in_stock", "storage_location": "store"}
        ],
        "total": 2, "page": 1, "size": 50, "pages": 1
    }))
    mock_core.get("/api/products/filter-options").mock(return_value=Response(200, json={}))

    # Add Item 10 to cart
    client.post("/cart/add", data={"product_id": 10, "quantity": 1})

    res = client.get("/products")
    assert res.status_code == 200
    html = res.text

    # Top cart button should be visible with (1)
    assert 'Перейти в корзину (<span>1</span>)' in html

    # Item 10 should have product-go-to-cart visible (no display: none) and quantity "В корзине: 1"
    assert 'data-product-id="10"' in html
    assert 'В корзине: <span class="product-cart-quantity-value">1</span>' in html
    assert 'data-product-id="20"' in html

def test_product_detail_cart_membership_rendering(mock_core):
    mock_core.get("/api/products/30/details").mock(return_value=Response(200, json={
        "id": 30, "title": "Detail Item", "price": 500.0, "quantity": 2, "status": "in_stock", "storage_location": "store"
    }))
    mock_core.get("/api/products/30").mock(return_value=Response(200, json={
        "id": 30, "title": "Detail Item", "price": 500.0, "quantity": 2, "status": "in_stock", "storage_location": "store"
    }))

    # Before adding to cart
    res1 = client.get("/products/30")
    assert res1.status_code == 200
    assert 'data-product-id="30"' in res1.text
    # Local cart link for 30 should be hidden initially
    assert 'class="btn btn-success product-go-to-cart" style="display: none;' in res1.text or 'class="btn btn-success product-go-to-cart" style="{% if product.id not in cart_product_ids %}display: none;{% endif %}' in res1.text or 'display: none;' in res1.text

    # Add to cart
    client.post("/cart/add", data={"product_id": 30, "quantity": 1})

    # After adding to cart
    res2 = client.get("/products/30")
    assert res2.status_code == 200
    # Local cart link for 30 should be visible
    assert 'В корзине: <span class="product-cart-quantity-value">1</span>' in res2.text

def test_after_checkout_local_cart_links_disappear(mock_core):
    mock_core.get("/api/products/40").mock(return_value=Response(200, json={
        "id": 40, "title": "Checkout Item", "price": 300.0, "quantity": 3, "status": "in_stock", "storage_location": "store"
    }))
    mock_core.get("/api/products/").mock(return_value=Response(200, json={
        "items": [{"id": 40, "title": "Checkout Item", "price": 300.0, "quantity": 3, "status": "in_stock", "storage_location": "store"}],
        "total": 1, "page": 1, "size": 50, "pages": 1
    }))
    mock_core.get("/api/products/filter-options").mock(return_value=Response(200, json={}))
    mock_core.post("/api/sales/").mock(return_value=Response(200, json={"id": 888, "status": "completed"}))

    # Add to cart
    client.post("/cart/add", data={"product_id": 40, "quantity": 1})

    # Perform checkout
    checkout_res = client.post("/cart/checkout", data={"payment_method": "cash"}, follow_redirects=False)
    assert checkout_res.status_code == 303

    # View products page after checkout
    res = client.get("/products")
    assert res.status_code == 200
    html = res.text

    # Top cart button hidden
    assert 'id="go-to-cart-button"' in html
    assert 'display: none;' in html
    # Local quantity value should be 0 and hidden
    assert 'В корзине: <span class="product-cart-quantity-value">0</span>' in html
