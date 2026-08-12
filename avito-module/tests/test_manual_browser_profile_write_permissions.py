import os
import pytest
from app import storage
from app.config import settings

def test_manual_browser_profile_directory_writable():
    """Verify browser profile data directory is writable."""
    account_key = "acc_test_writable"
    profile_dir = os.path.join(settings.AVITO_STORAGE_DIR, "profiles", account_key, "browser_data")
    os.makedirs(profile_dir, exist_ok=True)
    try:
        test_file = os.path.join(profile_dir, "test_perm.tmp")
        with open(test_file, "w") as f:
            f.write("write_ok")
        assert os.path.exists(test_file)
        os.remove(test_file)
    finally:
        storage.delete_profile(account_key)
