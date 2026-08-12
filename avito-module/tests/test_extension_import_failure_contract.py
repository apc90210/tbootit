import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_extension_import_failure_returns_422(mock_post):
    """Verify failed Core API import returns HTTP 422 with status=failed and product_id=None."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Core Error"
    mock_post.return_value = mock_resp

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
            "external_url": "https://www.avito.ru/item/8313765236",
            "title": "Принтер HP",
            "price": 7099
        }
    }

    res = client.post("/extension/api/listing", json=payload, headers={"X-Extension-Token": token})
    assert res.status_code == 422
    detail = res.json()["detail"]
    assert detail["status"] == "failed"
    assert detail["product_id"] is None
    assert detail["error_code"] == "CORE_IMPORT_FAILED"
