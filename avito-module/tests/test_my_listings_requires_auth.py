import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import storage, schemas

client = TestClient(app)

def test_my_listings_endpoint_requires_auth():
    p = schemas.AvitoAccountProfile(account_key="test_my_listings", display_name="Test My Listings", auth_status="unauthorized")
    storage.save_profile(p)

    res = client.get("/accounts/api/profiles/test_my_listings/discover")
    assert res.status_code == 409

    storage.delete_profile("test_my_listings")
