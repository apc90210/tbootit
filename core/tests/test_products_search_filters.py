from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_product(sku, title, status="in_stock", brand="BrandX", storage="Склад 1", price=10000.0):
    payload = {
        "source": "test", "schema_version": "1.0", "operation": "create_or_update",
        "product": {"sku": sku, "title": title, "brand": brand,
                    "storage_location": storage, "sale_price": price, "quantity": 1}
    }
    r = client.post("/api/product-cards/import-json", json=payload)
    pid = r.json()["product_id"]
    # set status via status endpoint
    client.patch(f"/api/products/{pid}/status", json={"status": status})
    return pid

def test_search_q():
    create_product("SRH-001", "Тест Поиск Ноутбук")
    r = client.get("/api/products/", params={"q": "Ноутбук"})
    assert r.status_code == 200
    results = r.json()
    assert any("Ноутбук" in p["title"] for p in results)

def test_filter_status():
    pid = create_product("SRH-002", "Тест статус", status="reserved")
    r = client.get("/api/products/", params={"status": "reserved"})
    ids = [p["id"] for p in r.json()]
    assert pid in ids

def test_filter_brand():
    create_product("SRH-003", "Тест бренд Dell", brand="Dell")
    r = client.get("/api/products/", params={"brand": "Dell"})
    assert r.status_code == 200
    brands = [p.get("brand") for p in r.json()]
    assert "Dell" in brands

def test_filter_storage_location():
    create_product("SRH-004", "Тест Витрина", storage="Витрина")
    r = client.get("/api/products/", params={"storage_location": "Витрина"})
    locs = [p.get("storage_location") for p in r.json()]
    assert "Витрина" in locs

def test_limit_offset():
    r_all = client.get("/api/products/", params={"limit": 1000})
    total = len(r_all.json())
    r_limit = client.get("/api/products/", params={"limit": 2, "offset": 0})
    assert len(r_limit.json()) <= 2

def test_search_q_no_results():
    r = client.get("/api/products/", params={"q": "ZZZNOMATCH999"})
    assert r.status_code == 200
    assert r.json() == []
