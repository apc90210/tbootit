import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import ParsedAd
from app import storage
import app.routers.exports as exports

client = TestClient(app)

ad = ParsedAd(
    id="test-ad-1",
    run_id="run",
    source_url="http",
    title="Test",
    parse_status="parsed",
    created_at="now"
)
storage.save_parsed_ad(ad)

class DummyCoreClient:
    async def validate_product_card(self, card):
        return {"valid": True, "warnings": []}

exports.core_client = DummyCoreClient()

response = client.post(f"/api/avito/parsed-ads/{ad.id}/core-import-preview")
print("STATUS:", response.status_code)
print("BODY:", response.text)
