import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_owner_origin_contract_routes():
    """Verify that all core owner-facing dashboard routes are served on origin 8011 without 404."""
    routes = [
        "/",
        "/avito",
        "/avito/accounts",
        "/avito/probe"
    ]
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, f"Route {route} returned HTTP {response.status_code}"
