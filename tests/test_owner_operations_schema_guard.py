import os
import sys
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
admin_shell_path = str(REPO_ROOT / "admin-shell")
scripts_path = str(REPO_ROOT / "scripts")

for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        mod = sys.modules[k]
        if hasattr(mod, "__file__") and mod.__file__ and "admin-shell" not in mod.__file__:
            sys.modules.pop(k, None)

if admin_shell_path in sys.path:
    sys.path.remove(admin_shell_path)
sys.path.insert(0, admin_shell_path)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from db_schema_contract import (
    extract_contract_from_source_models,
    compare_schema_contracts,
    check_deployment_compatibility_flag,
    compute_contract_sha256,
)

import app.main as admin_main
app = admin_main.app
_get_schema_compatibility_status = admin_main._get_schema_compatibility_status

client = TestClient(app)


def test_schema_contract_self_comparison_safe():
    """A contract compared to itself must always be safe with 0 diffs."""
    contract = extract_contract_from_source_models()
    is_safe, diffs = compare_schema_contracts(contract, contract)
    assert is_safe is True
    assert len(diffs) == 0


def test_schema_guard_detects_new_column():
    """Adding a column to a table must be detected as a schema difference."""
    c1 = extract_contract_from_source_models()
    c2 = json.loads(json.dumps(c1))  # deep copy
    
    # Add a column to products table in c2
    c2["tables"]["products"]["columns"].append({
        "name": "new_experimental_col",
        "type": "VARCHAR(100)",
        "nullable": True,
        "primary_key": 0,
        "default": None,
    })
    
    is_safe, diffs = compare_schema_contracts(c2, c1)
    assert is_safe is False
    assert any("new_experimental_col" in d for d in diffs)


def test_schema_guard_detects_type_change():
    """Altering column type must be detected."""
    c1 = extract_contract_from_source_models()
    c2 = json.loads(json.dumps(c1))
    
    # Change type of products.sale_price (was FLOAT in SQLite) to TEXT
    for col in c2["tables"]["products"]["columns"]:
        if col["name"] == "sale_price":
            col["type"] = "TEXT"
            break
    
    is_safe, diffs = compare_schema_contracts(c2, c1)
    assert is_safe is False
    assert any("Type mismatch" in d for d in diffs)


def test_schema_guard_detects_table_diff():
    """Adding or dropping a table must be detected."""
    c1 = extract_contract_from_source_models()
    c2 = json.loads(json.dumps(c1))
    
    # Add a new table
    c2["tables"]["new_audit_log_v2"] = {
        "columns": [
            {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": 1, "default": None}
        ],
        "foreign_keys": [],
        "indexes": []
    }
    
    is_safe, diffs = compare_schema_contracts(c2, c1)
    assert is_safe is False
    assert any("new_audit_log_v2" in d for d in diffs)


def test_deployment_compatibility_flag_check():
    """Verify check_deployment_compatibility_flag reads tracked json."""
    ok, msg = check_deployment_compatibility_flag()
    assert ok is True
    assert "SAFE" in msg or "compatible" in msg.lower()


def test_update_blocked_when_migration_flag_true(monkeypatch, tmp_path):
    """When requires_manual_migration is True, POST /admin-api/system/operations/update must be blocked (400)."""
    # Create fake devops dir with requires_manual_migration=True
    fake_devops = tmp_path / "dev-ops"
    fake_devops.mkdir(parents=True)
    compat_file = fake_devops / "deployment_compatibility.json"
    compat_file.write_text(json.dumps({
        "requires_manual_migration": True,
        "database_change": True,
        "reason": "Test manual migration required"
    }), encoding="utf-8")
    
    status = _get_schema_compatibility_status(fake_devops)
    assert status["safe_to_deploy"] is False
    assert status["requires_manual_migration"] is True

    # Monkeypatch _get_schema_compatibility_status in main to return this status
    from app import main
    monkeypatch.setattr(main, "_get_schema_compatibility_status", lambda d: {
        "safe_to_deploy": False,
        "requires_manual_migration": True,
        "database_change": True,
        "reason": "Test migration blocked",
    })
    
    resp = client.post("/admin-api/system/operations/update", headers={"x-auth-is-owner": "1"})
    assert resp.status_code == 400
    assert "требующие ручной миграции" in resp.json()["detail"]
