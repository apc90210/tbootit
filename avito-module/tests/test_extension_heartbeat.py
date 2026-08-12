from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extension_heartbeat():
    """Verify heartbeat succeeds with valid paired token."""
    gen_res = client.post("/extension/api/pairing/generate")
    code = gen_res.json()["pair_code"]
    pair_res = client.post("/extension/api/pairing/pair", json={"pair_code": code})
    token = pair_res.json()["extension_token"]

    hb_res = client.post("/extension/api/heartbeat", headers={"X-Extension-Token": token})
    assert hb_res.status_code == 200
    assert hb_res.json()["status"] == "ok"
