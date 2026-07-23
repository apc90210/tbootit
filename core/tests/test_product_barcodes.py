import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_test_product(sku_prefix="BC", status="in_stock", price=1000.0, barcode=None):
    sku = f"{sku_prefix}-{uuid.uuid4().hex[:8]}"
    payload = {
        "sku": sku,
        "title": f"Test Product {sku}",
        "sale_price": price,
        "quantity": 5,
        "storage_location": "store",
        "status": status
    }
    if barcode:
        payload["barcode"] = barcode
    resp = client.post("/api/products/", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()

def test_single_barcode_generation():
    prod = create_test_product(sku_prefix="SING")
    assert prod["barcode"] is None or prod["barcode"] == ""

    # Generate barcode
    gen_resp = client.post(f"/api/products/{prod['id']}/barcode/generate")
    assert gen_resp.status_code == 200
    data = gen_resp.json()
    assert data["generated"] == True
    assert data["barcode"].startswith("200")
    assert len(data["barcode"]) == 12

    # Fetch product to verify
    get_resp = client.get(f"/api/products/{prod['id']}")
    assert get_resp.json()["barcode"] == data["barcode"]

def test_existing_barcode_not_overwritten():
    prod = create_test_product(sku_prefix="NOOVERWRITE")
    gen1 = client.post(f"/api/products/{prod['id']}/barcode/generate").json()
    bc1 = gen1["barcode"]
    assert gen1["generated"] == True

    # Second generate attempt
    gen2 = client.post(f"/api/products/{prod['id']}/barcode/generate").json()
    assert gen2["generated"] == False
    assert gen2["barcode"] == bc1

def test_lookup_by_barcode():
    prod = create_test_product(sku_prefix="LOOKUP")
    gen = client.post(f"/api/products/{prod['id']}/barcode/generate").json()
    bc = gen["barcode"]

    lookup_resp = client.get(f"/api/products/by-barcode/{bc}")
    assert lookup_resp.status_code == 200
    assert lookup_resp.json()["id"] == prod["id"]

def test_unknown_barcode_returns_404():
    res = client.get("/api/products/by-barcode/999999999999")
    assert res.status_code == 404
    assert "не найден" in res.json()["detail"]

def test_bulk_generate_missing_only():
    p1 = create_test_product(sku_prefix="BULK1")
    p2 = create_test_product(sku_prefix="BULK2")

    # Bulk generate
    res1 = client.post("/api/products/barcodes/generate-missing").json()
    assert res1["generated"] >= 2

    # Verify both got barcodes
    prod1 = client.get(f"/api/products/{p1['id']}").json()
    prod2 = client.get(f"/api/products/{p2['id']}").json()
    assert prod1["barcode"] is not None
    assert prod2["barcode"] is not None

    # Second bulk generate should yield zero new generations
    res2 = client.post("/api/products/barcodes/generate-missing").json()
    assert res2["generated"] == 0

def test_barcode_uniqueness():
    p1 = create_test_product(sku_prefix="UNIQ1")
    gen1 = client.post(f"/api/products/{p1['id']}/barcode/generate").json()["barcode"]

    # Try creating a product with duplicate barcode
    sku2 = f"UNIQ2-{uuid.uuid4().hex[:8]}"
    res = client.post("/api/products/", json={
        "sku": sku2,
        "barcode": gen1,
        "title": "Dup Barcode Prod",
        "sale_price": 100
    })
    assert res.status_code in [400, 409, 500]  # Duplicate constraint error
