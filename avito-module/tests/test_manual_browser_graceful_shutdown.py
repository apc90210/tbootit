import pytest
from app.browser_worker import browser_session_manager

@pytest.mark.asyncio
async def test_manual_browser_graceful_shutdown():
    """Verify stop_session cleanly terminates active process."""
    await browser_session_manager.stop_session()
    assert browser_session_manager.manual_process is None
    assert browser_session_manager.session_mode is None
