import os
import base64
from unittest.mock import patch
import pytest
from app import models
from app.config import settings
from app.storage import check_persistent_photo_storage, get_product_photos_dir

def test_persistent_photo_storage_probe_success():
    """Verify check_persistent_photo_storage succeeds in standard environment."""
    ok, err = check_persistent_photo_storage()
    assert ok is True
    assert err == ""
    assert os.path.isdir(get_product_photos_dir())

def test_persistent_photo_storage_probe_failure():
    """Verify check_persistent_photo_storage returns False on disk error."""
    with patch("os.makedirs", side_effect=PermissionError("Permission denied")):
        ok, err = check_persistent_photo_storage()
        assert ok is False
        assert "Cannot create or access" in err

def test_avito_photo_import_persistent_storage_available(client, db_session):
    """
    TEST A: Normal persistent storage available:
    - Photo saved to canonical /data/storage/product_photos
    - photos_imported is 1
    - File physically exists and is served
    """
    photo_data = b"VALID_IMAGE_DATA_PERSISTENT_001"
    b64_str = base64.b64encode(photo_data).decode("utf-8")

    payload = {
        "account_key": "account_office",
        "external_item_id": "999888111",
        "title": "Монитор Dell 24",
        "price": 12000.0,
        "photos": [
            {"url": "https://img.avito.st/image/1/testphoto01.jpg", "content_base64": b64_str}
        ]
    }

    res = client.post("/api/integrations/avito/import-item", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["photos_imported"] == 1
    assert data["warnings"] == []

    prod_id = data["product_id"]
    photo = db_session.query(models.ProductPhoto).filter(models.ProductPhoto.product_id == prod_id).first()
    assert photo is not None
    assert photo.storage_path is not None
    assert photo.storage_path.startswith(get_product_photos_dir())
    assert os.path.isfile(photo.storage_path)
    assert os.path.getsize(photo.storage_path) == len(photo_data)
    assert photo.media_url.startswith("/media/product_photos/")

def test_avito_photo_import_storage_unavailable_no_tmp_fallback(client, db_session):
    """
    TEST B: Simulated persistent storage unavailable:
    - No /tmp/product_photos fallback
    - No false local storage_path
    - photos_imported is 0
    - Response includes explicit safe warning
    - No HTTP 500
    """
    photo_data = b"VALID_IMAGE_DATA_PERSISTENT_002"
    b64_str = base64.b64encode(photo_data).decode("utf-8")

    payload = {
        "account_key": "account_office",
        "external_item_id": "999888222",
        "title": "Клавиатура Logitech",
        "price": 3500.0,
        "photos": [
            {"url": "https://img.avito.st/image/1/testphoto02.jpg", "content_base64": b64_str}
        ]
    }

    with patch("app.routers.integrations.check_persistent_photo_storage", return_value=(False, "Simulated disk outage")):
        res = client.post("/api/integrations/avito/import-item", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ("created", "updated")
        assert data["photos_imported"] == 0
        assert len(data["warnings"]) > 0
        assert "Persistent photo storage unavailable" in data["warnings"][0]

        prod_id = data["product_id"]
        photo = db_session.query(models.ProductPhoto).filter(models.ProductPhoto.product_id == prod_id).first()
        assert photo is not None
        # MUST NOT have fake storage_path or /tmp path!
        assert photo.storage_path is None
        assert photo.media_url == "https://img.avito.st/image/1/testphoto02.jpg"

        # Verify nothing was written to /tmp/product_photos
        if os.path.exists("/tmp/product_photos"):
            assert len(os.listdir("/tmp/product_photos")) == 0

def test_avito_photo_import_remote_only_not_counted_as_imported(client, db_session):
    """
    Verify that photo with URL only and no byte content is NOT reported as photos_imported.
    """
    payload = {
        "account_key": "account_office",
        "external_item_id": "999888333",
        "title": "Мышь SteelSeries",
        "price": 2500.0,
        "photos": [
            {"url": "https://img.avito.st/image/1/remote_only_03.jpg"}
        ]
    }

    with patch("app.routers.integrations.fetch_remote_image_bytes", return_value=None):
        res = client.post("/api/integrations/avito/import-item", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["photos_imported"] == 0
        assert any("no byte content" in w for w in data["warnings"])

        prod_id = data["product_id"]
        photo = db_session.query(models.ProductPhoto).filter(models.ProductPhoto.product_id == prod_id).first()
        assert photo is not None
        assert photo.storage_path is None
        assert photo.media_url == "https://img.avito.st/image/1/remote_only_03.jpg"
