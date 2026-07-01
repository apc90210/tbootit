import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import ParsedAd
from app import storage
import httpx
from unittest.mock import AsyncMock, patch

client = TestClient(app)

@pytest.fixture
def mock_parsed_ad():
    ad = ParsedAd(
        id="mock-ad-123",
        run_id="mock-run-123",
        source="avito",
        source_url="https://avito.ru/item-123",
        title="Mock Item",
        price=100.0,
        currency="RUB",
        parse_status="success",
        created_at="2026-07-01T10:00:00Z"
    )
    storage.save_parsed_ad(ad)
    yield ad
    # cleanup
    import os
    try:
        os.remove(os.path.join(storage._get_ads_dir(), "mock-ad-123.json"))
        os.remove(os.path.join(storage._get_ads_dir(), "mock-ad-123_import.json"))
    except:
        pass

@pytest.mark.asyncio
async def test_import_status_not_imported(mock_parsed_ad):
    response = client.get(f"/api/avito/parsed-ads/{mock_parsed_ad.id}/core-import-status")
    assert response.status_code == 200
    assert response.json() == {"status": "not_imported"}

@pytest.mark.asyncio
@patch("app.core_client.import_product_card", new_callable=AsyncMock)
async def test_core_import_success(mock_import, mock_parsed_ad):
    mock_import.return_value = {"status": "imported", "product_id": 1, "sku": "AVITO-123"}
    
    response = client.post(f"/api/avito/parsed-ads/{mock_parsed_ad.id}/core-import", json={"force": False})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "imported"
    assert data["core_response"]["product_id"] == 1
    
    # Check status endpoint
    status_resp = client.get(f"/api/avito/parsed-ads/{mock_parsed_ad.id}/core-import-status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "imported"

@pytest.mark.asyncio
@patch("app.core_client.import_product_card", new_callable=AsyncMock)
async def test_core_import_idempotent(mock_import, mock_parsed_ad):
    mock_import.return_value = {"status": "imported", "product_id": 1}
    
    # First import
    client.post(f"/api/avito/parsed-ads/{mock_parsed_ad.id}/core-import", json={"force": False})
    
    # Second import without force
    response = client.post(f"/api/avito/parsed-ads/{mock_parsed_ad.id}/core-import", json={"force": False})
    assert response.status_code == 200
    assert response.json()["status"] == "already_imported"
    
    # Second import with force
    mock_import.return_value = {"status": "updated", "product_id": 1}
    response_force = client.post(f"/api/avito/parsed-ads/{mock_parsed_ad.id}/core-import", json={"force": True})
    assert response_force.status_code == 200
    assert response_force.json()["status"] == "imported"
