import pytest
from urllib.parse import unquote
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

MOCK_META = {
    "categories": ["Ноутбуки", "Системные блоки", "Принтеры и МФУ", "Мониторы", "Комплектующие", "Оргтехника"],
    "standard_characteristics": {
        "Ноутбуки": ["Процессор", "Оперативная память", "Объем накопителя", "Тип накопителя", "Диагональ экрана", "Видеокарта", "Состояние аккумулятора / Износ", "Операционная система"],
        "Системные блоки": ["Процессор", "Оперативная память", "Накопитель", "Видеокарта", "Материнская плата", "Блок питания", "Корпус", "Операционная система"]
    },
    "conditions": ["Новый", "Как новый", "Отличное", "Хорошее", "Б/У", "На запчасти"],
    "statuses": ["in_stock", "draft", "reserved", "sold", "in_repair", "written_off"],
    "storage_locations": ["store", "workshop", "archive", "draft"]
}

MOCK_PRODUCT = {
    "id": 42,
    "title": "Ноутбук Lenovo ThinkPad T480",
    "category": "Ноутбуки",
    "category_name": "Ноутбуки",
    "brand": "Lenovo",
    "model": "ThinkPad T480",
    "condition": "Б/У",
    "price": 35000.0,
    "sale_price": 33000.0,
    "cost_price": 25000.0,
    "quantity": 2,
    "status": "in_stock",
    "storage_location": "store",
    "sku": "PRD-TEST0042",
    "barcode": "4601234567890",
    "description": "Отличный рабочий ноутбук",
    "characteristics": {
        "Процессор": "Intel Core i5-8350U",
        "Оперативная память": "16 ГБ",
        "Объем накопителя": "256 ГБ SSD",
        "Кастомный параметр": "Значение кастом"
    },
    "photos": [
        {
            "id": 101,
            "product_id": 42,
            "filename": "42_main.jpg",
            "media_url": "/media/product_photos/42/42_main.jpg",
            "sort_order": 0,
            "created_at": "2026-09-10T10:00:00"
        },
        {
            "id": 102,
            "product_id": 42,
            "filename": "42_side.jpg",
            "media_url": "/media/product_photos/42/42_side.jpg",
            "sort_order": 1,
            "created_at": "2026-09-10T10:01:00"
        }
    ]
}


