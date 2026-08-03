import pytest
import os
import glob

def test_repairs_security_no_password_fields_in_schemas():
    from app import schemas
    # Check that schema fields do not contain password/pin/unlock_code/secret
    forbidden_terms = ["password", "device_password", "pin", "pin_code", "unlock_code", "graphic_key"]
    for field in schemas.RepairOrderBase.model_fields.keys():
        for term in forbidden_terms:
            assert term not in field.lower(), f"Forbidden field term '{term}' found in RepairOrderBase field '{field}'"

def test_access_code_provided_is_boolean_only():
    from app import schemas
    field_info = schemas.RepairOrderBase.model_fields["access_code_provided"]
    assert "bool" in str(field_info.annotation).lower()

def test_no_password_fields_in_models():
    from app import models
    forbidden_terms = ["password", "device_password", "pin", "pin_code", "unlock_code", "graphic_key"]
    for col in models.RepairOrder.__table__.columns:
        for term in forbidden_terms:
            assert term not in col.name.lower(), f"Forbidden column '{term}' found in RepairOrder table '{col.name}'"
