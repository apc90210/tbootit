import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import ParsedAd
from app import storage
import app.routers.exports as exports

client = TestClient(app)

@pytest.fixture
def mock_parsed_ad():
    ad = ParsedAd(
        id="test-ad-1",
        run_id="run",
        source_url="http",
        title="Test",
        parse_status="parsed",
        created_at="now"
    )
    storage.save_parsed_ad(ad)
    return ad

class DummyCoreClient:
    async def validate_product_card(self, card):
        return {"valid": True, "warnings": []}

def test_core_import_preview(mock_parsed_ad, monkeypatch):
    monkeypatch.setattr(exports, "core_client", DummyCoreClient())
    
    response = client.post(f"/api/avito/parsed-ads/{mock_parsed_ad.id}/core-import-preview")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "preview_done"
    assert data["core_validation"]["valid"] is True
