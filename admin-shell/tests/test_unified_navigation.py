import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_top_navigation_links_on_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert 'href="/inventory/products"' in html
    assert 'href="/inventory/sales"' in html
    assert 'href="/inventory/reports/sales"' in html
    assert 'href="/repairs/repairs"' in html
    assert 'href="/avito/extension"' in html

def test_top_navigation_links_on_avito_pages():
    for url in ["/avito/extension"]:
        response = client.get(url)
        assert response.status_code == 200
        html = response.text
        assert 'href="/inventory/products"' in html
        assert 'href="/inventory/sales"' in html
        assert 'href="/inventory/reports/sales"' in html
        assert 'href="/repairs/repairs"' in html
        assert 'href="/avito/extension"' in html