def test_products_list_contains_manual_create_button_and_edit_links():
    """Verify that product list contains '+ Создать товар вручную' and per-row 'Редактировать'."""
    mock_list_data = {
        "items": [
            {
                "id": 42,
                "title": "Ноутбук Lenovo",
                "price": 35000.0,
                "quantity": 2,
                "status": "in_stock",
                "storage_location": "store",
                "sku": "PRD-TEST0042",
                "barcode": "4601234567890"
            }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0
    }
    with patch("app.routers.products.core_client.get_products", new_callable=AsyncMock) as mock_list, \
         patch("app.routers.products.core_client.get_product_filter_options", new_callable=AsyncMock) as mock_opts:
        mock_list.return_value = mock_list_data
        mock_opts.return_value = {}

        res = client.get("/products")
        assert res.status_code == 200
        assert "Создать товар вручную" in res.text
        assert "/inventory/products/new" in res.text
        assert "+ Добавить новый товар через JSON" in res.text
        assert "/inventory/products/42/edit" in res.text


def test_product_detail_contains_edit_button():
    """Verify that product detail page has 'Редактировать товар' button."""
    with patch("app.routers.products.core_client.get_product_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MOCK_PRODUCT
        res = client.get("/products/42")
        assert res.status_code == 200
        assert "Редактировать товар" in res.text
        assert "/inventory/products/42/edit" in res.text


def test_new_product_form_renders():
    """Verify that GET /products/new renders creation form with editor metadata."""
    with patch("app.routers.products.core_client.get_editor_meta", new_callable=AsyncMock) as mock_meta:
        mock_meta.return_value = MOCK_META
        res = client.get("/products/new")
        assert res.status_code == 200
        assert "Создание товара вручную" in res.text
        assert "Ноутбуки" in res.text
        assert "Системные блоки" in res.text
        assert "Б/У" in res.text
        assert "Сохранить товар" in res.text or "Создать товар" in res.text


def test_create_product_empty_title_validation():
    """Verify that creating product with empty title fails with 400 and validation message."""
    with patch("app.routers.products.core_client.get_editor_meta", new_callable=AsyncMock) as mock_meta:
        mock_meta.return_value = MOCK_META
        res = client.post("/products/new", data={"title": "   ", "price": "1000", "quantity": "1"})
        assert res.status_code == 400
        assert "Название товара обязательно" in res.text


def test_create_product_negative_price_validation():
    """Verify that negative price fails with 400."""
    with patch("app.routers.products.core_client.get_editor_meta", new_callable=AsyncMock) as mock_meta:
        mock_meta.return_value = MOCK_META
        res = client.post("/products/new", data={"title": "Тестовый товар", "price": "-500", "quantity": "1"})
        assert res.status_code == 400
        assert "не может быть отрицательной" in res.text


def test_create_product_success_redirect():
    """Verify that successful creation posts payload to Core and redirects to edit mode."""
    with patch("app.routers.products.core_client.create_product", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {"id": 99, "title": "Новый ПК", "sku": "PRD-NEW00099"}
        
        post_data = {
            "title": "Системный блок Core i7",
            "category": "Системные блоки",
            "brand": "Custom",
            "model": "Gamer-1",
            "condition": "Новый",
            "price": "65000",
            "sale_price": "60000",
            "cost_price": "45000",
            "quantity": "3",
            "status": "in_stock",
            "storage_location": "store",
            "sku": "",  # Auto-generated
            "char_Процессор": "Intel Core i7-12700",
            "char_Оперативная память": "32 ГБ DDR5",
            "custom_char_name[]": ["Охлаждение"],
            "custom_char_val[]": ["Водяное"]
        }
        res = client.post("/products/new", data=post_data, follow_redirects=False)
        assert res.status_code == 303
        assert unquote(res.headers["location"]) == "/inventory/products/99/edit?msg=Товар+успешно+создан"

        # Check payload passed to core_client
        assert mock_create.called
        called_payload = mock_create.call_args[0][0]
        assert called_payload["title"] == "Системный блок Core i7"
        assert called_payload["category"] == "Системные блоки"
        assert called_payload["characteristics"]["Процессор"] == "Intel Core i7-12700"
        assert called_payload["characteristics"]["Охлаждение"] == "Водяное"
        assert called_payload["sku"] is None


def test_edit_product_form_renders():
    """Verify that GET /products/{id}/edit renders product details, category, and existing photos."""
    with patch("app.routers.products.core_client.get_product_details", new_callable=AsyncMock) as mock_get, \
         patch("app.routers.products.core_client.get_editor_meta", new_callable=AsyncMock) as mock_meta:
        mock_get.return_value = MOCK_PRODUCT
        mock_meta.return_value = MOCK_META

        res = client.get("/products/42/edit")
        assert res.status_code == 200
        assert "Редактирование товара" in res.text
        assert "Lenovo ThinkPad T480" in res.text
        assert "42_main.jpg" in res.text
        assert "Главное" in res.text
        assert "Сделать главным" in res.text
        assert "Удалить" in res.text


def test_edit_product_update_success():
    """Verify that POST /products/{id}/edit calls full_update_product and redirects."""
    with patch("app.routers.products.core_client.full_update_product", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"id": 42, "title": "Обновленный Lenovo ThinkPad"}
        
        post_data = {
            "title": "Обновленный Lenovo ThinkPad",
            "category": "Ноутбуки",
            "brand": "Lenovo",
            "price": "34000",
            "quantity": "5",
            "status": "in_stock",
            "storage_location": "store",
            "char_Процессор": "Intel Core i5-8350U vPro",
            "custom_char_name[]": ["Кастомный параметр"],
            "custom_char_val[]": ["Новое значение"]
        }
        res = client.post("/products/42/edit", data=post_data, follow_redirects=False)
        assert res.status_code == 303
        assert unquote(res.headers["location"]) == "/inventory/products/42/edit?msg=Изменения+успешно+сохранены"
        
        assert mock_update.called
        called_id = mock_update.call_args[0][0]
        called_payload = mock_update.call_args[0][1]
        assert called_id == 42
        assert called_payload["title"] == "Обновленный Lenovo ThinkPad"
        assert called_payload["characteristics"]["Кастомный параметр"] == "Новое значение"


def test_photos_upload_batch_ajax():
    """Verify AJAX photo batch upload endpoint."""
    with patch("app.routers.products.core_client.upload_product_photos_batch", new_callable=AsyncMock) as mock_batch:
        mock_batch.return_value = {
            "uploaded": [{"id": 201, "filename": "test.jpg"}],
            "failed": []
        }
        files = [
            ("files", ("photo1.jpg", b"\xff\xd8\xff\xe0" + b"fakeimg", "image/jpeg")),
            ("files", ("photo2.png", b"\x89PNG" + b"fakeimg", "image/png"))
        ]
        res = client.post("/products/42/photos/upload", files=files, headers={"Accept": "application/json"})
        assert res.status_code == 200
        data = res.json()
        assert len(data["uploaded"]) == 1
        assert mock_batch.called


def test_photo_make_main_and_delete_and_reorder():
    """Verify photo make-main, delete, and reorder actions."""
    with patch("app.routers.products.core_client.make_product_photo_main", new_callable=AsyncMock) as mock_main, \
         patch("app.routers.products.core_client.delete_product_photo", new_callable=AsyncMock) as mock_del, \
         patch("app.routers.products.core_client.reorder_product_photos", new_callable=AsyncMock) as mock_reorder:
        
        mock_main.return_value = {"id": 102, "sort_order": 0}
        mock_del.return_value = {"deleted": True, "id": 102}
        mock_reorder.return_value = {"reordered": True}

        # Make main
        res1 = client.post("/products/42/photos/102/make-main", headers={"Accept": "application/json"})
        assert res1.status_code == 200
        assert mock_main.called

        # Reorder
        res2 = client.post("/products/42/photos/reorder", json={"photo_ids": [102, 101]}, headers={"Accept": "application/json"})
        assert res2.status_code == 200
        assert mock_reorder.called

        # Delete
        res3 = client.post("/products/42/photos/102/delete", headers={"Accept": "application/json"})
        assert res3.status_code == 200
        assert mock_del.called
