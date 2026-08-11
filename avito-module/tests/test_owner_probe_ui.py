import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app import storage, schemas

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_profile():
    p = schemas.AvitoAccountProfile(account_key="acc_probe", display_name="Пробный профиль")
    storage.save_profile(p)
    yield
    storage.delete_profile("acc_probe")

@patch("app.browser_worker.AvitoBrowserWorker.discover_my_listings")
def test_discover_listings(mock_disc):
    mock_disc.return_value = [{
        "external_item_id": "12345678",
        "external_url": "https://www.avito.ru/item/12345678",
        "remote_status": "active",
        "title": "Ноутбук Lenovo",
        "price": 25000.0
    }]

    res = client.get("/accounts/api/profiles/acc_probe/discover")
    assert res.status_code == 200
    assert res.json()["listings_found"] == 1
    assert res.json()["items"][0]["external_item_id"] == "12345678"

@patch("app.browser_worker.AvitoBrowserWorker.extract_item_card")
def test_preview_listing(mock_card):
    mock_card.return_value = {
        "title": "Ноутбук Lenovo",
        "price": 25000.0,
        "description": "Тестовое описание",
        "photos": [{"url": "http://img.avito.ru/1.jpg"}]
    }

    res = client.get("/accounts/api/profiles/acc_probe/preview/12345678")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Ноутбук Lenovo"
    assert data["photo_count"] == 1

def test_full_import_gate_before_verification():
    # Full import without probe verification or allow_full should be 403 Forbidden
    res = client.post("/accounts/api/profiles/acc_probe/import", data={"scope": "all"})
    assert res.status_code == 403
    assert "FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED" in res.json()["detail"]

def test_verify_probe_endpoint():
    res = client.post("/accounts/api/profiles/acc_probe/verify-probe")
    assert res.status_code == 200
    assert res.json()["probe_verified"] is True

    prof = storage.get_profile("acc_probe")
    assert prof.probe_verified is True
