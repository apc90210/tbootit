from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extension_rejects_cookie_payload():
    """Verify security check rejects payloads containing cookie/session tokens."""
    gen_res = client.post("/extension/api/pairing/generate")
    token = client.post("/extension/api/pairing/pair", json={"pair_code": gen_res.json()["pair_code"]}).json()["extension_token"]

    payload = {
        "schema_version": 1,
        "captured_at": "2026-08-12T12:00:00Z",
        "listing": {
            "external_item_id": "3948271049",
            "external_url": "https://www.avito.ru/item_3948271049",
            "title": "Тест",
            "cookie_data": "sessionid=xyz123"
        }
    }

    res = client.post("/extension/api/listing", headers={"X-Extension-Token": token}, json=payload)
    assert res.status_code == 400
    assert "запрещённые" in res.json()["detail"]
