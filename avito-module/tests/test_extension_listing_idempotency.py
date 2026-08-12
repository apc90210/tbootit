from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("app.services.import_service.import_ad_to_core")
def test_extension_listing_idempotency(mock_import):
    """Verify repeated ingest calls import_ad_to_core idempotently."""
    mock_import.return_value = {"status": "created", "product_id": "prod_123"}

    gen_res = client.post("/extension/api/pairing/generate")
    token = client.post("/extension/api/pairing/pair", json={"pair_code": gen_res.json()["pair_code"]}).json()["extension_token"]

    payload = {
        "schema_version": 1,
        "captured_at": "2026-08-12T12:00:00Z",
        "listing": {
            "external_item_id": "3948271049",
            "external_url": "https://www.avito.ru/moskva/videokarta_3948271049",
            "title": "Видеокарта RTX 3060",
            "price": 26500,
            "description": "Тест"
        }
    }

    res1 = client.post("/extension/api/listing", headers={"X-Extension-Token": token}, json=payload)
    assert res1.status_code == 200
    assert res1.json()["status"] == "success"

    mock_import.return_value = {"status": "updated", "product_id": "prod_123"}
    res2 = client.post("/extension/api/listing", headers={"X-Extension-Token": token}, json=payload)
    assert res2.status_code == 200
    assert res2.json()["status"] == "success"
