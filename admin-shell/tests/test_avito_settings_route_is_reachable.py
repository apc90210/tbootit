import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_avito_settings_route_is_reachable():
    """Verify /avito settings route is accessible and returns owner UI HTML."""
    response = client.get("/avito")
    assert response.status_code == 200
    html = response.text
    assert "Avito" in html
    assert "avito" in html.lower()
