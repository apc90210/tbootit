import os
import pytest
from app import storage, schemas

def test_profile_persistence_on_disk():
    """
    Test that profile data and statistics persist on disk.
    """
    p = schemas.AvitoAccountProfile(account_key="persisted_key_99", display_name="Спец Профиль")
    p.stats.imported = 5
    storage.save_profile(p)

    re_fetched = storage.get_profile("persisted_key_99")
    assert re_fetched is not None
    assert re_fetched.display_name == "Спец Профиль"
    assert re_fetched.stats.imported == 5

    # Cleanup
    storage.delete_profile("persisted_key_99")
