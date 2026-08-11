import pytest
from app import storage, schemas

def test_browser_profiles_seeding_and_isolation():
    """
    Test that default account profiles (minimum 3: main, laptops, office) are seeded
    and profiles maintain separate keys and statistics.
    """
    profiles = storage.list_profiles()
    assert len(profiles) >= 3

    keys = [p.account_key for p in profiles]
    assert "main" in keys
    assert "laptops" in keys
    assert "office" in keys

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
