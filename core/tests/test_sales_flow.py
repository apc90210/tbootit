import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import models
from app.database import Base, engine, get_db
import json
from datetime import datetime

client = TestClient(app)

import uuid

def test_create_product_and_sale():
    unique_suffix = str(uuid.uuid4())[:8]
    # Create product
    response = client.post("/api/products/", json={
        "sku": f"SALE-TEST-001-{unique_suffix}",
        "title": "Sale Test Product",
        "sale_price": 500.0,
        "status": "in_stock"
    })
    assert response.status_code == 200
    p1_id = response.json()["id"]
    
    # Create another product
    response = client.post("/api/products/", json={
        "sku": f"SALE-TEST-002-{unique_suffix}",
        "title": "Sale Test Product 2",
        "sale_price": 300.0,
        "status": "draft"
    })
    p2_id = response.json()["id"]

    # Test reject sale from draft product
    response = client.post("/api/sales/", json={
        "total_amount": 300.0,
        "payment_method": "cash",
        "items": [{"product_id": p2_id, "title": "Test 2", "price": 300.0, "quantity": 1}]
    })
    assert response.status_code == 400
    assert "Cannot sell product" in response.json()["detail"]

    # Test successful sale from in_stock
    response = client.post("/api/sales/", json={
        "total_amount": 500.0,
        "payment_method": "card",
        "items": [{"product_id": p1_id, "title": "Test 1", "price": 500.0, "quantity": 1}]
    })
    assert response.status_code == 200
    sale = response.json()
    assert sale["total_amount"] == 500.0
    assert sale["payment_method"] == "card"
    assert sale["status"] == "completed"
    sale_id = sale["id"]
    
    # Verify product is sold
    response = client.get(f"/api/products/{p1_id}")
    assert response.json()["status"] == "sold"
    
    # Verify event created
    response = client.get(f"/api/products/{p1_id}/details")
    events = response.json()["events"]
    assert any(e["event_type"] == "sale_completed" for e in events)

    # Test reject sale of sold product
    response = client.post("/api/sales/", json={
        "total_amount": 500.0,
        "payment_method": "cash",
        "items": [{"product_id": p1_id, "title": "Test 1", "price": 500.0, "quantity": 1}]
    })
    assert response.status_code == 400

    # Test cancel sale
    response = client.post(f"/api/sales/{sale_id}/cancel", json={"reason": "Customer changed mind"})
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    
    # Verify product is in_stock
    response = client.get(f"/api/products/{p1_id}")
    assert response.json()["status"] == "in_stock"
    
    # Verify event created
    response = client.get(f"/api/products/{p1_id}/details")
    events = response.json()["events"]
    assert any(e["event_type"] == "sale_cancelled" for e in events)

def test_invalid_payment_method():
    response = client.post("/api/sales/", json={
        "total_amount": 100.0,
        "payment_method": "bitcoin",
        "items": [{"product_id": 1, "title": "Test", "price": 100.0, "quantity": 1}]
    })
    assert response.status_code == 400
    assert "Invalid payment method" in response.json()["detail"]

def test_get_sales():
    response = client.get("/api/sales/")
    assert response.status_code == 200
    assert "items" in response.json()
    
    response = client.get("/api/sales/today")
    assert response.status_code == 200
    assert "items" in response.json()
