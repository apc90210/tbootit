from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_navigation_has_no_price_tags_section():
    response = client.get("/products")
    assert response.status_code == 200
    # Navbar must not contain "Ценники — скоро" or separate Ценники section in top nav
    assert "Ценники — скоро" not in response.text
