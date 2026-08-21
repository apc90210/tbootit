import pytest
import json
from app import models, schemas

def test_extension_payload_contract_and_r9_binding(client, db_session):
    """Test that current extension listing payload binds to Core R9 models end-to-end."""
    
    # Actual observed extension payload structure from v0.2.10
    payload_data = {
        "account_key": "acc_extension_owner",
        "external_item_id": "8313765236",
        "external_url": "https://www.avito.ru/items/8313765236",
        "remote_status": "active",
        "remote_status_raw": "active",
        "title": "Лазерный цветной принтер hp m252n на запчасти",
        "price": 3500.0,
        "description": "Принтер HP Color LaserJet Pro M252n. Включается, но выдает ошибку.",
        "category_path": ["Бытовая электроника", "Оргтехника и расходники", "Принтеры"],
        "brand": "HP",
        "model": "m252n",
        "condition": "Б/у",
        "parameters": {
            "Состояние": "Б/у",
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Цветная"
        },
        "photos": []
    }

    # 1. Ingest via API
    res = client.post("/api/integrations/avito/ingest-parsed-ad", json=payload_data)
    assert res.status_code == 200, res.text
    res_data = res.json()
    assert res_data["status"] == "created"
    product_id = res_data["product_id"]

    # 2. Verify Product model & foreign key
    product = db_session.query(models.Product).filter(models.Product.id == product_id).first()
    assert product is not None
    assert product.title == "Лазерный цветной принтер hp m252n на запчасти"
    assert product.avito_category_id is not None

    # 3. Verify AvitoCategory model (no invented IDs)
    avito_cat = db_session.query(models.AvitoCategory).filter(models.AvitoCategory.id == product.avito_category_id).first()
    assert avito_cat is not None
    assert avito_cat.name == "Принтеры"
    assert avito_cat.external_category_id is None  # Honest null, no invented ID
    assert avito_cat.source == "avito"

    # 4. Verify AvitoAttributeDefinition and ProductAvitoAttributeValue
    attr_vals = db_session.query(models.ProductAvitoAttributeValue).filter(
        models.ProductAvitoAttributeValue.product_id == product_id
    ).all()
    assert len(attr_vals) == 4

    val_by_name = {v.definition.name: v for v in attr_vals}
    assert "Состояние" in val_by_name
    assert "Тип устройства" in val_by_name
    assert "Технология печати" in val_by_name
    assert "Цветность печати" in val_by_name

    assert val_by_name["Технология печати"].value == "Лазерная"
    assert val_by_name["Технология печати"].raw_value == "Лазерная"
    assert val_by_name["Технология печати"].source == "avito"

    # 5. Verify ProductDetails endpoint includes avito_category_name, characteristics, and avito_source_url
    details_res = client.get(f"/api/products/{product_id}/details")
    assert details_res.status_code == 200
    details = details_res.json()
    assert details["avito_category_name"] == "Принтеры"
    assert details["avito_source_url"] == "https://www.avito.ru/items/8313765236"
    assert details["avito_characteristics"] == {
        "Состояние": "Б/у",
        "Тип устройства": "Принтер",
        "Технология печати": "Лазерная",
        "Цветность печати": "Цветная"
    }

    # 6. Verify Structured R9 endpoint
    r9_res = client.get(f"/api/v1/products/{product_id}/avito-attributes")
    assert r9_res.status_code == 200
    r9_data = r9_res.json()
    assert r9_data["product_id"] == product_id
    assert r9_data["avito_category"]["name"] == "Принтеры"
    assert len(r9_data["attributes"]) == 4

def test_idempotent_repeat_ingest(client, db_session):
    """Verify repeat import updates data and does not duplicate categories or definitions."""
    payload_data = {
        "account_key": "acc_extension_owner",
        "external_item_id": "8313765237",
        "external_url": "https://www.avito.ru/items/8313765237",
        "title": "Лазерный цветной принтер hp m252n на запчасти (обновлено)",
        "price": 3200.0,
        "category_path": ["Оргтехника", "Принтеры"],
        "parameters": {
            "Состояние": "Б/у",
            "Технология печати": "Лазерная"
        },
        "photos": []
    }

    # First ingest
    res1 = client.post("/api/integrations/avito/ingest-parsed-ad", json=payload_data)
    assert res1.status_code == 200
    pid = res1.json()["product_id"]

    # Second ingest
    res2 = client.post("/api/integrations/avito/ingest-parsed-ad", json=payload_data)
    assert res2.status_code == 200
    assert res2.json()["status"] == "updated"
    assert res2.json()["product_id"] == pid

    # Count categories and definitions
    cats_count = db_session.query(models.AvitoCategory).filter(models.AvitoCategory.name == "Принтеры").count()
    assert cats_count == 1

    attr_count = db_session.query(models.ProductAvitoAttributeValue).filter(
        models.ProductAvitoAttributeValue.product_id == pid
    ).count()
    assert attr_count == 2

