from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

def test_product_detail_with_avito_characteristics_and_source_link():
    """Verify that a product with Avito characteristics & source URL renders both correctly."""
    mock_product = {
        "id": 58,
        "title": "Лазерный цветной принтер hp m252n на запчасти",
        "sale_price": 3500.0,
        "status": "draft",
        "storage_location": "store",
        "quantity": 1,
        "description": "Тестовое описание",
        "photos": [],
        "avito_category_name": "Принтеры",
        "avito_source_url": "https://www.avito.ru/ekaterinburg/orgtehnika_i_rashodniki/lazernyy_tsvetnoy_printer_hp_m252n_na_zapchasti_8313765236",
        "avito_characteristics": {
            "Состояние": "Б/у",
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Цветная"
        }
    }
    with patch("app.routers.products.core_client.get_product_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        res = client.get("/products/58")
        assert res.status_code == 200
        assert "Характеристики Avito" in res.text
        assert "Принтеры" in res.text
        assert "Технология печати" in res.text
        assert "Лазерная" in res.text
        assert "Цветность печати" in res.text
        assert "Цветная" in res.text
        assert "Источник: <strong>Avito</strong>" in res.text
        assert 'href="https://www.avito.ru/ekaterinburg/orgtehnika_i_rashodniki/lazernyy_tsvetnoy_printer_hp_m252n_na_zapchasti_8313765236"' in res.text
        assert 'target="_blank"' in res.text
        assert 'rel="noopener noreferrer"' in res.text
        assert "Открыть объявление на Avito ↗" in res.text

def test_product_detail_without_avito_source_link():
    """Verify that a product without Avito source URL does not render broken link."""
    mock_product = {
        "id": 99,
        "title": "Обычный товар",
        "sale_price": 1000.0,
        "status": "in_stock",
        "storage_location": "store",
        "quantity": 1,
        "description": "Описание",
        "photos": [],
        "avito_category_name": None,
        "avito_source_url": None,
        "avito_characteristics": {}
    }
    with patch("app.routers.products.core_client.get_product_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        res = client.get("/products/99")
        assert res.status_code == 200
        assert "Характеристики Avito" in res.text
        assert "Характеристики Avito не импортированы" in res.text
        assert "Открыть объявление на Avito ↗" not in res.text
        assert "avito-source-link-container" not in res.text

def test_product_detail_rich_monitor_attributes_ui():
    """Verify rich 12-attribute monitor renders all keys and values in table."""
    mock_product = {
        "id": 150,
        "title": "Монитор 27\" IPS 144Hz 2K",
        "sale_price": 18500.0,
        "status": "draft",
        "storage_location": "store",
        "quantity": 1,
        "description": "Игровой монитор LG",
        "photos": [],
        "avito_category_name": "Мониторы",
        "avito_source_url": "https://www.avito.ru/items/9988776655",
        "avito_characteristics": {
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
    }
    with patch("app.routers.products.core_client.get_product_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        res = client.get("/products/150")
        assert res.status_code == 200
        assert "Мониторы" in res.text
        assert "Диагональ" in res.text
        assert "27 дюймов" in res.text
        assert "Разрешение" in res.text
        assert "2560x1440 (QHD)" in res.text
        assert "Частота обновления" in res.text
        assert "144 Гц" in res.text
        assert "Открыть объявление на Avito ↗" in res.text
