from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extension_my_listings_ingest():
    """Verify receiving discovery list of own listings without polluting live DB."""
    gen_res = client.post("/extension/api/pairing/generate")
    token = client.post("/extension/api/pairing/pair", json={"pair_code": gen_res.json()["pair_code"]}).json()["extension_token"]

    payload = {
        "schema_version": 1,
        "extension_version": "0.1.0",
        "captured_at": "2026-08-12T12:00:00Z",
        "page_type": "my_listings",
        "listings_count": 2,
        "items": [
            {"external_item_id": "111", "external_url": "https://www.avito.ru/item_111", "title": "Товар 1", "price": 1000},
            {"external_item_id": "222", "external_url": "https://www.avito.ru/item_222", "title": "Товар 2", "price": 2000}
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "created", "product_id": 999}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = client.post("/extension/api/my-listings", headers={"X-Extension-Token": token}, json=payload)
        assert res.status_code == 200
        assert res.json()["count"] == 2

