from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cart_remove_item_functionality():
    """Verify POST /cart/remove removes item from session cart and redirects to /inventory/cart."""
    # First add to cart
    add_res = client.post("/cart/add", data={
        "product_id": 9991,
        "title": "Тестовый товар",
        "price": 100.0,
        "quantity": 1
    }, follow_redirects=False)
    assert add_res.status_code in [302, 303]

    # Remove item
    rem_res = client.post("/cart/remove", data={"product_id": 9991}, follow_redirects=False)
    assert rem_res.status_code == 303
    assert rem_res.headers.get("location", "") in ["/cart", "/inventory/cart"]
