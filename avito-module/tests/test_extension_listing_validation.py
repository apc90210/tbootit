from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extension_listing_validation_invalid_payload():
    """Verify invalid payloads (missing item_id or non-avito URL) are rejected."""
    gen_res = client.post("/extension/api/pairing/generate")
    code = gen_res.json()["pair_code"]
    pair_res = client.post("/extension/api/pairing/pair", json={"pair_code": code})
    token = pair_res.json()["extension_token"]

    # Missing ID
    res1 = client.post("/extension/api/listing", headers={"X-Extension-Token": token}, json={
        "schema_version": 1,
        "captured_at": "2026-08-12T12:00:00Z",
        "listing": {"external_url": "https://www.avito.ru/item_123", "title": "Test"}
    })
    assert res1.status_code == 400
    assert "external_item_id" in res1.json()["detail"]

    # Non-avito URL
    res2 = client.post("/extension/api/listing", headers={"X-Extension-Token": token}, json={
        "schema_version": 1,
        "captured_at": "2026-08-12T12:00:00Z",
        "listing": {"external_item_id": "123456", "external_url": "https://google.com", "title": "Test"}
    })
    assert res2.status_code == 400
    assert "avito.ru" in res2.json()["detail"]
