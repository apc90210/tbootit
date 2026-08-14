import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cross_module_links_same_origin():
    """
    Ensures links between modules (Avito Extension -> Products, Repairs, etc.)
    all maintain the same-origin localhost:8011 base structure.
    """
    res = client.get("/avito/extension")
    assert res.status_code == 200
    assert 'href="/inventory/products"' in res.text
    assert 'href="/repairs/repairs"' in res.text
