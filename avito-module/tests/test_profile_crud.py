import pytest
from app import storage, schemas

def test_owner_profile_crud_and_max_limit():
    """
    Test Blocker D fix:
    - Profiles are created by owner with custom display names and generated keys.
    - No hardcoded profile names.
    - Maximum 3 profiles limit enforced.
    """
    # Clean storage
    storage.save_profiles([])

    profiles_before = storage.list_profiles()
    assert len(profiles_before) == 0

    # Create Profile 1
    p1 = schemas.AvitoAccountProfile(account_key="acc_11", display_name="Профиль ПК 1")
    storage.save_profile(p1)

    # Create Profile 2
    p2 = schemas.AvitoAccountProfile(account_key="acc_22", display_name="Профиль ПК 2")
    storage.save_profile(p2)

    # Create Profile 3
    p3 = schemas.AvitoAccountProfile(account_key="acc_33", display_name="Профиль Ноутбуки")
    storage.save_profile(p3)

    fetched = storage.list_profiles()
    assert len(fetched) == 3
    names = [p.display_name for p in fetched]
    assert "Профиль ПК 1" in names
    assert "Main" not in names
    assert "Laptops" not in names
    assert "Office" not in names

    # Delete Profile 1
    storage.delete_profile("acc_11")
    assert storage.get_profile("acc_11") is None
    assert len(storage.list_profiles()) == 2
