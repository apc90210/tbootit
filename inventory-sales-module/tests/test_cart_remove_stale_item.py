from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cart_remove_stale_or_unavailable_item():
    """Verify item can be removed from cart even if product is unavailable or deleted from Core API."""
    add_res = client.post("/cart/add", data={
        "product_id": 8888,
        "title": "Удалённый товар",
        "price": 500.0,
        "quantity": 1
    }, follow_redirects=False)

    # Remove stale item
    rem_res = client.post("/cart/remove", data={"product_id": 8888}, follow_redirects=False)
    assert rem_res.status_code == 303
    assert rem_res.headers.get("location", "") in ["/cart", "/inventory/cart"]
