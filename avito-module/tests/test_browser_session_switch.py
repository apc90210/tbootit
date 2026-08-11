import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app import storage, schemas
from app.browser_worker import browser_session_manager

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_profiles():
    p1 = schemas.AvitoAccountProfile(account_key="acc1", display_name="Тестовый аккаунт 1")
    p2 = schemas.AvitoAccountProfile(account_key="acc2", display_name="Тестовый аккаунт 2")
    storage.save_profile(p1)
    storage.save_profile(p2)
    yield
    asyncio.run(browser_session_manager.stop_session())
    storage.delete_profile("acc1")
    storage.delete_profile("acc2")

@pytest.mark.asyncio
async def test_single_active_browser_enforcement():
    # Mock active session for acc1
    browser_session_manager.active_account_key = "acc1"
    browser_session_manager.active_display_name = "Тестовый аккаунт 1"
    browser_session_manager.context = object()  # dummy context

    # Attempt launching acc2
    success, msg = await browser_session_manager.launch_session("acc2", "Тестовый аккаунт 2")
    assert success is False
    assert "Сейчас открыт браузер аккаунта <Тестовый аккаунт 1>" in msg
