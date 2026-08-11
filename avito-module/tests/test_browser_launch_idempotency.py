import pytest
from app.browser_worker import browser_session_manager

def test_session_manager_status_default():
    """Verify default session status is inactive."""
    status = browser_session_manager.get_status()
    assert isinstance(status, dict)
    assert "active" in status
    assert "status_text" in status
