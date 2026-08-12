from unittest.mock import patch, AsyncMock
from fastapi.responses import Response
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("app.main._proxy_request")
def test_empty_cart_inventory_route_proxy(mock_proxy):
    """Verify that proxying /inventory/cart returns empty cart HTML with canonical /inventory/products link."""
    cart_html = '''
    <div style="text-align: center; padding: 50px;">
        <h3>Корзина пуста</h3>
        <a href="/inventory/products" class="btn btn-primary">Перейти к товарам</a>
    </div>
    '''
    mock_proxy.return_value = Response(content=cart_html, status_code=200, media_type="text/html")

    response = client.get("/inventory/cart")
    assert response.status_code == 200
    assert 'href="/inventory/products"' in response.text
    assert 'href="/products"' not in response.text
