import pytest
import respx
from httpx import Response
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

CORE_URL = settings.core_api_base_url.rstrip("/")

@pytest.fixture
def mock_core():
    with respx.mock(base_url=CORE_URL) as respx_mock:
        yield respx_mock

def test_quick_add_success_json(mock_core):
    mock_core.get("/api/products/100").mock(return_value=Response(200, json={
        "id": 100,
        "title": "Test Phone",
        "price": 10000.0,
        "sale_price": 9500.0,
        "quantity": 5,
        "status": "in_stock",
        "storage_location": "store"
    }))

    res = client.post("/cart/add-quick", data={"product_id": 100, "quantity": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["cart_items_count"] == 1
    assert data["cart_lines_count"] == 1
    assert data["product_id"] == 100
    assert data["product_quantity_in_cart"] == 1
    assert "Test Phone" in data["message"]

def test_quick_add_no_redirect(mock_core):
    mock_core.get("/api/products/101").mock(return_value=Response(200, json={
        "id": 101,
        "title": "Test Laptop",
        "price": 50000.0,
        "quantity": 3,
        "status": "in_stock",
        "storage_location": "store"
    }))

    res = client.post("/cart/add", data={"product_id": 101, "quantity": 1}, headers={"X-Requested-With": "XMLHttpRequest"})
    assert res.status_code == 200
    assert "location" not in res.headers

def test_quick_add_readd_quantity_limit(mock_core):
    mock_core.get("/api/products/102").mock(return_value=Response(200, json={
        "id": 102,
        "title": "Limited Item",
        "price": 1000.0,
        "quantity": 1,
        "status": "in_stock",
        "storage_location": "store"
    }))

    # First add succeeds
    res1 = client.post("/cart/add-quick", data={"product_id": 102, "quantity": 1})
    assert res1.status_code == 200
    assert res1.json()["ok"] is True

    # Second add exceeds quantity=1 -> blocked with 409
    res2 = client.post("/cart/add-quick", data={"product_id": 102, "quantity": 1})
    assert res2.status_code == 409
    data2 = res2.json()
    assert data2["ok"] is False
    assert "Нельзя добавить больше 1 шт" in data2["message"]

def test_quick_add_reserved_blocked(mock_core):
    mock_core.get("/api/products/103").mock(return_value=Response(200, json={
        "id": 103,
        "title": "Reserved Item",
        "price": 1000.0,
        "quantity": 1,
        "status": "reserved",
        "storage_location": "store"
    }))

    res = client.post("/cart/add-quick", data={"product_id": 103})
    assert res.status_code == 409
    assert res.json()["ok"] is False
    assert " зарезервирован " in res.json()["message"]

def test_quick_add_sold_blocked(mock_core):
    mock_core.get("/api/products/104").mock(return_value=Response(200, json={
        "id": 104,
        "title": "Sold Item",
        "price": 1000.0,
        "quantity": 0,
        "status": "sold",
        "storage_location": "store"
    }))

    res = client.post("/cart/add-quick", data={"product_id": 104})
    assert res.status_code == 409
    assert res.json()["ok"] is False
    assert " уже продан" in res.json()["message"]

def test_quick_add_draft_blocked(mock_core):
    mock_core.get("/api/products/105").mock(return_value=Response(200, json={
        "id": 105,
        "title": "Draft Item",
        "price": 1000.0,
        "quantity": 1,
        "status": "draft",
        "storage_location": "store"
    }))

    res = client.post("/cart/add-quick", data={"product_id": 105})
    assert res.status_code == 409
    assert res.json()["ok"] is False
    assert "не готов" in res.json()["message"] or "черновик" in res.json()["message"] or "Черновик" in res.json()["message"]

def test_quick_add_zero_quantity_blocked(mock_core):
    mock_core.get("/api/products/106").mock(return_value=Response(200, json={
        "id": 106,
        "title": "Out of stock Item",
        "price": 1000.0,
        "quantity": 0,
        "status": "in_stock",
        "storage_location": "store"
    }))

    res = client.post("/cart/add-quick", data={"product_id": 106})
    assert res.status_code == 409
    assert res.json()["ok"] is False
    assert "отсутствует в остатках" in res.json()["message"]

def test_quick_add_wrong_location_blocked(mock_core):
    mock_core.get("/api/products/107").mock(return_value=Response(200, json={
        "id": 107,
        "title": "Workshop Item",
        "price": 1000.0,
        "quantity": 1,
        "status": "in_stock",
        "storage_location": "workshop"
    }))

    res = client.post("/cart/add-quick", data={"product_id": 107})
    assert res.status_code == 409
    assert res.json()["ok"] is False
    assert "workshop" in res.json()["message"]

def test_quick_add_unknown_product_returns_russian_error(mock_core):
    mock_core.get("/api/products/99999").mock(return_value=Response(404, json={"detail": "Not Found"}))

    res = client.post("/cart/add-quick", data={"product_id": 99999})
    assert res.status_code == 404
    data = res.json()
    assert data["ok"] is False
    assert "не найден" in data["message"]
