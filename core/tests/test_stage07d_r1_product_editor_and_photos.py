import pytest
import io
import uuid
import json
from fastapi.testclient import TestClient
from app.main import app
from app import models
from app.database import SessionLocal

client = TestClient(app)

def test_stage07d_editor_meta():
    """Verify GET /api/products/editor-meta returns categories, conditions, statuses, locations."""
    resp = client.get("/api/products/editor-meta")
    assert resp.status_code == 200
    data = resp.json()
    assert "categories" in data
    assert "category_characteristics" in data
    assert "Ноутбуки" in data["categories"]
    assert "Принтеры и МФУ" in data["categories"]
    assert "Процессор" in data["category_characteristics"]["Ноутбуки"]
    assert "conditions" in data
    assert "statuses" in data
    assert "storage_locations" in data

def test_stage07d_manual_create_and_auto_sku():
    """TEST A: Create product manually with blank SKU -> auto-generated unique SKU."""
    payload = {
        "title": "Тестовый ноутбук для проверки авто-SKU",
        "category": "Ноутбуки",
        "brand": "Asus",
        "model": "ZenBook 14",
        "condition": "Отличное",
        "sale_price": 45000.0,
        "purchase_price": 32000.0,
        "quantity": 2,
        "storage_location": "store",
        "status": "in_stock",
        "description": "Ультрабук в идеальном состоянии.\nБез дефектов.",
        "characteristics": {
            "Процессор": "Intel Core i7-1165G7",
            "Оперативная память": "16 ГБ",
            "Диагональ экрана": "14\""
        }
    }
    resp = client.post("/api/products/", json=payload)
    assert resp.status_code == 200
    prod = resp.json()
    assert prod["id"] > 0
    assert prod["sku"] is not None
    assert prod["sku"].startswith("PRD-")
    assert prod["title"] == payload["title"]
    assert prod["quantity"] == 2

    # Verify details
    det_resp = client.get(f"/api/products/{prod['id']}/details")
    assert det_resp.status_code == 200
    det = det_resp.json()
    assert det["avito_characteristics"]["Процессор"] == "Intel Core i7-1165G7"
    assert det["avito_characteristics"]["Диагональ экрана"] == "14\""

def test_stage07d_edit_common_fields():
    """TEST B: Change common fields through PUT /api/products/{id}."""
    # 1. Create product
    payload = {
        "title": "Начальный монитор",
        "sale_price": 5000.0,
        "purchase_price": 3000.0,
        "quantity": 1,
        "storage_location": "store",
        "status": "draft",
        "condition": "Б/у",
        "description": "Старое описание"
    }
    create_resp = client.post("/api/products/", json=payload)
    assert create_resp.status_code == 200
    pid = create_resp.json()["id"]

    # 2. Update all common fields
    update_payload = {
        "title": "Обновленный монитор Dell 27 4K",
        "category": "Мониторы",
        "brand": "Dell",
        "model": "U2720Q",
        "sale_price": 27000.0,
        "purchase_price": 19000.0,
        "quantity": 3,
        "storage_location": "workshop",
        "status": "in_stock",
        "condition": "Отличное",
        "description": "Профессиональный монитор 4K.\nIPS матрица, USB-C."
    }
    put_resp = client.put(f"/api/products/{pid}", json=update_payload)
    assert put_resp.status_code == 200
    updated = put_resp.json()
    assert updated["title"] == update_payload["title"]
    assert updated["sale_price"] == 27000.0
    assert updated["purchase_price"] == 19000.0
    assert updated["quantity"] == 3
    assert updated["storage_location"] == "workshop"
    assert updated["status"] == "in_stock"
    assert updated["description"] == update_payload["description"]

def test_stage07d_category_characteristics_laptop_and_printer():
    """TEST C & D: Edit laptop and printer characteristics and verify round-trip."""
    # 1. Laptop characteristics
    laptop_payload = {
        "title": "Lenovo ThinkPad P1",
        "category": "Ноутбуки",
        "sale_price": 85000.0,
        "characteristics": {
            "Процессор": "Intel Core i7-10750H",
            "Оперативная память": "32 ГБ",
            "Объем накопителя": "1000 ГБ",
            "Тип накопителя": "SSD",
            "Видеокарта": "NVIDIA Quadro T1000",
            "Диагональ экрана": "15.6\"",
            "Разрешение экрана": "3840x2160 4K OLED",
            "Операционная система": "Windows 11 Pro"
        }
    }
    lap_res = client.post("/api/products/", json=laptop_payload)
    assert lap_res.status_code == 200
    lap_id = lap_res.json()["id"]

    lap_det = client.get(f"/api/products/{lap_id}/details").json()
    for k, v in laptop_payload["characteristics"].items():
        assert lap_det["avito_characteristics"].get(k) == v

    # 2. Printer characteristics
    printer_payload = {
        "title": "МФУ Canon imageRUNNER 2206",
        "category": "Принтеры и МФУ",
        "sale_price": 38000.0,
        "characteristics": {
            "Тип устройства": "МФУ",
            "Технология печати": "Лазерная",
            "Цветность печати": "Черно-белая",
            "Максимальный формат": "A3",
            "Двусторонняя печать": "Да",
            "Wi-Fi": "Нет"
        }
    }
    prn_res = client.post("/api/products/", json=printer_payload)
    assert prn_res.status_code == 200
    prn_id = prn_res.json()["id"]

    prn_det = client.get(f"/api/products/{prn_id}/details").json()
    for k, v in printer_payload["characteristics"].items():
        assert prn_det["avito_characteristics"].get(k) == v

