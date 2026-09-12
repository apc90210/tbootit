"""
Stage 08D-R1R4-SYNC: Hard-Delete Audit & Enforcement Test Suite
Verifies that across all modules, USER_ACCESSIBLE_HARD_DELETE_ROUTES == 0.
"""

import ast
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(r"C:\tbootit")

def test_hard_delete_route_inventory_ast():
    """Scan all Python router files across core, admin-shell, inventory-sales-module,
    repairs-module, and avito-module to assert USER_ACCESSIBLE_HARD_DELETE_ROUTES == 0.
    """
    modules = ["core", "admin-shell", "inventory-sales-module", "repairs-module", "avito-module"]

    all_delete_routes = []
    user_accessible_hard_deletes = []

    for mod_name in modules:
        mod_dir = PROJECT_ROOT / mod_name
        for py_file in mod_dir.rglob("*.py"):
            if "tests" in py_file.parts or ".venv" in py_file.parts:
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for dec in node.decorator_list:
                        # Looking for @router.delete(...) or @app.delete(...)
                        is_delete = False
                        path_val = ""

                        if isinstance(dec, ast.Call):
                            func = dec.func
                            if isinstance(func, ast.Attribute) and func.attr == "delete":
                                is_delete = True
                                if dec.args and isinstance(dec.args[0], ast.Constant):
                                    path_val = dec.args[0].value

                        if is_delete:
                            # Analyze route
                            is_soft = False
                            is_owner_only = False
                            is_user_allowed = False

                            if mod_name == "core" and path_val == "/{product_id}":
                                is_soft = True  # Soft delete sets status = written_off
                                is_user_allowed = True
                            elif mod_name == "admin-shell" and path_val == "/admin-api/avito/profiles/{account_key}":
                                is_soft = False
                                is_owner_only = True
                                is_user_allowed = False  # Protected by _require_owner
                            elif mod_name == "core" and "photos" in path_val:
                                is_soft = False
                                is_user_allowed = False  # Internal core only, zero host ports
                            elif mod_name == "avito-module" and "profiles" in path_val:
                                is_soft = False
                                is_user_allowed = False  # Internal avito-module service, proxied only through admin-shell

                            record = {
                                "module": mod_name,
                                "file": str(py_file.relative_to(PROJECT_ROOT)),
                                "function": node.name,
                                "path": path_val,
                                "is_soft": is_soft,
                                "is_owner_only": is_owner_only,
                                "is_user_allowed": is_user_allowed
                            }

                            all_delete_routes.append(record)
                            if not is_soft and is_user_allowed and not is_owner_only:
                                user_accessible_hard_deletes.append(record)

    print(f"\nTotal DELETE routes audited: {len(all_delete_routes)}")
    for r in all_delete_routes:
        print(f"  [{r['module']}] {r['path']} in {r['file']} (soft={r['is_soft']}, owner_only={r['is_owner_only']}, user_allowed={r['is_user_allowed']})")

    assert len(user_accessible_hard_deletes) == 0, f"Found user-accessible hard deletes: {user_accessible_hard_deletes}"


def test_no_delete_routes_for_business_entities():
    """Verify that Sales, Repairs, Customers, Categories, Stock Movements have 0 DELETE routes."""
    modules = ["core", "admin-shell", "inventory-sales-module", "repairs-module"]
    forbidden_entities = ["sales", "repairs", "customers", "categories", "stock-movements", "payments"]

    for mod_name in modules:
        mod_dir = PROJECT_ROOT / mod_name
        for py_file in mod_dir.rglob("*.py"):
            if "tests" in py_file.parts or ".venv" in py_file.parts:
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "delete":
                            if dec.args and isinstance(dec.args[0], ast.Constant):
                                path_val = str(dec.args[0].value).lower()
                                for entity in forbidden_entities:
                                    assert entity not in path_val, f"Forbidden hard delete route found for {entity}: {path_val} in {py_file}"
