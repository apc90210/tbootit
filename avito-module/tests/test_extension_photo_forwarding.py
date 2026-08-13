import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_extension_photo_forwarding_preserves_position(mock_post):
    """Verify import_service forwards photo URLs with explicit position to Core API."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "updated",
        "product_id": 58,
        "external_listing_id": 2,
        "photos_imported": 2
    }
    mock_post.return_value = mock_resp

    gen = client.post("/extension/api/pairing/generate").json()
    pair = client.post("/extension/api/pairing/pair", json={"pair_code": gen["pair_code"]}).json()
    token = pair["extension_token"]

    payload = {
        "schema_version": 1,
        "extension_version": "0.1.4",
        "captured_at": "2026-08-13T11:00:00Z",
        "page_type": "listing",
        "listing": {
            "external_item_id": "8313765236",
            "external_url": "https://www.avito.ru/item/8313765236",
            "title": "Принтер HP M252N",
            "price": 6900,
            "photos": [
                {"url": "https://10.img.avito.st/image/1/1.main.jpg", "position": 0},
                {"url": "https://10.img.avito.st/image/1/1.sub.jpg", "position": 1}
            ]
        }
    }

    res = client.post("/extension/api/listing", json=payload, headers={"X-Extension-Token": token})
    assert res.status_code == 200
    assert mock_post.called
    core_payload = mock_post.call_args[1]["json"]
    assert "photos" in core_payload
    assert len(core_payload["photos"]) == 2
    assert core_payload["photos"][0]["position"] == 0
    assert core_payload["photos"][1]["position"] == 1
