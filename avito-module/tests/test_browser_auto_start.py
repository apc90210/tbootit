import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app import storage, schemas

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_profile():
    p = schemas.AvitoAccountProfile(account_key="test_acc", display_name="Тестовый аккаунт")
    storage.save_profile(p)
    yield
    storage.delete_profile("test_acc")

def test_browser_status_endpoint():
    res = client.get("/accounts/api/profiles/test_acc/browser-status")
    assert res.status_code == 200
    data = res.json()
    assert "active" in data
    assert "status_text" in data

@patch("app.browser_worker.browser_session_manager.launch_session")
def test_launch_browser_endpoint(mock_launch):
    mock_launch.return_value = (True, "Браузер успешно запущен.")
    res = client.post("/accounts/api/profiles/test_acc/launch-browser")
    assert res.status_code == 200
    assert res.json()["status"] == "launched"
