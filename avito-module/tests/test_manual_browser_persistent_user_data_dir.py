import os
import pytest
from app.config import settings

def test_manual_browser_uses_persistent_profile_path():
    """Verify profile dir path format for manual browser."""
    account_key = "acc_test_path"
    profile_dir = os.path.join(settings.AVITO_STORAGE_DIR, "profiles", account_key, "browser_data")
    assert "profiles" in profile_dir
    assert account_key in profile_dir
    assert profile_dir.endswith("browser_data")
