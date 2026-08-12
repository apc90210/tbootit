from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_empty_cart_products_link_canonical():
    """Verify that an empty cart renders a link to /inventory/products and does NOT contain href="/products"."""
    response = client.get("/cart")
    assert response.status_code == 200
    assert 'href="/inventory/products"' in response.text
    assert 'href="/products"' not in response.text