def test_priority_categories_schema_scaffolding(client, db_session):
    """Verify distinct priority categories (Printers, MFP, Computers, Components) are isolated."""
    categories_data = [
        ("9001", "Принтеры", {"Технология печати": "Струйная", "Формат": "A4"}),
        ("9002", "МФУ", {"Функции": "Печать, сканирование, копирование", "Цветность": "Черно-белая"}),
        ("9003", "Настольные компьютеры", {"Процессор": "Intel Core i5", "Оперативная память": "16 ГБ"}),
        ("9004", "Видеокарты", {"Объем видеопамяти": "8 ГБ", "Тип памяти": "GDDR6"})
    ]

    for ext_id, cat_name, params in categories_data:
        payload = {
            "account_key": "acc_extension_owner",
            "external_item_id": ext_id,
            "title": f"Тестовый товар {cat_name}",
            "price": 10000.0,
            "category_path": ["Электроника", cat_name],
            "parameters": params,
            "photos": []
        }
        res = client.post("/api/integrations/avito/ingest-parsed-ad", json=payload)
        assert res.status_code == 200, res.text

    # Verify 4 distinct categories created
    for _, cat_name, params in categories_data:
        cat = db_session.query(models.AvitoCategory).filter(models.AvitoCategory.name == cat_name).first()
        assert cat is not None
        for key in params.keys():
            defn = db_session.query(models.AvitoAttributeDefinition).filter(
                models.AvitoAttributeDefinition.category_id == cat.id,
                models.AvitoAttributeDefinition.external_key == key
            ).first()
            assert defn is not None, f"Missing definition {key} in category {cat_name}"

def test_manual_product_without_avito_attributes(client, db_session):
    """Verify products created without Avito integration return clean empty details."""
    prod = models.Product(
        sku="TEST-MANUAL-NO-AVITO",
        title="Обычный товар без Авито",
        status="active"
    )
    db_session.add(prod)
    db_session.commit()

    details_res = client.get(f"/api/products/{prod.id}/details")
    assert details_res.status_code == 200
    details = details_res.json()
    assert details["avito_category_name"] is None
    assert details["avito_characteristics"] == {}
    assert details["avito_source_url"] is None

    r9_res = client.get(f"/api/v1/products/{prod.id}/avito-attributes")
    assert r9_res.status_code == 200
    r9_data = r9_res.json()
    assert r9_data["avito_category"] is None
    assert r9_data["attributes"] == []

def test_rich_monitor_attribute_validation(client, db_session):
    """Synthetic test validating a rich 12-attribute monitor dataset."""
    rich_monitor_params = {
        "Состояние": "Б/у",
        "Диагональ": "27 дюймов",
        "Разрешение": "2560x1440 (QHD)",
        "Тип матрицы": "IPS",
        "Частота обновления": "144 Гц",
        "Соотношение сторон": "16:9",
        "Яркость": "350 кд/м²",
        "Время отклика": "1 мс",
        "Интерфейсы": "HDMI, DisplayPort",
        "Регулировка по высоте": "Да",
        "Встроенные динамики": "Есть",
        "Цвет": "Черный"
    }

    payload = {
        "account_key": "acc_extension_owner",
        "external_item_id": "9988776655",
        "external_url": "https://www.avito.ru/ekaterinburg/tovary_dlya_kompyutera/monitor_27_ips_144hz_9988776655",
        "title": "Монитор 27\" IPS 144Hz 2K",
        "price": 18500.0,
        "category_path": ["Товары для компьютера", "Мониторы"],
        "brand": "LG",
        "model": "27GL850",
        "condition": "Б/у",
        "parameters": rich_monitor_params,
        "photos": []
    }

    res = client.post("/api/integrations/avito/ingest-parsed-ad", json=payload)
    assert res.status_code == 200, res.text
    pid = res.json()["product_id"]

    details_res = client.get(f"/api/products/{pid}/details")
    assert details_res.status_code == 200
    details = details_res.json()
    assert details["avito_category_name"] == "Мониторы"
    assert details["avito_source_url"] == "https://www.avito.ru/ekaterinburg/tovary_dlya_kompyutera/monitor_27_ips_144hz_9988776655"
    assert len(details["avito_characteristics"]) == 12
    assert details["avito_characteristics"]["Частота обновления"] == "144 Гц"
    assert details["avito_characteristics"]["Разрешение"] == "2560x1440 (QHD)"

    r9_res = client.get(f"/api/v1/products/{pid}/avito-attributes")
    assert r9_res.status_code == 200
    r9_data = r9_res.json()
    assert len(r9_data["attributes"]) == 12

