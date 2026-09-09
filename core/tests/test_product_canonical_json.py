import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app import models
from app.services.product_json_service import (
    CANONICAL_FORMAT,
    CANONICAL_VERSION,
    generate_ai_prompt,
    normalize_payload,
    import_canonical_products,
    export_canonical_products
)

client = TestClient(app)

class TestProductCanonicalJson:

    def test_test_b_canonical_schema_single_product(self):
        """Test B: Canonical versioned JSON schema accepts one valid product."""
        payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "title": "Ноутбук Lenovo ThinkPad T480",
                    "category": "Ноутбуки",
                    "brand": "Lenovo",
                    "model": "ThinkPad T480",
                    "price": 25000.0,
                    "purchase_price": 15000.0,
                    "condition": "Б/у",
                    "status": "in_stock",
                    "quantity": 1,
                    "description": "Рабочая корпоративная машина.",
                    "storage_location": "Склад 1",
                    "characteristics": {
                        "Процессор": "Intel Core i5-8250U",
                        "Оперативная память": "16 ГБ"
                    },
                    "photos": []
                }
            ]
        }
        res = client.post("/api/products/json/import", json=payload)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["success"] is True
        assert data["created_count"] == 1
        assert data["updated_count"] == 0
        assert data["skipped_count"] == 0
        assert len(data["imported_product_ids"]) == 1

        # Check DB
        db = SessionLocal()
        p = db.query(models.Product).filter(models.Product.id == data["imported_product_ids"][0]).first()
        assert p is not None
        assert p.title == "Ноутбук Lenovo ThinkPad T480"
        assert p.brand == "Lenovo"
        assert p.sale_price == 25000.0
        assert p.purchase_price == 15000.0
        assert p.sku.startswith("PRD-")
        db.close()

    def test_test_c_schema_accepts_multiple_products(self):
        """Test C: Schema accepts multiple valid products in a batch."""
        payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "title": "Монитор Dell 24",
                    "category": "Мониторы",
                    "price": 8000.0
                },
                {
                    "title": "Клавиатура Logitech",
                    "category": "Комплектующие",
                    "price": 1500.0
                },
                {
                    "title": "Принтер HP 1020",
                    "category": "Принтеры и МФУ",
                    "price": 6000.0
                }
            ]
        }
        res = client.post("/api/products/json/import", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["created_count"] == 3
        assert data["skipped_count"] == 0
        assert len(data["imported_product_ids"]) == 3

    def test_test_d_invalid_json_is_rejected_safely(self):
        """Test D: Invalid JSON syntax or wrong top-level envelope is rejected safely."""
        # Top-level wrong format name
        payload = {
            "format": "unknown-format",
            "version": 1,
            "products": [{"title": "Test"}]
        }
        res = client.post("/api/products/json/import", json=payload)
        assert res.status_code == 400
        assert "Не распознан формат JSON" in res.json()["detail"]["errors"][0]

        # Version mismatch
        payload_v2 = {
            "format": "technoreboot-products",
            "version": 99,
            "products": [{"title": "Test"}]
        }
        res_v2 = client.post("/api/products/json/import", json=payload_v2)
        assert res_v2.status_code == 400
        assert "Неподдерживаемая версия формата: 99" in res_v2.json()["detail"]["errors"][0]

        # Empty products array
        payload_empty = {
            "format": "technoreboot-products",
            "version": 1,
            "products": []
        }
        res_empty = client.post("/api/products/json/import", json=payload_empty)
        assert res_empty.status_code == 400
        assert "Массив 'products' пуст" in res_empty.json()["detail"]["errors"][0]

    def test_test_e_invalid_product_record_reports_exact_error(self):
        """Test E: Invalid product record reports exact product-level error and skips cleanly."""
        payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "title": "Валидный товар 1",
                    "price": 1000.0
                },
                {
                    "title": "",  # Missing title
                    "price": 2000.0
                },
                {
                    "title": "Товар с неверной ценой",
                    "price": "not_a_number"
                },
                {
                    "title": "Товар с отрицательной ценой",
                    "price": -500.0
                },
                {
                    "title": "Валидный товар 2",
                    "price": 3000.0
                }
            ]
        }
        res = client.post("/api/products/json/import", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["created_count"] == 2
        assert data["skipped_count"] == 3
        assert len(data["errors"]) == 3
        assert any("Товар #2: отсутствует обязательное название" in e for e in data["errors"])
        assert any("Товар #3: поле 'price' должно быть числом" in e for e in data["errors"])
        assert any("Товар #4: цена 'price' не может быть отрицательной" in e for e in data["errors"])

    def test_test_f_laptop_characteristics_import_correctly(self):
        """Test F: Category-specific laptop characteristics import into dynamic schema and attributes."""
        payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "title": "Ноутбук Dell XPS 13",
                    "category": "Ноутбуки",
                    "brand": "Dell",
                    "model": "XPS 13 9300",
                    "price": 55000.0,
                    "characteristics": {
                        "Процессор": "Intel Core i7-1065G7",
                        "Оперативная память": "16 ГБ",
                        "Объем накопителя": "512 ГБ SSD",
                        "Диагональ экрана": "13.4\"",
                        "Разрешение экрана": "1920x1200"
                    }
                }
            ]
        }
        res = client.post("/api/products/json/import", json=payload)
        assert res.status_code == 200
        prod_id = res.json()["imported_product_ids"][0]

        db = SessionLocal()
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        assert p.category.name == "Ноутбуки"
        assert p.avito_category is not None
        assert p.avito_category.name == "Ноутбуки"

        # Check ProductAvitoAttributeValue rows
        attr_vals = {row.definition.name: row.value for row in p.avito_attribute_values}
        assert attr_vals["Процессор"] == "Intel Core i7-1065G7"
        assert attr_vals["Оперативная память"] == "16 ГБ"
        assert attr_vals["Объем накопителя"] == "512 ГБ SSD"
        db.close()

    def test_test_g_printer_mfp_characteristics_import_correctly(self):
        """Test G: Category-specific printer/MFP characteristics import correctly."""
        payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "title": "МФУ Canon i-SENSYS MF3010",
                    "category": "Принтеры и МФУ",
                    "brand": "Canon",
                    "model": "i-SENSYS MF3010",
                    "price": 14000.0,
                    "characteristics": {
                        "Тип устройства": "МФУ",
                        "Технология печати": "Лазерная",
                        "Цветность печати": "Черно-белая",
                        "Интерфейсы": "USB"
                    }
                }
            ]
        }
        res = client.post("/api/products/json/import", json=payload)
        assert res.status_code == 200
        prod_id = res.json()["imported_product_ids"][0]

        db = SessionLocal()
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        attr_vals = {row.definition.name: row.value for row in p.avito_attribute_values}
        assert attr_vals["Тип устройства"] == "МФУ"
        assert attr_vals["Технология печати"] == "Лазерная"
        assert attr_vals["Цветность печати"] == "Черно-белая"
        db.close()

    def test_test_h_pc_or_component_category_imports_correctly(self):
        """Test H: System unit / PC category imports correctly with hardware specs."""
        payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "title": "Системный блок Core i7 / RTX 3060",
                    "category": "Системные блоки",
                    "brand": "Custom",
                    "price": 60000.0,
                    "characteristics": {
                        "Процессор": "Intel Core i7-10700",
                        "Оперативная память": "32 ГБ DDR4",
                        "Видеокарта": "NVIDIA GeForce RTX 3060 12GB",
                        "Блок питания": "700W"
                    }
                }
            ]
        }
        res = client.post("/api/products/json/import", json=payload)
        assert res.status_code == 200
        prod_id = res.json()["imported_product_ids"][0]

        db = SessionLocal()
        p = db.query(models.Product).filter(models.Product.id == prod_id).first()
        attr_vals = {row.definition.name: row.value for row in p.avito_attribute_values}
        assert attr_vals["Процессор"] == "Intel Core i7-10700"
        assert attr_vals["Видеокарта"] == "NVIDIA GeForce RTX 3060 12GB"
        db.close()

    def test_test_i_photos_are_optional(self):
        """Test I: Photos are completely optional (omitted or empty list works identically)."""
        payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "title": "Товар без ключа photos",
                    "price": 100.0
                },
                {
                    "title": "Товар с пустым массивом photos",
                    "price": 200.0,
                    "photos": []
                }
            ]
        }
        res = client.post("/api/products/json/import", json=payload)
        assert res.status_code == 200
        assert res.json()["created_count"] == 2

    def test_test_k_ai_prompt_example_validates_against_schema(self):
        """Test K: AI prompt generated by service produces valid example JSON accepted by importer."""
        prompt_text = generate_ai_prompt()
        assert "technoreboot-products" in prompt_text
        assert "version\": 1" in prompt_text

        # Extract Example 1 (Laptop) from prompt
        ex1_start = prompt_text.find('### ПРИМЕР 1: ОДИН ТОВАР')
        ex2_start = prompt_text.find('### ПРИМЕР 2: НЕСКОЛЬКО ТОВАРОВ')
        ex1_json_str = prompt_text[prompt_text.find('{', ex1_start):ex2_start].strip()
        ex1_obj = json.loads(ex1_json_str)

        res1 = client.post("/api/products/json/import", json=ex1_obj)
        assert res1.status_code == 200
        assert res1.json()["created_count"] == 1

        # Extract Example 2 (Multi product) from prompt
        ex2_json_str = prompt_text[prompt_text.find('{', ex2_start):].strip()
        ex2_obj = json.loads(ex2_json_str)

        res2 = client.post("/api/products/json/import", json=ex2_obj)
        assert res2.status_code == 200
        assert res2.json()["created_count"] == 2

    def test_test_l_m_n_o_p_export_and_roundtrip(self):
        """
        Tests L, M, N, O, P:
        - Test L: One product exports correctly.
        - Test M: Multiple products export correctly.
        - Test N: Exported JSON re-imports successfully.
        - Test O: Common fields survive round-trip.
        - Test P: Category-specific characteristics survive round-trip.
        """
        # 1. Create two rich products
        p1_payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "title": "Ультрабук ASUS ZenBook 14",
                    "category": "Ноутбуки",
                    "brand": "ASUS",
                    "model": "ZenBook UX425",
                    "price": 49000.0,
                    "purchase_price": 32000.0,
                    "condition": "Отличное",
                    "status": "in_stock",
                    "quantity": 2,
                    "description": "Тонкий металлический ультрабук в идеальном состоянии.",
                    "storage_location": "Витрина 2",
                    "barcode": "460000000001",
                    "characteristics": {
                        "Процессор": "Intel Core i5-1135G7",
                        "Оперативная память": "8 ГБ",
                        "Объем накопителя": "512 ГБ SSD"
                    }
                },
                {
                    "title": "Принтер Kyocera FS-1040",
                    "category": "Принтеры и МФУ",
                    "brand": "Kyocera",
                    "model": "FS-1040",
                    "price": 4500.0,
                    "purchase_price": 2500.0,
                    "condition": "Б/у",
                    "status": "in_stock",
                    "quantity": 1,
                    "description": "Экономичный офисный принтер с дешевой заправкой.",
                    "storage_location": "Склад 2",
                    "characteristics": {
                        "Тип устройства": "Принтер",
                        "Технология печати": "Лазерная",
                        "Цветность печати": "Черно-белая"
                    }
                }
            ]
        }
        res_init = client.post("/api/products/json/import", json=p1_payload)
        assert res_init.status_code == 200
        p_ids = res_init.json()["imported_product_ids"]
        assert len(p_ids) == 2

        # 2. Test L: Export single product
        res_single_export = client.get(f"/api/products/json/export?ids={p_ids[0]}")
        assert res_single_export.status_code == 200
        single_data = res_single_export.json()
        assert single_data["format"] == "technoreboot-products"
        assert single_data["version"] == 1
        assert len(single_data["products"]) == 1
        assert single_data["products"][0]["title"] == "Ультрабук ASUS ZenBook 14"
        assert single_data["products"][0]["id"] == p_ids[0]

        # 3. Test M: Export all products
        res_multi_export = client.get(f"/api/products/json/export?ids={p_ids[0]},{p_ids[1]}")
        assert res_multi_export.status_code == 200
        multi_data = res_multi_export.json()
        assert len(multi_data["products"]) == 2

        # 4. Modify price and characteristic on exported products and re-import (Test N, O, P)
        exported_products = multi_data["products"]
        # Update product 1 price and memory
        exported_products[0]["price"] = 52000.0
        exported_products[0]["characteristics"]["Оперативная память"] = "16 ГБ"
        # Update product 2 description
        exported_products[1]["description"] = "Обновленное описание принтера."

        reimport_payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": exported_products
        }
        res_reimport = client.post("/api/products/json/import", json=reimport_payload)
        assert res_reimport.status_code == 200
        reimport_res = res_reimport.json()
        assert reimport_res["updated_count"] == 2
        assert reimport_res["created_count"] == 0
        assert reimport_res["skipped_count"] == 0

        # Verify DB state after round-trip
        db = SessionLocal()
        p1 = db.query(models.Product).filter(models.Product.id == p_ids[0]).first()
        assert p1.sale_price == 52000.0
        assert p1.title == "Ультрабук ASUS ZenBook 14"
        assert p1.category.name == "Ноутбуки"
        assert p1.brand == "ASUS"
        assert p1.model == "ZenBook UX425"
        assert p1.purchase_price == 32000.0
        assert p1.barcode == "460000000001"
        assert p1.storage_location == "Витрина 2"
        # Check updated characteristics
        attr_vals_1 = {row.definition.name: row.value for row in p1.avito_attribute_values}
        assert attr_vals_1["Оперативная память"] == "16 ГБ"
        assert attr_vals_1["Процессор"] == "Intel Core i5-1135G7"

        p2 = db.query(models.Product).filter(models.Product.id == p_ids[1]).first()
        assert p2.description == "Обновленное описание принтера."
        attr_vals_2 = {row.definition.name: row.value for row in p2.avito_attribute_values}
        assert attr_vals_2["Технология печати"] == "Лазерная"
        db.close()

    def test_test_q_duplicate_update_policy(self):
        """
        Test Q: Duplicate / Update Policy:
        - If id provided and product exists -> UPDATE.
        - If id provided and product does not exist -> ERROR/SKIP.
        - If id NOT provided and sku exists in DB -> SKIP (prevents accidental overwrite).
        - If id NOT provided and sku is new or omitted -> CREATE.
        """
        # Step 1: Create a product with explicit SKU
        init_payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "sku": "UNIQUE-SKU-100",
                    "title": "Исходный товар",
                    "price": 1000.0
                }
            ]
        }
        res1 = client.post("/api/products/json/import", json=init_payload)
        assert res1.status_code == 200
        p_id = res1.json()["imported_product_ids"][0]

        # Step 2: Attempt to import another product with same SKU but NO id -> Must SKIP!
        dup_sku_payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "sku": "UNIQUE-SKU-100",
                    "title": "Попытка перезаписать без ID",
                    "price": 9999.0
                }
            ]
        }
        res2 = client.post("/api/products/json/import", json=dup_sku_payload)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["created_count"] == 0
        assert data2["updated_count"] == 0
        assert data2["skipped_count"] == 1
        assert "уже существует (укажите 'id' для обновления)" in data2["errors"][0]

        # Verify DB product was NOT overwritten
        db = SessionLocal()
        p_check = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert p_check.title == "Исходный товар"
        assert p_check.sale_price == 1000.0
        db.close()

        # Step 3: Attempt to update with non-existent ID -> Must SKIP with error
        bad_id_payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "id": 999999,
                    "title": "Несуществующий товар",
                    "price": 500.0
                }
            ]
        }
        res3 = client.post("/api/products/json/import", json=bad_id_payload)
        assert res3.status_code == 200
        assert res3.json()["skipped_count"] == 1
        assert "Товар с ID 999999 не найден в базе данных" in res3.json()["errors"][0]

        # Step 4: Legitimate update using existing ID -> Must UPDATE
        legit_update_payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "id": p_id,
                    "title": "Обновленный товар по ID",
                    "price": 1500.0
                }
            ]
        }
        res4 = client.post("/api/products/json/import", json=legit_update_payload)
        assert res4.status_code == 200
        assert res4.json()["updated_count"] == 1
        assert res4.json()["created_count"] == 0
        assert res4.json()["skipped_count"] == 0

        db = SessionLocal()
        p_updated = db.query(models.Product).filter(models.Product.id == p_id).first()
        assert p_updated.title == "Обновленный товар по ID"
        assert p_updated.sale_price == 1500.0
        db.close()

    def test_legacy_format_backward_compatibility(self):
        """Test backward compatibility with legacy single-card ChatGPT payload."""
        legacy_payload = {
            "source": "chatgpt",
            "schema_version": "1.0",
            "operation": "create",
            "product": {
                "sku": "LEGACY-SKU-001",
                "title": "Старый формат товара",
                "category_path": ["Электроника", "Ноутбуки"],
                "brand": "Lenovo",
                "model": "ThinkPad",
                "sale_price": 20000.0,
                "condition": "Б/у"
            },
            "avito": {
                "parameters": {
                    "Процессор": "Intel Core i3"
                }
            }
        }
        res = client.post("/api/products/json/import", json=legacy_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["created_count"] == 1
        assert data["skipped_count"] == 0
        db = SessionLocal()
        p = db.query(models.Product).filter(models.Product.sku == "LEGACY-SKU-001").first()
        assert p is not None
        assert p.title == "Старый формат товара"
        assert p.category.name == "Ноутбуки"
        db.close()

    def test_selected_product_export_single_item(self):
        """TEST A: One selected product export -> exactly 1 item in canonical format."""
        # 1. Create a distinct test product
        payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "sku": "SELECT-001",
                    "title": "Ноутбук одиночного экспорта",
                    "category": "Ноутбуки",
                    "price": 33000.0,
                    "characteristics": {"Процессор": "Intel Core i5"}
                }
            ]
        }
        res_create = client.post("/api/products/json/import", json=payload)
        assert res_create.status_code == 200
        p_id = res_create.json()["imported_product_ids"][0]

        # 2. Export only this 1 ID via GET
        res_export = client.get(f"/api/products/json/export?ids={p_id}")
        assert res_export.status_code == 200
        export_data = res_export.json()

        assert export_data["format"] == "technoreboot-products"
        assert export_data["version"] == 1
        assert len(export_data["products"]) == 1
        assert export_data["products"][0]["id"] == p_id
        assert export_data["products"][0]["title"] == "Ноутбук одиночного экспорта"
        assert export_data["products"][0]["sku"] == "SELECT-001"
        assert export_data["products"][0]["characteristics"]["Процессор"] == "Intel Core i5"

    def test_selected_product_export_multiple_and_exclusion(self):
        """TEST B & C: Three selected products export -> exactly 3 items, unselected excluded."""
        # Create 4 products (3 to select, 1 to leave unselected)
        payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {"sku": "MULTI-A", "title": "Товар для выбора 1", "price": 1000.0},
                {"sku": "MULTI-B", "title": "Товар для выбора 2", "price": 2000.0},
                {"sku": "MULTI-C", "title": "Товар для выбора 3", "price": 3000.0},
                {"sku": "MULTI-D", "title": "НЕВЫБРАННЫЙ ТОВАР", "price": 9999.0}
            ]
        }
        res_create = client.post("/api/products/json/import", json=payload)
        assert res_create.status_code == 200
        p_ids = res_create.json()["imported_product_ids"]
        assert len(p_ids) == 4

        selected_ids = p_ids[:3]
        unselected_id = p_ids[3]

        # Export selected 3 products via GET ?ids=...
        res_export = client.get(f"/api/products/json/export?ids={selected_ids[0]},{selected_ids[1]},{selected_ids[2]}")
        assert res_export.status_code == 200
        data = res_export.json()

        assert data["format"] == "technoreboot-products"
        assert data["version"] == 1
        assert len(data["products"]) == 3

        exported_ids = [p["id"] for p in data["products"]]
        assert exported_ids == selected_ids
        # TEST C: Verify unselected product is strictly ABSENT
        assert unselected_id not in exported_ids
        assert all(p["sku"] != "MULTI-D" for p in data["products"])

    def test_selected_product_export_roundtrip(self):
        """TEST E, F, G, H: Selected export validates against importer and round-trip preserves all fields."""
        # Create product with rich characteristics
        payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "sku": "RT-SEL-01",
                    "title": "МФУ для раундтрипа",
                    "category": "Принтеры и МФУ",
                    "brand": "HP",
                    "model": "LaserJet Pro",
                    "price": 19500.0,
                    "purchase_price": 12000.0,
                    "condition": "Отличное",
                    "description": "Тестовое подробное описание МФУ.",
                    "storage_location": "Склад А",
                    "barcode": "469999999999",
                    "characteristics": {
                        "Тип устройства": "МФУ",
                        "Технология печати": "Лазерная",
                        "Цветность печати": "Черно-белая"
                    }
                }
            ]
        }
        res_create = client.post("/api/products/json/import", json=payload)
        assert res_create.status_code == 200
        prod_id = res_create.json()["imported_product_ids"][0]

        # Export selected product
        res_export = client.get(f"/api/products/json/export?ids={prod_id}")
        assert res_export.status_code == 200
        exported = res_export.json()

        # Modify values on the exported item
        exported["products"][0]["price"] = 21000.0
        exported["products"][0]["characteristics"]["Тип устройства"] = "МФУ (Обновлено)"

        # TEST F: Validate and re-import via importer
        res_reimport = client.post("/api/products/json/import", json=exported)
        assert res_reimport.status_code == 200
        reimport_res = res_reimport.json()
        assert reimport_res["updated_count"] == 1
        assert reimport_res["created_count"] == 0

        # TEST G & H: Verify in DB that common fields and characteristics survived round-trip
        db = SessionLocal()
        p_check = db.query(models.Product).filter(models.Product.id == prod_id).first()
        assert p_check.sale_price == 21000.0
        assert p_check.purchase_price == 12000.0
        assert p_check.title == "МФУ для раундтрипа"
        assert p_check.brand == "HP"
        assert p_check.model == "LaserJet Pro"
        assert p_check.storage_location == "Склад А"
        assert p_check.barcode == "469999999999"

        attr_vals = {row.definition.name: row.value for row in p_check.avito_attribute_values}
        assert attr_vals["Тип устройства"] == "МФУ (Обновлено)"
        assert attr_vals["Технология печати"] == "Лазерная"
        db.close()

    def test_selected_export_unknown_id_handled_safely(self):
        """TEST J: Unknown product IDs handled safely without crashing (returns empty list)."""
        res = client.get("/api/products/json/export?ids=999999,888888")
        assert res.status_code == 200
        data = res.json()
        assert data["format"] == "technoreboot-products"
        assert data["version"] == 1
        assert len(data["products"]) == 0

    def test_selected_export_post_endpoint(self):
        """TEST POST endpoint: POST /api/products/json/export accepts JSON body {"ids": [..]}."""
        # Create 2 products
        payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {"sku": "POST-SEL-1", "title": "Товар для POST 1", "price": 500.0},
                {"sku": "POST-SEL-2", "title": "Товар для POST 2", "price": 750.0}
            ]
        }
        res_create = client.post("/api/products/json/import", json=payload)
        p_ids = res_create.json()["imported_product_ids"]

        # Call POST /api/products/json/export
        res_post = client.post("/api/products/json/export", json={"ids": p_ids})
        assert res_post.status_code == 200
        data = res_post.json()
        assert len(data["products"]) == 2
        assert [p["id"] for p in data["products"]] == p_ids

    def test_owner_exact_payload_imports_two_products_and_enforces_invariant(self):
        """Stage 07C-R1-R2: Exact Owner payload creates 2 products, returns summary & results, preserves fields."""
        owner_payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {
                    "title": "Монитор Dell P2419H 24\" Full HD",
                    "category": "Мониторы",
                    "brand": "Dell",
                    "model": "P2419H",
                    "price": 8500.0,
                    "purchase_price": 5000.0,
                    "condition": "Б/у",
                    "status": "in_stock",
                    "quantity": 1,
                    "description": "Монитор Dell P2419H в рабочем состоянии. Экран без трещин, изображение стабильное. Подходит для офиса, дома и работы с документами. В комплекте кабель питания.",
                    "storage_location": "Витрина",
                    "barcode": "",
                    "characteristics": {
                        "Диагональ": "24\"",
                        "Разрешение": "1920x1080",
                        "Тип матрицы": "IPS",
                        "Частота обновления": "60 Гц",
                        "Разъемы": "HDMI, DisplayPort, VGA, USB"
                    },
                    "photos": []
                },
                {
                    "title": "Ноутбук HP ProBook 450 G6 15.6\"",
                    "category": "Ноутбуки",
                    "brand": "HP",
                    "model": "ProBook 450 G6",
                    "price": 24500.0,
                    "purchase_price": 15500.0,
                    "condition": "Б/у",
                    "status": "in_stock",
                    "quantity": 1,
                    "description": "Рабочий ноутбук HP ProBook 450 G6. Подходит для офисных задач, учебы, интернета и удаленной работы. Ноутбук проверен, основные функции работают исправно. Блок питания в комплекте.",
                    "storage_location": "Склад 1",
                    "barcode": "",
                    "characteristics": {
                        "Процессор": "Intel Core i5-8265U",
                        "Оперативная память": "8 ГБ",
                        "Объем накопителя": "256 ГБ",
                        "Тип накопителя": "SSD",
                        "Видеокарта": "Intel UHD Graphics 620",
                        "Диагональ экрана": "15.6\"",
                        "Разрешение экрана": "1920x1080 Full HD",
                        "Операционная система": "Windows 10 Pro"
                    },
                    "photos": []
                }
            ]
        }

        res = client.post("/api/products/json/import", json=owner_payload)
        assert res.status_code == 200
        data = res.json()

        # Invariant & Summary assertions
        assert data["success"] is True
        assert data["created_count"] == 2
        assert data["updated_count"] == 0
        assert data["skipped_count"] == 0
        assert data["errors"] == []

        summary = data.get("summary")
        assert summary is not None
        assert summary["total_in_payload"] == 2
        assert summary["created"] == 2
        assert summary["updated"] == 0
        assert summary["skipped"] == 0
        assert summary["errors"] == 0

        # Accounting invariant: created + updated + skipped + errors == total_in_payload
        assert summary["created"] + summary["updated"] + summary["skipped"] + summary["errors"] == 2

        # Results list assertions
        results = data.get("results")
        assert results is not None
        assert len(results) == 2
        assert results[0]["status"] == "created"
        assert results[0]["title"] == "Монитор Dell P2419H 24\" Full HD"
        assert results[1]["status"] == "created"
        assert results[1]["title"] == "Ноутбук HP ProBook 450 G6 15.6\""

        # Unique SKUs
        sku1 = results[0]["sku"]
        sku2 = results[1]["sku"]
        assert sku1 and sku2
        assert sku1 != sku2
        assert sku1.startswith("PRD-")
        assert sku2.startswith("PRD-")

        # Verify in DB: Dell monitor
        db = SessionLocal()
        m_prod = db.query(models.Product).filter(models.Product.id == results[0]["id"]).first()
        assert m_prod is not None
        assert m_prod.title == "Монитор Dell P2419H 24\" Full HD"
        assert m_prod.category.name == "Мониторы"
        assert m_prod.brand == "Dell"
        assert m_prod.model == "P2419H"
        assert m_prod.sale_price == 8500.0
        assert m_prod.purchase_price == 5000.0
        assert m_prod.condition == "Б/у"
        assert m_prod.quantity == 1
        assert m_prod.storage_location == "Витрина"
        assert "Монитор Dell P2419H в рабочем состоянии" in m_prod.description
        m_params = json.loads(m_prod.avito_params_json)
        assert m_params["Диагональ"] == "24\""
        assert m_params["Разрешение"] == "1920x1080"
        assert m_params["Тип матрицы"] == "IPS"
        assert m_params["Частота обновления"] == "60 Гц"
        assert m_params["Разъемы"] == "HDMI, DisplayPort, VGA, USB"

        # Verify in DB: HP laptop
        l_prod = db.query(models.Product).filter(models.Product.id == results[1]["id"]).first()
        assert l_prod is not None
        assert l_prod.title == "Ноутбук HP ProBook 450 G6 15.6\""
        assert l_prod.category.name == "Ноутбуки"
        assert l_prod.brand == "HP"
        assert l_prod.model == "ProBook 450 G6"
        assert l_prod.sale_price == 24500.0
        assert l_prod.purchase_price == 15500.0
        assert l_prod.condition == "Б/у"
        assert l_prod.quantity == 1
        assert l_prod.storage_location == "Склад 1"
        assert "Рабочий ноутбук HP ProBook 450 G6" in l_prod.description
        l_params = json.loads(l_prod.avito_params_json)
        assert l_params["Процессор"] == "Intel Core i5-8265U"
        assert l_params["Оперативная память"] == "8 ГБ"
        assert l_params["Объем накопителя"] == "256 ГБ"
        assert l_params["Тип накопителя"] == "SSD"
        assert l_params["Видеокарта"] == "Intel UHD Graphics 620"
        assert l_params["Диагональ экрана"] == "15.6\""
        assert l_params["Разрешение экрана"] == "1920x1080 Full HD"
        assert l_params["Операционная система"] == "Windows 10 Pro"
        db.close()

    def test_mixed_batch_accounting_invariant_enforced(self):
        """Stage 07C-R1-R2: Mixed batch accounts for every item (created, updated, skipped, errors)."""
        # Step 1: Create an existing product to test update and duplicate sku
        seed_res = client.post("/api/products/json/import", json={
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {"sku": "SEED-INV-1", "title": "Товар для обновления", "price": 1000.0}
            ]
        })
        existing_id = seed_res.json()["imported_product_ids"][0]

        # Step 2: Send mixed batch of 4 items:
        # 1. Update existing (id=existing_id) -> updated
        # 2. Duplicate SKU without id (sku="SEED-INV-1") -> skipped
        # 3. Invalid item (price="invalid") -> error
        # 4. New valid item -> created
        mixed_payload = {
            "format": "technoreboot-products",
            "version": 1,
            "products": [
                {"id": existing_id, "title": "Товар обновленный", "price": 1200.0},
                {"sku": "SEED-INV-1", "title": "Товар дубликат", "price": 999.0},
                {"title": "Товар с битой ценой", "price": "not_a_number"},
                {"title": "Новый валидный товар", "price": 3000.0}
            ]
        }

        res = client.post("/api/products/json/import", json=mixed_payload)
        assert res.status_code == 200
        data = res.json()

        assert data["success"] is True
        summary = data["summary"]
        assert summary["total_in_payload"] == 4
        assert summary["created"] == 1
        assert summary["updated"] == 1
        assert summary["skipped"] == 1
        assert summary["errors"] == 1

        # Strict invariant
        assert summary["created"] + summary["updated"] + summary["skipped"] + summary["errors"] == 4
        assert len(data["results"]) == 4

        statuses = [r["status"] for r in data["results"]]
        assert statuses == ["updated", "skipped", "error", "created"]


