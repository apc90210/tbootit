from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_no_price_tags_nav():
    response = client.get("/products")
    assert response.status_code == 200
    # Make sure there is no standalone nav link for price tags
    assert "Ценники" not in response.text
