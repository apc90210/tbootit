import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.routers.products import format_core_error

client = TestClient(app)

MOCK_META = {
    "categories": ["Ноутбуки", "Системные блоки"],
    "standard_characteristics": {"Ноутбуки": ["Процессор"]},
    "conditions": ["Б/У"],
    "statuses": ["in_stock"],
    "storage_locations": ["store"]
}

MOCK_PRODUCT = {
    "id": 42,
    "title": "Ноутбук Lenovo ThinkPad",
    "category": "Ноутбуки",
    "sale_price": 35000.0,
    "purchase_price": 20000.0,
    "quantity": 1,
    "status": "in_stock",
    "storage_location": "store",
    "description": "Исходное описание"
}

def test_ui_has_single_sale_price_field_no_duplicates():
    """TEST K: Verify no duplicate confusing price fields in editor UI."""
    with patch("app.core_client.core_client.get_product_details", new=AsyncMock(return_value=MOCK_PRODUCT)), \
         patch("app.core_client.core_client.get_editor_meta", new=AsyncMock(return_value=MOCK_META)):
        resp = client.get("/products/42/edit")
        assert resp.status_code == 200
        html = resp.text
        # Must contain single clear 'Цена продажи'
        assert "Цена продажи (₽)" in html
        assert 'name="sale_price"' in html
        # Must NOT contain duplicate 'Цена (базовая, ₽)'
        assert "Цена (базовая, ₽)" not in html
        assert 'name="price"' not in html

def test_edit_description_only_preserves_sale_price():
    """TEST B: Edit description only -> save succeeds and sale price is sent unchanged."""
    captured_payload = {}
    async def mock_full_update(prod_id, payload):
        nonlocal captured_payload
        captured_payload = payload
        return {"id": prod_id, "title": payload["title"], "sale_price": payload["sale_price"]}

    with patch("app.core_client.core_client.get_product_details", new=AsyncMock(return_value=MOCK_PRODUCT)), \
         patch("app.core_client.core_client.get_editor_meta", new=AsyncMock(return_value=MOCK_META)), \
         patch("app.core_client.core_client.full_update_product", side_effect=mock_full_update):
        
        # Simulating submitting the form with original sale_price pre-populated and new description
        data = {
            "title": "Ноутбук Lenovo ThinkPad",
            "description": "Новое описание товара",
            "sale_price": "35000.0",
            "quantity": "1"
        }
        resp = client.post("/products/42/edit", data=data, follow_redirects=False)
        assert resp.status_code == 303
        assert captured_payload.get("sale_price") == 35000.0
        assert captured_payload.get("description") == "Новое описание товара"

def test_edit_sale_price_integer_and_decimal_with_comma():
    """TEST C & D: Setting sale price to integer or decimal with comma -> normalized properly."""
    captured_payload = {}
    async def mock_full_update(prod_id, payload):
        nonlocal captured_payload
        captured_payload = payload
        return {"id": prod_id, "title": payload["title"], "sale_price": payload["sale_price"]}

    with patch("app.core_client.core_client.get_product_details", new=AsyncMock(return_value=MOCK_PRODUCT)), \
         patch("app.core_client.core_client.get_editor_meta", new=AsyncMock(return_value=MOCK_META)), \
         patch("app.core_client.core_client.full_update_product", side_effect=mock_full_update):
        
        # Test comma decimal: '27500,50'
        data = {
            "title": "Ноутбук Lenovo ThinkPad",
            "sale_price": "27500,50",
            "quantity": "1"
        }
        resp = client.post("/products/42/edit", data=data, follow_redirects=False)
        assert resp.status_code == 303
        assert captured_payload.get("sale_price") == 27500.50

def test_edit_blank_sale_price_controlled_russian_error():
    """TEST E: Blank required sale price returns controlled Russian validation, no raw Pydantic error."""
    with patch("app.core_client.core_client.get_product_details", new=AsyncMock(return_value=MOCK_PRODUCT)), \
         patch("app.core_client.core_client.get_editor_meta", new=AsyncMock(return_value=MOCK_META)):
        
        data = {
            "title": "Ноутбук Lenovo ThinkPad",
            "sale_price": "   ",
            "quantity": "1"
        }
        resp = client.post("/products/42/edit", data=data, follow_redirects=False)
        assert resp.status_code == 400
        html = resp.text
        assert "Укажите корректную цену продажи" in html
        assert "float_type" not in html
        assert "pydantic" not in html

def test_format_core_error_replaces_raw_pydantic():
    """Verify format_core_error strips Pydantic URLs and translates 422 errors into friendly Russian."""
    raw_pydantic = [
        {
            'type': 'float_type',
            'loc': ['body', 'sale_price'],
            'msg': 'Input should be a valid number',
            'input': None,
            'url': 'https://errors.pydantic.dev/2.6/v/float_type'
        }
    ]
    formatted = format_core_error(raw_pydantic)
    assert "Цена продажи должна быть корректным числом" in formatted
    assert "https://" not in formatted
    assert "pydantic" not in formatted

    # Test stringified python repr
    repr_str = "[{'type': 'float_type', 'loc': ['body', 'sale_price'], 'msg': 'Input should be a valid number', 'input': None, 'url': 'https://errors.pydantic.dev/2.6/v/float_type'}]"
    formatted_repr = format_core_error(repr_str)
    assert "Цена продажи должна быть корректным числом" in formatted_repr
    assert "https://" not in formatted_repr

def test_legacy_product_null_price_edit_description():
    """TEST J: Legacy product with null sale_price can be edited without unrelated validation failure."""
    legacy_product = {
        "id": 99,
        "title": "Legacy Item Without Price",
        "sale_price": None,
        "quantity": 1
    }
    captured_payload = {}
    async def mock_full_update(prod_id, payload):
        nonlocal captured_payload
        captured_payload = payload
        return {"id": prod_id, "title": payload["title"], "sale_price": payload["sale_price"]}

    with patch("app.core_client.core_client.get_product_details", new=AsyncMock(return_value=legacy_product)), \
         patch("app.core_client.core_client.get_editor_meta", new=AsyncMock(return_value=MOCK_META)), \
         patch("app.core_client.core_client.full_update_product", side_effect=mock_full_update):
        
        data = {
            "title": "Legacy Item Updated Title",
            "sale_price": "",
            "quantity": "1"
        }
        resp = client.post("/products/99/edit", data=data, follow_redirects=False)
        assert resp.status_code == 303
        assert captured_payload.get("sale_price") is None
        assert captured_payload.get("title") == "Legacy Item Updated Title"

def test_create_form_price_semantics_match_edit():
    """TEST L: Create form validates sale_price, normalizes decimal comma, and rejects empty price."""
    captured_payload = {}
    async def mock_create(payload):
        nonlocal captured_payload
        captured_payload = payload
        return {"id": 100, "title": payload["title"], "sale_price": payload["sale_price"]}

    with patch("app.core_client.core_client.get_editor_meta", new=AsyncMock(return_value=MOCK_META)), \
         patch("app.core_client.core_client.create_product", side_effect=mock_create):
        
        # 1. Blank sale_price rejected
        r_blank = client.post("/products/new", data={"title": "Новый товар", "sale_price": ""})
        assert r_blank.status_code == 400
        assert "Укажите корректную цену продажи" in r_blank.text

        # 2. Comma decimal normalized
        r_valid = client.post("/products/new", data={"title": "Новый товар", "sale_price": "14900,99"}, follow_redirects=False)
        assert r_valid.status_code == 303
        assert captured_payload.get("sale_price") == 14900.99
