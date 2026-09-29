"""
Root Pytest Configuration for TechnoReboot.
Guarantees test database isolation across all test suites in the repository.
Prevents tests from creating ./technoreboot.db in repo root or touching canonical DB.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent
_core_path = str(REPO_ROOT / "core")
if _core_path not in sys.path:
    sys.path.insert(0, _core_path)

# Ensure IS_TESTING flag is set early
os.environ["IS_TESTING"] = "1"

# Fail-safe validator
def assert_not_canonical_db(url_or_path: str):
    norm = str(url_or_path).replace("\\", "/").lower()
    for forbidden in ["data/db/technoreboot.db", "/data/db/technoreboot.db", "/srv/technoreboot"]:
        if forbidden in norm:
            raise RuntimeError(
                f"FATAL SECURITY VIOLATION: Test database points to canonical DB: {url_or_path}"
            )

# Create session-scoped isolated temporary directory and test database
_root_test_dir = tempfile.TemporaryDirectory(prefix="pytest_root_isolated_")
_root_test_db_path = os.path.join(_root_test_dir.name, "isolated_test.db")
_root_test_db_url = f"sqlite:///{_root_test_db_path}"

# Only set if DATABASE_URL is not set or points to relative/canonical technoreboot.db
current_db_url = os.environ.get("DATABASE_URL", "")
if not current_db_url or "technoreboot.db" in current_db_url:
    os.environ["DATABASE_URL"] = _root_test_db_url

assert_not_canonical_db(os.environ["DATABASE_URL"])


@pytest.fixture(autouse=True, scope="session")
def fail_safe_canonical_db_protection():
    """Verify before and after test session that tests never point to canonical DB."""
    active_url = os.environ.get("DATABASE_URL", "")
    assert_not_canonical_db(active_url)
    yield
    assert_not_canonical_db(active_url)
    try:
        _root_test_dir.cleanup()
    except Exception:
        pass
