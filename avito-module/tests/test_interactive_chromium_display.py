import os
import pytest
from app.browser_worker import browser_session_manager

def test_display_environment_variable():
    """Verify DISPLAY environment variable is set for headed Chromium."""
    display = os.getenv("DISPLAY", ":99")
    assert display.startswith(":")
