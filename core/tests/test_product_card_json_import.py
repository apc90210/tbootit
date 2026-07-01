import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)


def make_card(sku=None):
    if sku is None:
        sku = f"TEST-IMPORT-{uuid.uuid4().hex[:8]}"
    return {
        "source": "chatgpt",
        "schema_version": "1.0",
        "operation": "create_or_update",
        "product": {
            "sku": sku,
            "title": "Ноутбук Lenovo ThinkPad T480",
            "category_path": ["Ноутбуки"],
            "brand": "Lenovo",
            "model": "ThinkPad T480",
            "condition": "БУ, рабочий",
            "description": "Тест импорта.",
            "purchase_price": 12000,
            "sale_price": 21000,
            "quantity": 2,
            "storage_location": "Склад 1"
        },
        "avito": {
            "title": "Ноутбук Lenovo ThinkPad T480",
            "description": "Описание для Авито",
            "goods_type": "Ноутбук",
            "condition": "Б/у",
            "price": 21000,
            "seller_type": "company",
            "contact_name": "Техноребут",
            "phone": "+7 999 000-00-11",
            "parameters": {
                "Производитель": "Lenovo",
                "Модель": "ThinkPad T480",
                "Процессор": "Intel Core i5",
                "RAM": "8 ГБ"
            }
        },
        "site": {
            "title": "Ноутбук Lenovo ThinkPad T480",
            "description": "Описание для сайта",
            "publish_ready": True
        }
    }


def test_import_creates_product():
    card = make_card()
    r = client.post("/api/product-cards/import-json", json=card)
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "imported"
    assert d["operation"] == "created"
    assert d["product_id"] > 0


def test_import_updates_existing_product_not_duplicate():
    sku = f"TEST-UPDATE-{uuid.uuid4().hex[:8]}"
    card = make_card(sku=sku)
    r1 = client.post("/api/product-cards/import-json", json=card)
    assert r1.status_code == 200
    id1 = r1.json()["product_id"]

    # Second import with same SKU → update, not create
    card2 = make_card(sku=sku)
    card2["product"]["sale_price"] = 22000
    r2 = client.post("/api/product-cards/import-json", json=card2)
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["operation"] == "updated"
    assert d2["product_id"] == id1  # same product, not a duplicate


def test_import_sets_avito_fields():
    card = make_card()
    r = client.post("/api/product-cards/import-json", json=card)
    product_id = r.json()["product_id"]

    det = client.get(f"/api/products/{product_id}/details")
    assert det.status_code == 200
    d = det.json()
    assert d["avito_title"] == card["avito"]["title"]
    assert d["avito_goods_type"] == "Ноутбук"
    assert d["avito_params_json"] is not None
    assert "Lenovo" in d["avito_params_json"]


def test_import_sets_site_fields():
    card = make_card()
    r = client.post("/api/product-cards/import-json", json=card)
    product_id = r.json()["product_id"]

    det = client.get(f"/api/products/{product_id}/details")
    d = det.json()
    assert d["site_title"] == card["site"]["title"]
    assert d["is_published_site"] == 1  # publish_ready was True


def test_import_stores_source_json():
    card = make_card()
    r = client.post("/api/product-cards/import-json", json=card)
    product_id = r.json()["product_id"]

    det = client.get(f"/api/products/{product_id}/details")
    d = det.json()
    assert d["source_type"] == "chatgpt"
    assert d["source_json"] is not None


def test_import_logged_in_imports_list():
    card = make_card()
    client.post("/api/product-cards/import-json", json=card)
    imports = client.get("/api/product-cards/imports")
    assert imports.status_code == 200
    data = imports.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["validation_status"] in ("success", "invalid")
