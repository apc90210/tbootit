import os
import pytest
from app import storage
from app.schemas import AvitoAccountProfile

def test_reconcile_profile_registry_returns_list():
    """Verify reconcile_profile_registry returns a list of profiles."""
    profiles = storage.reconcile_profile_registry()
    assert isinstance(profiles, list)
