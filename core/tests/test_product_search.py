import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_search_product(sku, title, brand="TestBrand", model="TestModel"):
    resp = client.post("/api/products/", json={
        "sku": sku,
        "title": title,
        "brand": brand,
        "model": model,
        "sale_price": 5000,
        "quantity": 10,
        "storage_location": "store",
        "status": "in_stock"
    })
    assert resp.status_code == 200, resp.text
    return resp.json()

def test_search_by_barcode():
    unique_suffix = uuid.uuid4().hex[:6]
    sku = f"SRCH-BC-{unique_suffix}"
    prod = create_search_product(sku, f"Product Search Barcode {unique_suffix}")
    
    # Generate barcode
    bc = client.post(f"/api/products/{prod['id']}/barcode/generate").json()["barcode"]

    # Search by exact barcode
    res = client.get(f"/api/products/?q={bc}").json()
    assert res["total"] >= 1
    assert res["items"][0]["id"] == prod["id"]
    assert res["items"][0]["barcode"] == bc

def test_search_by_sku():
    unique_suffix = uuid.uuid4().hex[:6]
    sku = f"SRCH-SKU-{unique_suffix}"
    prod = create_search_product(sku, f"Product Search SKU {unique_suffix}")

    res = client.get(f"/api/products/?q={sku}").json()
    assert res["total"] >= 1
    assert any(item["id"] == prod["id"] for item in res["items"])

def test_search_by_id():
    unique_suffix = uuid.uuid4().hex[:6]
    sku = f"SRCH-ID-{unique_suffix}"
    prod = create_search_product(sku, f"Product Search ID {unique_suffix}")

    pid = prod["id"]
    res = client.get(f"/api/products/?q={pid}").json()
    assert res["total"] >= 1
    assert any(item["id"] == pid for item in res["items"])

def test_search_by_name():
    unique_name = f"UniqueTitleKey_{uuid.uuid4().hex[:6]}"
    sku = f"SRCH-NAME-{uuid.uuid4().hex[:6]}"
    prod = create_search_product(sku, f"Special {unique_name} Device")

    res = client.get(f"/api/products/?q={unique_name}").json()
    assert res["total"] >= 1
    assert res["items"][0]["id"] == prod["id"]
