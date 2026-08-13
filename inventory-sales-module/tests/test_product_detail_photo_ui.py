from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

def test_product_detail_zero_photos():
    """Verify that a product with 0 photos renders 'Фотографий нет' cleanly."""
    mock_product = {
        "id": 101,
        "title": "Товар без фото",
        "price": 1000.0,
        "sale_price": 1000.0,
        "status": "in_stock",
        "storage_location": "store",
        "quantity": 1,
        "description": "Описание товара без фотографий",
        "photos": []
    }
    with patch("app.routers.products.core_client.get_product_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        res = client.get("/products/101")
        assert res.status_code == 200
        assert "Фотографии" in res.text
        assert "Фотографий нет" in res.text
        assert "<img" not in res.text.split("product-photos-block")[1]


def test_product_detail_one_photo():
    """Verify that a product with 1 photo renders the photo image URL."""
    mock_product = {
        "id": 102,
        "title": "Товар с одним фото",
        "price": 2000.0,
        "sale_price": 2000.0,
        "status": "in_stock",
        "storage_location": "store",
        "quantity": 1,
        "description": "Описание товара с фото",
        "photos": [
            {
                "id": 10,
                "product_id": 102,
                "filename": "102_abc123.jpg",
                "media_url": "/media/product_photos/102_abc123.jpg",
                "sort_order": 0,
                "created_at": "2026-08-13T10:00:00"
            }
        ]
    }
    with patch("app.routers.products.core_client.get_product_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        res = client.get("/products/102")
        assert res.status_code == 200
        assert "Фотографии" in res.text
        assert "1" in res.text
        assert "/media/product_photos/102_abc123.jpg" in res.text
        assert "Главное" in res.text


def test_product_detail_multiple_photos_preserve_order():
    """Verify that multiple photos render in sort_order sequence with main photo marked."""
    mock_product = {
        "id": 103,
        "title": "Товар с несколькими фото",
        "price": 3000.0,
        "sale_price": 3000.0,
        "status": "in_stock",
        "storage_location": "store",
        "quantity": 1,
        "description": "Галерея из 3 фото",
        "photos": [
            {
                "id": 11,
                "product_id": 103,
                "filename": "103_main.jpg",
                "media_url": "/media/product_photos/103_main.jpg",
                "sort_order": 0,
                "created_at": "2026-08-13T10:00:00"
            },
            {
                "id": 12,
                "product_id": 103,
                "filename": "103_second.jpg",
                "media_url": "/media/product_photos/103_second.jpg",
                "sort_order": 1,
                "created_at": "2026-08-13T10:01:00"
            },
            {
                "id": 13,
                "product_id": 103,
                "filename": "103_third.jpg",
                "media_url": "/media/product_photos/103_third.jpg",
                "sort_order": 2,
                "created_at": "2026-08-13T10:02:00"
            }
        ]
    }
    with patch("app.routers.products.core_client.get_product_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        res = client.get("/products/103")
        assert res.status_code == 200
        assert "103_main.jpg" in res.text
        assert "103_second.jpg" in res.text
        assert "103_third.jpg" in res.text
        # Verify order of URLs in HTML response
        idx1 = res.text.find("103_main.jpg")
        idx2 = res.text.find("103_second.jpg")
        idx3 = res.text.find("103_third.jpg")
        assert idx1 < idx2 < idx3
