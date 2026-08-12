from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extension_invalid_or_used_pair_code():
    """Verify invalid or re-used pair code returns 400."""
    res = client.post("/extension/api/pairing/pair", json={"pair_code": "000000"})
    assert res.status_code == 400
    assert "не найден" in res.json()["detail"]
