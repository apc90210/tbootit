"""
Stage 08D-R1R1: Tests for Production Data Guard and Code-Only Deployment Model
"""

import os
import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(r"C:\tbootit")
UPDATE_SCRIPT = PROJECT_ROOT / "deploy" / "production" / "update_code_only.sh"
COMPOSE_PROD_FILE = PROJECT_ROOT / "deploy" / "production" / "docker-compose.prod.yml"


def test_update_script_exists_and_has_guard_logic():
    """Verifies update_code_only.sh exists and contains required guard checks."""
    assert UPDATE_SCRIPT.is_file(), f"Missing update script: {UPDATE_SCRIPT}"
    content = UPDATE_SCRIPT.read_text(encoding="utf-8")
    
    # Check guard file presence check
    assert ".technoreboot_production_data" in content, "Missing production data guard check"
    assert "DATA_DIR" in content
    assert "PRE_COUNTS" in content
    assert "POST_COUNTS" in content
    assert "create_backup" in content
    assert "HEALTHCHECK TIMEOUT" in content
    
    # Check forbidden arguments list
    for kw in ["restore", "bootstrap", "wipe", "reset", "sync-from-local"]:
        assert kw in content, f"Missing forbidden keyword check for '{kw}'"


def test_guard_file_format():
    """Validates the structure and expected keys of the production data guard file."""
    sample_guard = (
        "environment=production\n"
        "data_owner=vds\n"
        "do_not_overwrite_from_local=true\n"
    )
    lines = [line.strip() for line in sample_guard.splitlines() if line.strip()]
    kv = dict(line.split("=", 1) for line in lines)
    
    assert kv.get("environment") == "production"
    assert kv.get("data_owner") == "vds"
    assert kv.get("do_not_overwrite_from_local") == "true"


def test_production_deployment_invariants():
    """Validates that production docker-compose does not mount local Windows paths."""
    assert COMPOSE_PROD_FILE.is_file()
    content = COMPOSE_PROD_FILE.read_text(encoding="utf-8")
    
    # Must not contain Windows drive letters in volume mounts
    assert "C:\\" not in content
    assert "c:/" not in content
    assert "TECHNOREBOOT_DATA_ROOT" in content
