import pytest
from unittest.mock import AsyncMock, patch
from httpx import Response
from starlette.testclient import TestClient
from app.main import app
from app.core_client import core_client

client = TestClient(app)


def test_product_detail_top_and_bottom_actions_in_stock(respx_mock):
    """
    Verify that in-stock product displays active action buttons both at the top
    and at the bottom of the product detail card:
    - Редактировать товар
    - Продать
    - В корзину
    - Ценник 58×40
    - Назад к товарам
    """
    mock_product = {
        "id": 105,
        "title": "Игровой ноутбук Asus ROG Strix",
        "sale_price": 65000.0,
        "price": 65000.0,
        "quantity": 1,
        "status": "in_stock",
        "storage_location": "store",
        "sku": "AVITO-105",
        "barcode": "460000000105"
    }

    with patch.object(core_client, "get_product_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product

        res = client.get("/products/105")
        assert res.status_code == 200
        html = res.text

        # Verify top and bottom action containers exist
        assert 'id="product-actions-top"' in html
        assert 'id="product-actions-bottom"' in html

        # Top container assertions
        top_start = html.find('id="product-actions-top"')
        top_end = html.find('</div>', top_start)
        # Find closing div of top toolbar
        top_block = html[top_start:top_start + 2500]

        assert 'href="/inventory/products"' in top_block
        assert 'Назад к товарам' in top_block
        assert 'href="/inventory/products/105/edit"' in top_block
        assert '✏️ Редактировать товар' in top_block
        assert 'href="/inventory/sales/new?product_id=105"' in top_block
        assert 'Продать' in top_block
        assert 'class="quick-add-form"' in top_block
        assert 'data-product-id="105"' in top_block
        assert 'В корзину' in top_block
        assert 'href="/inventory/products/105/price-tag/58x40"' in top_block
        assert 'Ценник 58×40' in top_block

        # Bottom container assertions
        bottom_start = html.find('id="product-actions-bottom"')
        bottom_block = html[bottom_start:bottom_start + 2500]

        assert 'href="/inventory/products"' in bottom_block
        assert 'Назад к товарам' in bottom_block
        assert 'id="btn-edit-product"' in bottom_block
        assert 'href="/inventory/products/105/edit"' in bottom_block
        assert '✏️ Редактировать товар' in bottom_block
        assert 'href="/inventory/sales/new?product_id=105"' in bottom_block
        assert 'Продать' in bottom_block
        assert 'class="quick-add-form"' in bottom_block
        assert 'data-product-id="105"' in bottom_block
        assert 'В корзину' in bottom_block
        assert 'href="/inventory/products/105/price-tag/58x40"' in bottom_block
        assert 'Ценник 58×40' in bottom_block


def test_product_detail_top_and_bottom_actions_out_of_stock_disabled():
    """
    Verify that out-of-stock or sold product displays disabled buttons
    both at the top and at the bottom:
    - Продать (disabled)
    - В корзину (disabled)
    - Ценник 58×40 (disabled)
    - Редактировать товар (remains clickable)
    """
    mock_sold_product = {
        "id": 106,
        "title": "Проданный монитор LG UltraGear",
        "sale_price": 18000.0,
        "price": 18000.0,
        "quantity": 0,
        "status": "sold",
        "storage_location": "archive",
        "sku": "AVITO-106"
    }

    with patch.object(core_client, "get_product_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_sold_product

        res = client.get("/products/106")
        assert res.status_code == 200
        html = res.text

        top_start = html.find('id="product-actions-top"')
        top_block = html[top_start:top_start + 2500]
        bottom_start = html.find('id="product-actions-bottom"')
        bottom_block = html[bottom_start:bottom_start + 2500]

        # In both top and bottom:
        # 1. Edit remains enabled
        assert 'href="/inventory/products/106/edit"' in top_block
        assert 'href="/inventory/products/106/edit"' in bottom_block

        # 2. Sell is disabled
        assert '<button class="btn" disabled' in top_block
        assert 'Продажа недоступна' in top_block
        assert '<button class="btn" disabled' in bottom_block
        assert 'Продажа недоступна' in bottom_block

        # 3. Add to cart is disabled
        assert 'Добавление в корзину недоступно' in top_block
        assert 'Добавление в корзину недоступно' in bottom_block

        # 4. Price tag is disabled
        assert 'Ценник доступен только для товаров в наличии' in top_block
        assert 'Ценник доступен только для товаров в наличии' in bottom_block


def test_product_detail_cart_membership_synchronization_top_and_bottom():
    """
    Verify that when product is in cart, both top and bottom bars display
    the 'Перейти в корзину' button and the item counter.
    """
    mock_product = {
        "id": 107,
        "title": "Клавиатура Logitech G Pro",
        "sale_price": 4500.0,
        "price": 4500.0,
        "quantity": 3,
        "status": "in_stock",
        "storage_location": "store",
        "sku": "KEYBOARD-107"
    }

    with patch.object(core_client, "get_product", new_callable=AsyncMock) as mock_prod, \
         patch.object(core_client, "get_product_details", new_callable=AsyncMock) as mock_details:
        mock_prod.return_value = mock_product
        mock_details.return_value = mock_product

        # Add item to session cart
        res_add = client.post("/cart/add", data={"product_id": 107, "quantity": 2})
        assert res_add.status_code in [200, 302, 303]

        res = client.get("/products/107")
        assert res.status_code == 200
        html = res.text

        top_start = html.find('id="product-actions-top"')
        top_block = html[top_start:top_start + 2500]
        bottom_start = html.find('id="product-actions-bottom"')
        bottom_block = html[bottom_start:bottom_start + 2500]

        # Top toolbar has visible cart link and count 2
        assert 'class="btn btn-success product-go-to-cart"' in top_block
        assert 'display: none;' not in top_block.split('class="btn btn-success product-go-to-cart"')[1].split('>')[0]
        assert '<span class="product-cart-quantity-value">2</span>' in top_block

        # Bottom toolbar has visible cart link and count 2
        assert 'class="btn btn-success product-go-to-cart"' in bottom_block
        assert 'display: none;' not in bottom_block.split('class="btn btn-success product-go-to-cart"')[1].split('>')[0]
        assert '<span class="product-cart-quantity-value">2</span>' in bottom_block
