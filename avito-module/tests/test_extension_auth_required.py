from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extension_endpoints_require_token():
    """Verify heartbeat and listing ingest fail without valid token."""
    res1 = client.post("/extension/api/heartbeat")
    assert res1.status_code == 401

    res2 = client.post("/extension/api/listing", json={"schema_version": 1, "captured_at": "2026-08-12T12:00:00Z", "listing": {}})
    assert res2.status_code == 401
