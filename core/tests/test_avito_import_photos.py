import pytest
import base64
from app import models

def test_avito_photo_import_deduplication(client, db_session):
    """
    Test idempotent photo import:
    - Photos with same base64 content or source URL are NOT duplicated on subsequent imports
    - SHA256 content_hash is generated and stored
    """
    photo_data = b"FAKE_PHOTO_JPEG_BYTES_12345"
    b64_str = base64.b64encode(photo_data).decode("utf-8")

    payload1 = {
        "account_key": "account_office",
        "external_item_id": "555444333",
        "title": "Принтер HP LaserJet",
        "price": 8000.0,
        "photos": [
            {"url": "https://img.avito.st/1.jpg", "content_base64": b64_str}
        ]
    }

    res1 = client.post("/api/integrations/avito/import-item", json=payload1)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["photos_imported"] == 1
    assert data1["photos_skipped"] == 0

    # Re-import same item with same photo
    res2 = client.post("/api/integrations/avito/import-item", json=payload1)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["photos_imported"] == 0
    assert data2["photos_skipped"] == 1

    # Verify photos count in DB
    prod_id = data1["product_id"]
    photos = db_session.query(models.ProductPhoto).filter(models.ProductPhoto.product_id == prod_id).all()
    assert len(photos) == 1
    assert photos[0].content_hash is not None
