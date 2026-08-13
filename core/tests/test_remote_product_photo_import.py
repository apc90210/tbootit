import pytest
from unittest.mock import patch, MagicMock
from app import models
from app.routers.integrations import fetch_remote_image_bytes

@patch("app.routers.integrations.fetch_remote_image_bytes")
def test_remote_product_photo_import(mock_fetch, client, db_session):
    """Verify Core downloads remote photo bytes via HTTPS, saves to storage, creates ProductPhoto row."""
    fake_jpg = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01" + b"A" * 500
    mock_fetch.return_value = fake_jpg

    payload = {
        "account_key": "acc_remote_test",
        "external_item_id": "999888777",
        "title": "Remote Photo Test Item",
        "price": 1200.0,
        "photos": [
            {"url": "https://img.avito.st/remote1.jpg", "position": 0}
        ]
    }

    res = client.post("/api/integrations/avito/import-item", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["photos_imported"] == 1

    prod_id = data["product_id"]
    photo_rows = db_session.query(models.ProductPhoto).filter(models.ProductPhoto.product_id == prod_id).all()
    assert len(photo_rows) == 1
    assert photo_rows[0].source_url == "https://img.avito.st/remote1.jpg"
    assert photo_rows[0].sort_order == 0
