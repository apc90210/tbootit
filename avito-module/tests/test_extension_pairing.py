from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extension_pairing_flow():
    """Verify code generation and successful pairing."""
    # 1. Generate code
    gen_res = client.post("/extension/api/pairing/generate")
    assert gen_res.status_code == 200
    code = gen_res.json()["pair_code"]
    assert len(code) == 6

    # 2. Pair with code
    pair_res = client.post("/extension/api/pairing/pair", json={"pair_code": code})
    assert pair_res.status_code == 200
    assert pair_res.json()["status"] == "paired"
    token = pair_res.json()["extension_token"]
    assert token.startswith("ext_tok_")

    # 3. Status with token
    status_res = client.get("/extension/api/status", headers={"X-Extension-Token": token})
    assert status_res.status_code == 200
    assert status_res.json()["paired"] is True
