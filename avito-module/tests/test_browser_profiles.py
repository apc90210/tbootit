import pytest
from app import storage, schemas

def test_browser_profiles_seeding_and_isolation():
    """
    Test user-defined profile creation and profile storage isolation.
    """
    p1 = schemas.AvitoAccountProfile(account_key="acc_1", display_name="Профиль 1")
    storage.save_profile(p1)
    p2 = schemas.AvitoAccountProfile(account_key="acc_2", display_name="Профиль 2")
    storage.save_profile(p2)

    profiles = storage.list_profiles()
    assert len(profiles) >= 2


    # Add a custom profile
    new_profile = schemas.AvitoAccountProfile(
        account_key="custom_test",
        display_name="Avito — Тестовый"
    )
    storage.save_profile(new_profile)

    fetched = storage.get_profile("custom_test")
    assert fetched is not None
    assert fetched.display_name == "Avito — Тестовый"

    # Cleanup
    storage.delete_profile("custom_test")
    assert storage.get_profile("custom_test") is None
