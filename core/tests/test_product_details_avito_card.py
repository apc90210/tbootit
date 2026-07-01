from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def setup_product():
    """Create a product via JSON import."""
    payload = {
        "source": "test",
        "schema_version": "1.0",
        "operation": "create_or_update",
        "product": {
            "sku": "TEST-DETAILS-001",
            "title": "Тестовый товар для деталей",
            "category_path": ["Тест"],
            "brand": "TestBrand",
            "sale_price": 10000,
            "purchase_price": 7000,
            "quantity": 3,
            "storage_location": "Тест-склад"
        },
        "avito": {
            "title": "Тест Авито заголовок",
            "description": "Тест Авито описание",
            "goods_type": "Тест",
            "condition": "Б/у",
            "price": 10000,
            "contact_name": "Тест",
            "phone": "+7 999 000-00-99",
            "parameters": {"Параметр1": "Значение1"}
        },
        "site": {
            "title": "Тест сайт заголовок",
            "description": "Тест сайт описание",
            "publish_ready": True
        }
    }
    r = client.post("/api/product-cards/import-json", json=payload)
    return r.json()["product_id"]

def test_details_contains_product_fields():
    pid = setup_product()
    r = client.get(f"/api/products/{pid}/details")
    assert r.status_code == 200
    d = r.json()
    assert d["sku"] == "TEST-DETAILS-001"
    assert d["brand"] == "TestBrand"

def test_details_contains_avito_fields():
    pid = setup_product()
    r = client.get(f"/api/products/{pid}/details")
    d = r.json()
    assert d["avito_title"] == "Тест Авито заголовок"
    assert d["avito_goods_type"] == "Тест"
    assert d["avito_params_json"] is not None

def test_details_contains_site_fields():
    pid = setup_product()
    r = client.get(f"/api/products/{pid}/details")
    d = r.json()
    assert d["site_title"] == "Тест сайт заголовок"
    assert d["is_published_site"] == 1

def test_details_computed_margin():
    pid = setup_product()
    r = client.get(f"/api/products/{pid}/details")
    d = r.json()
    # 10000 - 7000 = 3000
    assert d["margin"] == 3000.0
    assert d["available_quantity"] == 3

def test_details_events_list():
    pid = setup_product()
    r = client.get(f"/api/products/{pid}/details")
    d = r.json()
    assert "events" in d
    assert isinstance(d["events"], list)
    assert len(d["events"]) >= 1

def test_details_stock_movements_list():
    pid = setup_product()
    r = client.get(f"/api/products/{pid}/details")
    d = r.json()
    assert "stock_movements" in d
    assert isinstance(d["stock_movements"], list)
