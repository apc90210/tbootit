from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@patch("app.routers.cart.core_client", new_callable=AsyncMock)
def test_cart_products_link_same_origin(mock_core):
    """Verify that cart actions maintain same-origin /inventory/products navigation links."""
    # View cart with items
    client.post("/cart/add", data={"product_id": "58", "title": "HP M252n", "price": "6900.0"}, follow_redirects=True)
    res = client.get("/cart")
    assert res.status_code == 200
    assert 'href="/inventory/products"' in res.text
    assert 'href="/products"' not in res.text

    # Clear cart and verify empty cart link
    client.post("/cart/clear", follow_redirects=True)
    res_empty = client.get("/cart")
    assert res_empty.status_code == 200
    assert 'href="/inventory/products"' in res_empty.text
    assert 'href="/products"' not in res_empty.text
