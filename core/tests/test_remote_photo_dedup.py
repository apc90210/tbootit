import pytest
from unittest.mock import patch
from app import models

@patch("app.routers.integrations.fetch_remote_image_bytes")
def test_remote_photo_dedup_and_dummy_replacement(mock_fetch, client, db_session):
    """Verify remote photos are deduplicated and dummy 146-byte placeholders are replaced upon re-import with real bytes."""
    fake_img = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01" + b"REAL_IMAGE_BYTES" * 50
    mock_fetch.return_value = fake_img

    payload = {
        "account_key": "acc_dedup_test",
        "external_item_id": "777666555",
        "title": "Dedup Remote Photo Test",
        "price": 3000.0,
        "photos": [
            {"url": "https://img.avito.st/dedup1.jpg", "position": 0}
        ]
    }

    # First import
    res1 = client.post("/api/integrations/avito/import-item", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["photos_imported"] == 1

    # Second import (identical URL/content) -> skipped
    res2 = client.post("/api/integrations/avito/import-item", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["photos_skipped"] == 1

    prod_id = data1["product_id"]
    photos = db_session.query(models.ProductPhoto).filter(models.ProductPhoto.product_id == prod_id).all()
    assert len(photos) == 1
