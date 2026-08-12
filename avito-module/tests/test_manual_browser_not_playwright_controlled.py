import pytest
from app.browser_worker import browser_session_manager

@pytest.mark.asyncio
async def test_manual_browser_session_uses_subprocess():
    """Verify manual browser manager does not attach Playwright context."""
    assert browser_session_manager.manual_process is None
    status = browser_session_manager.get_status("acc_test")
    assert status["session_mode"] is None
