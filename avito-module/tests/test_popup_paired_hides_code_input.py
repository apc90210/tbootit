from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_bridge_status_paired_with_valid_header():
    """Verify /status returns paired=True ONLY when valid token header is supplied."""
    gen = client.post("/extension/api/pairing/generate").json()
    pair = client.post("/extension/api/pairing/pair", json={"pair_code": gen["pair_code"]}).json()
    token = pair["extension_token"]

    # Valid token header -> paired: True
    res1 = client.get("/extension/api/status", headers={"X-Extension-Token": token})
    assert res1.status_code == 200
    assert res1.json()["paired"] is True

    # No token header -> paired: False
    res2 = client.get("/extension/api/status")
    assert res2.status_code == 200
    assert res2.json()["paired"] is False
