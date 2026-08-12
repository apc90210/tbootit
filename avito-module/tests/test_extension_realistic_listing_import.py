import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_extension_realistic_listing_import_contract(mock_post):
    """Verify extension ingests realistic owner listing fixture and forwards to Core API import-item endpoint."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "created",
        "product_id": 83137,
        "external_listing_id": 9901,
        "photos_imported": 1
    }
    mock_post.return_value = mock_resp

    # Generate and pair token
    gen = client.post("/extension/api/pairing/generate").json()
    pair = client.post("/extension/api/pairing/pair", json={"pair_code": gen["pair_code"]}).json()
    token = pair["extension_token"]

    payload = {
        "schema_version": 1,
        "extension_version": "0.1.3",
        "captured_at": "2026-08-12T13:20:00Z",
        "page_type": "listing",
        "listing": {
            "external_item_id": "8313765236",
            "external_url": "https://www.avito.ru/moskva/orgtehnika_i_rashodniki/lazernyy_tsvetnoy_printer_hp_m252n_na_zapchasti_8313765236",
            "title": "Лазерный цветной принтер hp m252n на запчасти",
            "price": 7099,
            "description": "Принтер HP M252N на запчасти.",
            "category": "Оргтехника",
            "characteristics": {"Состояние": "Б/у"},
            "photos": ["https://80.img.avito.st/image/1/1.xyz"]
        }
    }

    res = client.post("/extension/api/listing", json=payload, headers={"X-Extension-Token": token})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["product_id"] == 83137
    assert data["result"] == "created"
    assert "8313765236" in data["message"]
