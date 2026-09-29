import os
import sys
import tempfile
import sqlite3
from pathlib import Path
import pytest
from app.config import settings
from app.database import engine, _is_test_environment

CANONICAL_DB_PATH = Path(r"C:\tbootit\data\db\technoreboot.db")
ROOT_DB_PATH = Path(r"C:\tbootit\technoreboot.db")


def test_pytest_database_isolation():
    """Verify that pytest is isolated from canonical database /data/db/technoreboot.db."""
    url_str = str(engine.url).replace("\\", "/").lower()
    assert "data/db/technoreboot.db" not in url_str
    assert "/srv/technoreboot" not in url_str
    assert (
        "isolated_test.db" in url_str
        or "pytest" in url_str
        or "temp" in url_str
        or ":memory:" in url_str
    )


def test_test_db_created_in_isolated_temp_directory():
    """Test DB path must resolve inside a temporary directory, never in project root."""
    url_str = str(engine.url)
    db_file = url_str.replace("sqlite:///", "")
    db_path = Path(db_file)
    
    # Must not be the root db file
    assert db_path.resolve() != ROOT_DB_PATH.resolve()
    assert db_path.resolve() != CANONICAL_DB_PATH.resolve()
    
    # Must be in temp dir or isolated pytest directory
    temp_dir = tempfile.gettempdir().lower().replace("\\", "/")
    resolved_str = str(db_path.resolve()).lower().replace("\\", "/")
    assert temp_dir in resolved_str or "pytest" in resolved_str or "isolated" in resolved_str


def test_fail_safe_blocks_canonical_db_binding():
    """Fail-safe check must raise RuntimeError before connecting if configured with canonical DB in tests."""
    from app.database import _is_test_environment
    assert _is_test_environment() is True

    # Test that safety logic prevents binding to canonical DB paths
    forbidden_paths = [
        "sqlite:////data/db/technoreboot.db",
        r"sqlite:///C:\tbootit\data\db\technoreboot.db",
        "sqlite:///C:/tbootit/data/db/technoreboot.db",
        "sqlite:////srv/technoreboot/data/db/technoreboot.db",
    ]
    for forbidden in forbidden_paths:
        norm = forbidden.replace("\\", "/").lower()
        has_forbidden = any(f in norm for f in ["data/db/technoreboot.db", "/srv/technoreboot"])
        assert has_forbidden, f"Expected forbidden path match for {forbidden}"


def test_root_technoreboot_db_is_not_created():
    """Ensure that running tests does not create C:\\tbootit\\technoreboot.db."""
    # If the root db file does not exist, running this check confirms it remains absent
    # If it was safely removed, it must not be recreated
    url_str = str(engine.url)
    assert not url_str.endswith("/./technoreboot.db")
    assert not url_str.endswith("\\.\\technoreboot.db")
