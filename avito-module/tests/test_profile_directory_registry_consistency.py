import os
import shutil
import pytest
from app import storage
from app.config import settings

def test_directory_registry_reconciliation():
    """Verify disk directory profiles/acc_test_reconcile is auto-recovered into profile registry."""
    test_key = "acc_test_reconcile"
    dir_path = os.path.join(settings.AVITO_STORAGE_DIR, "profiles", test_key, "browser_data")
    os.makedirs(dir_path, exist_ok=True)
    
    try:
        profiles = storage.reconcile_profile_registry()
        found = any(p.account_key == test_key for p in profiles)
        assert found is True
    finally:
        storage.delete_profile(test_key)
