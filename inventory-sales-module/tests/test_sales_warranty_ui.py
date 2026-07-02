import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_sales_new_form_has_warranty_fields(respx_mock):
    # Mock core_client.get_product_details to return a valid product
    respx_mock.get("http://core:8000/api/products/1/details").mock(
        return_value=httpx.Response(200, json={"id": 1, "title": "Test Product", "status": "in_stock", "price": 1000})
    )
    
    resp = client.get("/sales/new?product_id=1")
    assert resp.status_code == 200
    
    html = resp.content.decode('utf-8')
    assert 'name="quantity"' in html
    assert 'name="warranty_days"' in html
    assert 'name="no_warranty"' in html

import httpx
import re

def test_sale_create_passes_warranty_and_quantity(respx_mock):
    # We can inspect the POST body by checking the route
    route = respx_mock.post(re.compile(r".*/api/sales/?")).mock(
        return_value=httpx.Response(200, json={"id": 99})
    )
    
    respx_mock.get(re.compile(r".*/api/products/1")).mock(
        return_value=httpx.Response(200, json={"id": 1, "title": "Test Product"})
    )
    
    resp = client.post(
        "/sales/create",
        data={
            "product_id": 1,
            "price": 1000,
            "quantity": 2,
            "payment_method": "cash",
            "warranty_days": 14,
            "no_warranty": "False",
            "notes": "Test"
        },
        follow_redirects=False
    )
    
    assert resp.status_code == 303, resp.content.decode('utf-8')
    assert resp.headers["Location"] == "/sales/99"
    
    assert route.called
    req = route.calls.last.request
    import json
    body = json.loads(req.content)
    assert body["total_amount"] == 2000.0
    assert body["warranty_days"] == 14
    assert body["warranty_enabled"] is True
    assert body["items"][0]["quantity"] == 2
    assert body["items"][0]["price"] == 1000.0

def test_sale_receipt_page(respx_mock):
    respx_mock.get(re.compile(r".*/api/sales/99")).mock(
        return_value=httpx.Response(200, json={
            "id": 99, 
            "total_amount": 2000, 
            "payment_method": "cash",
            "warranty_enabled": True,
            "warranty_days": 14,
            "items": [
                {"title": "Test Product", "quantity": 2, "price": 1000}
            ]
        })
    )
    
    resp = client.get("/sales/99/receipt")
    assert resp.status_code == 200
    
    html = resp.content.decode('utf-8')
    assert "ТОВАРНЫЙ ЧЕК" in html
    assert "14 дней" in html
    assert "Test Product" in html
    assert "2 шт." in html

def test_price_tag_page(respx_mock):
    respx_mock.get(re.compile(r".*/api/products/1/details")).mock(
        return_value=httpx.Response(200, json={
            "id": 1,
            "title": "Test Product",
            "sku": "123",
            "sale_price": 1000,
            "status": "in_stock"
        })
    )
    
    resp = client.get("/products/1/price-tag")
    assert resp.status_code == 200
    
    html = resp.content.decode('utf-8')
    assert "Test Product" in html
    assert "1000" in html
    assert "Арт: 123" in html