def test_stage07d_unknown_characteristics_safety():
    """TEST E: Existing extra characteristic is not silently destroyed."""
    payload = {
        "title": "Системный блок с редкими опциями",
        "category": "Системные блоки",
        "sale_price": 55000.0,
        "characteristics": {
            "Процессор": "AMD Ryzen 7 5700X",
            "Оперативная память": "32 ГБ",
            "Особая подсветка ARGB": "Адресная Aura Sync",
            "Кастомное СВО": "360мм водоблок"
        }
    }
    res = client.post("/api/products/", json=payload)
    assert res.status_code == 200
    pid = res.json()["id"]

    # Now update via PUT modifying processor, while keeping custom keys
    update_payload = {
        "title": "Системный блок с редкими опциями",
        "category": "Системные блоки",
        "sale_price": 57000.0,
        "characteristics": {
            "Процессор": "AMD Ryzen 7 5800X3D",
            "Оперативная память": "32 ГБ",
            "Особая подсветка ARGB": "Адресная Aura Sync",
            "Кастомное СВО": "360мм водоблок"
        }
    }
    put_res = client.put(f"/api/products/{pid}", json=update_payload)
    assert put_res.status_code == 200

    det = client.get(f"/api/products/{pid}/details").json()
    assert det["avito_characteristics"]["Процессор"] == "AMD Ryzen 7 5800X3D"
    assert det["avito_characteristics"]["Особая подсветка ARGB"] == "Адресная Aura Sync"
    assert det["avito_characteristics"]["Кастомное СВО"] == "360мм водоблок"

def test_stage07d_photo_lifecycle_upload_reorder_main_delete():
    """TEST I, J, K, L: Photo upload (batch & single), reorder, set main, and delete."""
    # 1. Create product
    prod_res = client.post("/api/products/", json={"title": "Товар для теста фото", "sale_price": 1000.0})
    assert prod_res.status_code == 200
    pid = prod_res.json()["id"]

    # 2. Upload two photos
    fake_img1 = b"\xFF\xD8\xFF\xE0" + b"FAKE_JPEG_PHOTO_1"
    fake_img2 = b"\xFF\xD8\xFF\xE0" + b"FAKE_JPEG_PHOTO_2"

    up1 = client.post(
        f"/api/products/{pid}/photos",
        files={"file": ("photo1.jpg", io.BytesIO(fake_img1), "image/jpeg")}
    )
    assert up1.status_code == 200
    photo1 = up1.json()
    assert photo1["media_url"].startswith(f"/media/product_photos/{pid}/")
    p1_id = photo1["id"]

    up2 = client.post(
        f"/api/products/{pid}/photos",
        files={"file": ("photo2.jpg", io.BytesIO(fake_img2), "image/jpeg")}
    )
    assert up2.status_code == 200
    photo2 = up2.json()
    p2_id = photo2["id"]

    # Verify both photos present in details
    det = client.get(f"/api/products/{pid}/details").json()
    assert len(det["photos"]) == 2
    assert det["photos"][0]["id"] == p1_id
    assert det["photos"][1]["id"] == p2_id

    # 3. TEST K: Set second photo as main
    main_res = client.post(f"/api/products/{pid}/photos/{p2_id}/make-main")
    assert main_res.status_code == 200
    photos_after_main = main_res.json()
    assert photos_after_main[0]["id"] == p2_id
    assert photos_after_main[0]["sort_order"] == 0

    det_after_main = client.get(f"/api/products/{pid}/details").json()
    assert det_after_main["photos"][0]["id"] == p2_id

    # 4. TEST J: Reorder photos back
    reorder_res = client.post(
        f"/api/products/{pid}/photos/reorder",
        json={"photo_ids": [p1_id, p2_id]}
    )
    assert reorder_res.status_code == 200
    photos_reordered = reorder_res.json()
    assert photos_reordered[0]["id"] == p1_id
    assert photos_reordered[0]["sort_order"] == 0
    assert photos_reordered[1]["id"] == p2_id
    assert photos_reordered[1]["sort_order"] == 1

    # 5. TEST L: Delete one photo
    del_res = client.delete(f"/api/products/{pid}/photos/{p1_id}")
    assert del_res.status_code == 200

    det_after_del = client.get(f"/api/products/{pid}/details").json()
    assert len(det_after_del["photos"]) == 1
    assert det_after_del["photos"][0]["id"] == p2_id
    assert det_after_del["photos"][0]["sort_order"] == 0

def test_stage07d_validation_and_duplicate_sku():
    """TEST O & P: Validation on empty title, negative price/quantity, bad file, duplicate SKU."""
    # 1. Empty title
    r_title = client.post("/api/products/", json={"title": "  ", "sale_price": 100})
    assert r_title.status_code == 400

    # 2. Negative price
    r_price = client.post("/api/products/", json={"title": "Товар", "sale_price": -50})
    assert r_price.status_code == 400

    # 3. Negative quantity
    r_qty = client.post("/api/products/", json={"title": "Товар", "sale_price": 100, "quantity": -5})
    assert r_qty.status_code == 400

    # 4. Duplicate SKU on create
    fixed_sku = f"SKU-DUP-{uuid.uuid4().hex[:6]}"
    r1 = client.post("/api/products/", json={"title": "Товар 1", "sku": fixed_sku, "sale_price": 100})
    assert r1.status_code == 200

    r2 = client.post("/api/products/", json={"title": "Товар 2", "sku": fixed_sku, "sale_price": 200})
    assert r2.status_code == 409

    # 5. Bad file upload (text instead of image)
    pid = r1.json()["id"]
    bad_file = client.post(
        f"/api/products/{pid}/photos",
        files={"file": ("malicious.exe", b"NOT_AN_IMAGE", "application/octet-stream")}
    )
    assert bad_file.status_code == 400
