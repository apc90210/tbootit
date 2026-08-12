from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_last_ingest_endpoint_returns_json():
    """Verify GET /extension/api/last-ingest returns last ingest status dictionary."""
    res = client.get("/extension/api/last-ingest")
    assert res.status_code == 200
    assert isinstance(res.json(), dict)
