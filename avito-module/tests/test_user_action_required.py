import pytest
from app import schemas

def test_user_action_required_auth_status_handling():
    p = schemas.AvitoAccountProfile(
        account_key="test_user_action",
        display_name="User Action Test",
        auth_status="user_action_required"
    )
    assert p.auth_status == "user_action_required"
