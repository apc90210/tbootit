from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_bridge_status_unpaired_without_header():
    """Verify /status endpoint returns paired=False when no header or invalid token is supplied."""
    res1 = client.get("/extension/api/status")
    assert res1.status_code == 200
    assert res1.json()["paired"] is False

    res2 = client.get("/extension/api/status", headers={"X-Extension-Token": "invalid_token"})
    assert res2.status_code == 200
    assert res2.json()["paired"] is False
