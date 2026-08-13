from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

def test_extension_bridge_multi_photo_forwarding():
    """Verify extension bridge accepts multiple photos and preserves order."""
    gen = client.post("/extension/api/pairing/generate").json()
    pair = client.post("/extension/api/pairing/pair", json={"pair_code": gen["pair_code"]}).json()
    token = pair["extension_token"]

    payload = {
        "schema_version": 1,
        "extension_version": "0.1.5",
        "captured_at": "2026-08-13T10:00:00Z",
        "page_type": "listing",
        "listing": {
            "external_item_id": "9999888877",
            "external_url": "https://www.avito.ru/items/9999888877",
            "title": "Тестовый товар с 3 фото",
            "price": 5000.0,
            "description": "Описание товара с 3 фото",
            "photos": [
                {"url": "https://80.img.avito.st/image/1/1280x960/photo1.jpg", "position": 0},
                {"url": "https://80.img.avito.st/image/1/1280x960/photo2.jpg", "position": 1},
                {"url": "https://80.img.avito.st/image/1/1280x960/photo3.jpg", "position": 2}
            ]
        }
    }

    mock_core_resp = {
        "status": "updated",
        "product_id": 99,
        "photos_imported": 3,
        "photos": [
            {"id": 1, "product_id": 99, "filename": "99_p1.jpg", "sort_order": 0},
            {"id": 2, "product_id": 99, "filename": "99_p2.jpg", "sort_order": 1},
            {"id": 3, "product_id": 99, "filename": "99_p3.jpg", "sort_order": 2}
        ]
    }

    with patch("app.services.import_service.import_ad_to_core", new_callable=AsyncMock) as mock_import:
        mock_import.return_value = mock_core_resp

        headers = {"X-Extension-Token": token}
        res = client.post("/extension/api/listing", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["product_id"] == 99
        assert data["photos_received"] == 3
        assert data["photos_imported"] == 3
