import os
import pytest
from app import storage
from app.config import settings

def test_stale_profile_recovery_does_not_delete():
    """Verify stale profile directory recovery preserves existing profiles."""
    test_key = "acc_stale_recovery"
    dir_path = os.path.join(settings.AVITO_STORAGE_DIR, "profiles", test_key, "browser_data")
    os.makedirs(dir_path, exist_ok=True)
    
    try:
        cookie_file = os.path.join(dir_path, "Cookies")
        with open(cookie_file, "w") as f:
            f.write("mock_cookie_db")
            
        storage.reconcile_profile_registry()
        assert os.path.exists(cookie_file)
        assert os.path.getsize(cookie_file) > 0
    finally:
        storage.delete_profile(test_key)
