import pytest
from unittest.mock import AsyncMock, patch
from starlette.testclient import TestClient
from app.main import app
from app.core_client import core_client

@pytest.fixture
def client():
    return TestClient(app)

def test_batch_checkboxes_and_toolbar_present_in_products_page(client):
    mock_products = {
        "items": [
            {
                "id": 101,
                "title": "ThinkPad T480s",
                "sku": "TP-480S",
                "barcode": "4600000000101",
                "status": "in_stock",
                "sale_price": 28000.0,
                "price": 28000.0,
                "quantity": 2,
                "storage_location": "store",
                "main_photo_url": None
            },
            {
                "id": 102,
                "title": "Dell UltraSharp U2415",
                "sku": "DELL-U2415",
                "barcode": "4600000000102",
                "status": "draft",
                "sale_price": 12500.0,
                "price": 12500.0,
                "quantity": 1,
                "storage_location": "workshop",
                "main_photo_url": None
            }
        ],
        "total": 2,
        "limit": 50,
        "offset": 0
    }

    with patch.object(core_client, "get_products", new=AsyncMock(return_value=mock_products)), \
         patch.object(core_client, "get_product_filter_options", new=AsyncMock(return_value={})):
        res = client.get("/products")
        assert res.status_code == 200
        html = res.text

        # 1. Header checkbox
        assert 'id="select-all-products"' in html
        # 2. Row checkboxes
        assert 'class="product-select-cb"' in html
        assert 'value="101"' in html
        assert 'value="102"' in html
        # 3. Batch action bar and controls
        assert 'id="batch-actions-bar"' in html
        assert 'id="batch-selected-count"' in html
        assert 'id="btn-batch-print-tags"' in html
        assert 'id="btn-batch-add-cart"' in html
        assert 'id="batch-status-select"' in html
        assert '— Статус (не менять) —' in html
        assert 'id="batch-location-select"' in html
        assert '— Место (не менять) —' in html
        assert 'id="btn-batch-apply-changes"' in html


def test_batch_action_apply_changes_both_status_and_location(client):
    with patch.object(core_client, "batch_update_products", new=AsyncMock(return_value={"success": True, "updated_count": 2})) as mock_batch:
        res = client.post(
            "/products/batch-action",
            data={
                "action": "apply_changes",
                "new_status": "in_stock",
                "new_location": "store",
                "ids": "101,102"
            },
            follow_redirects=False
        )
        assert res.status_code == 303
        assert "/inventory/products?" in res.headers["location"]
        mock_batch.assert_called_once_with({
            "product_ids": [101, 102],
            "status": "in_stock",
            "storage_location": "store",
            "comment": "Массовое обновление: статус «В наличии», место «Магазин»"
        })


def test_batch_action_apply_changes_only_status(client):
    with patch.object(core_client, "batch_update_products", new=AsyncMock(return_value={"success": True, "updated_count": 2})) as mock_batch:
        res = client.post(
            "/products/batch-action",
            data={
                "action": "apply_changes",
                "new_status": "archived",
                "new_location": "",
                "ids": "101,102"
            },
            follow_redirects=False
        )
        assert res.status_code == 303
        assert "/inventory/products?" in res.headers["location"]
        mock_batch.assert_called_once_with({
            "product_ids": [101, 102],
            "status": "archived",
            "comment": "Массовое обновление: статус «В архиве»"
        })


def test_batch_action_apply_changes_only_location(client):
    with patch.object(core_client, "batch_update_products", new=AsyncMock(return_value={"success": True, "updated_count": 2})) as mock_batch:
        res = client.post(
            "/products/batch-action",
            data={
                "action": "apply_changes",
                "new_status": "",
                "new_location": "workshop",
                "ids": "101,102"
            },
            follow_redirects=False
        )
        assert res.status_code == 303
        assert "/inventory/products?" in res.headers["location"]
        mock_batch.assert_called_once_with({
            "product_ids": [101, 102],
            "storage_location": "workshop",
            "comment": "Массовое обновление: место «Мастерская»"
        })


