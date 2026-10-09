import os
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure core package is importable
_core_dir = str(Path(__file__).resolve().parent.parent)
if _core_dir not in sys.path:
    sys.path.insert(0, _core_dir)

# CRITICAL SECURITY RULE: Pytest MUST NEVER connect to or mutate live canonical DB
def assert_not_canonical_db(url_or_path: str):
    norm = str(url_or_path).replace("\\", "/").lower()
    for forbidden in ["data/db/technoreboot.db", "/srv/technoreboot"]:
        if forbidden in norm:
            raise RuntimeError(f"FATAL SECURITY VIOLATION: Test database points to canonical DB: {url_or_path}")

# Initialize isolated temporary database BEFORE importing app modules
_temp_dir = tempfile.TemporaryDirectory(prefix="pytest_core_isolated_", ignore_cleanup_errors=True)
TEST_DB_PATH = os.path.join(_temp_dir.name, "isolated_test.db")
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["IS_TESTING"] = "1"
assert_not_canonical_db(TEST_DATABASE_URL)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.database
from app.config import settings

settings.database_url = TEST_DATABASE_URL

# Re-bind app.database engine and SessionLocal to isolated temporary SQLite DB
from sqlalchemy import event
app.database.engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
event.listen(app.database.engine, "connect", app.database.configure_sqlite_connection)
app.database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app.database.engine)
app.database.settings.database_url = TEST_DATABASE_URL

from app.database import Base, engine
from fastapi.testclient import TestClient
from app.main import app

# Hard safety assertion
assert "/data/db/technoreboot.db" not in str(engine.url), "FATAL: Pytest attempted to bind to live production database!"
assert "isolated_test.db" in str(engine.url), "FATAL: Pytest is not using isolated temporary database!"

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def db(db_session):
    """Alias for db_session fixture for consistency across test suites."""
    return db_session


@pytest.fixture(autouse=True, scope="session")
def setup_isolated_test_database():
    """Ensure isolated temp DB tables are initialized before tests and cleaned up after session."""
    Base.metadata.create_all(bind=engine)
    yield
    try:
        engine.dispose()
        if hasattr(app.database, "engine"):
            app.database.engine.dispose()
    except Exception:
        pass
    try:
        _temp_dir.cleanup()
    except Exception:
        pass

