import pytest
from app import storage, schemas
from app.browser_worker import AvitoBrowserWorker

def test_same_profile_user_data_dir_used_for_worker_and_session():
    p = schemas.AvitoAccountProfile(account_key="profile_reuse_check", display_name="Reuse Check")
    storage.save_profile(p)

    worker = AvitoBrowserWorker("profile_reuse_check")
    from app.config import settings
    import os
    expected_path = os.path.join(settings.AVITO_STORAGE_DIR, "profiles", "profile_reuse_check", "browser_data")
    
    assert worker.profile_dir == expected_path

    storage.delete_profile("profile_reuse_check")