def test_batch_action_apply_changes_neither_selected_fails(client):
    res = client.post(
        "/products/batch-action",
        data={
            "action": "apply_changes",
            "new_status": "",
            "new_location": "",
            "ids": "101,102"
        },
        follow_redirects=False
    )
    assert res.status_code == 303
    assert "error=" in res.headers["location"]


def test_batch_action_set_status(client):
    with patch.object(core_client, "batch_update_products", new=AsyncMock(return_value={"success": True, "updated_count": 2})) as mock_batch:
        res = client.post(
            "/products/batch-action",
            data={
                "action": "set_status",
                "new_status": "draft",
                "ids": "101,102"
            },
            follow_redirects=False
        )
        assert res.status_code == 303
        assert "/inventory/products?" in res.headers["location"]
        mock_batch.assert_called_once_with({
            "product_ids": [101, 102],
            "status": "draft",
            "comment": "Массовое обновление: статус «Черновик»"
        })


def test_batch_action_set_location(client):
    with patch.object(core_client, "batch_update_products", new=AsyncMock(return_value={"success": True, "updated_count": 2})) as mock_batch:
        res = client.post(
            "/products/batch-action",
            data={
                "action": "set_location",
                "new_location": "workshop",
                "ids": "101,102"
            },
            follow_redirects=False
        )
        assert res.status_code == 303
        assert "/inventory/products?" in res.headers["location"]
        mock_batch.assert_called_once_with({
            "product_ids": [101, 102],
            "storage_location": "workshop",
            "comment": "Массовое обновление: место «Мастерская»"
        })


def test_batch_action_add_to_cart(client):
    mock_p1 = {
        "id": 101,
        "title": "ThinkPad T480s",
        "sale_price": 28000.0,
        "price": 28000.0,
        "status": "in_stock",
        "storage_location": "store",
        "quantity": 2
    }
    mock_p2 = {
        "id": 102,
        "title": "Dell U2415",
        "sale_price": 12500.0,
        "price": 12500.0,
        "status": "in_stock",
        "storage_location": "store",
        "quantity": 1
    }

    async def mock_get_details(pid):
        if pid == 101: return mock_p1
        if pid == 102: return mock_p2
        return {"error": True}

    with patch.object(core_client, "get_product_details", side_effect=mock_get_details):
        res = client.post(
            "/products/batch-action",
            data={
                "action": "add_to_cart",
                "ids": "101,102"
            },
            follow_redirects=False
        )
        assert res.status_code == 303
        assert res.headers["location"] == "/inventory/cart"


def test_batch_price_tags_page(client):
    mock_p1 = {
        "id": 201,
        "title": "HP LaserJet 1022",
        "sku": "HP-1022",
        "barcode": "4600000000201",
        "sale_price": 3500.0,
        "price": 3500.0,
        "condition": "Б/У",
        "status": "in_stock"
    }
    mock_p2 = {
        "id": 202,
        "title": "Logitech MX Master 3S",
        "sku": "LOGI-MX3S",
        "barcode": "4600000000202",
        "sale_price": 6500.0,
        "price": 6500.0,
        "condition": "Отличное",
        "status": "in_stock"
    }

    async def mock_get_details(pid):
        if pid == 201: return mock_p1
        if pid == 202: return mock_p2
        return {"error": True}

    with patch.object(core_client, "get_product_details", side_effect=mock_get_details):
        res = client.get("/products/price-tags/batch?ids=201,202")
        assert res.status_code == 200
        html = res.text
        assert "Массовая печать ценников 58×40 мм" in html
        assert "HP LaserJet 1022" in html
        assert "Logitech MX Master 3S" in html
        assert "3 500 ₽" in html
        assert "6 500 ₽" in html
        assert "ТЕХНОРЕБУТ" in html
        assert "window.print()" in html
