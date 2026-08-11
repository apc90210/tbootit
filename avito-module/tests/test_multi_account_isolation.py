import pytest
from app import storage, schemas

def test_multi_account_isolation():
    """
    Test isolation between multiple account profiles:
    - Profile stats and import runs do not leak across different account keys.
    """
    # Create isolated test profiles
    p_acc1 = schemas.AvitoAccountProfile(account_key="acc_test_1", display_name="Test Acc 1")
    p_acc2 = schemas.AvitoAccountProfile(account_key="acc_test_2", display_name="Test Acc 2")

    storage.save_profile(p_acc1)
    storage.save_profile(p_acc2)

    # Update stats for acc2 only
    p_acc2.stats.imported = 25
    storage.save_profile(p_acc2)

    # Re-fetch both and check isolation
    fetched_acc1 = storage.get_profile("acc_test_1")
    fetched_acc2 = storage.get_profile("acc_test_2")

    assert fetched_acc1.stats.imported == 0
    assert fetched_acc2.stats.imported == 25

    # Clean up
    storage.delete_profile("acc_test_1")
    storage.delete_profile("acc_test_2")
