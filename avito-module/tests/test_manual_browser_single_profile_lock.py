import pytest
from app.browser_worker import browser_session_manager

@pytest.mark.asyncio
async def test_manual_browser_prevents_concurrent_profiles():
    """Verify launch_session rejects opening second profile while one is active."""
    browser_session_manager.active_account_key = "acc_1"
    browser_session_manager.active_display_name = "Account 1"
    
    # Fake a running process object
    class FakeProc:
        def poll(self): return None
    browser_session_manager.manual_process = FakeProc()
    
    success, msg = await browser_session_manager.launch_session("acc_2")
    assert success is False
    assert "Закройте его или переключитесь" in msg
    
    # Cleanup
    browser_session_manager.manual_process = None
    browser_session_manager.active_account_key = None
