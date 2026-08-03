import os
import sys
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.database

# CRITICAL SECURITY RULE: Pytest MUST NEVER connect to or mutate live production DB (/data/db/technoreboot.db)
_temp_dir = tempfile.TemporaryDirectory(prefix="pytest_core_isolated_")
TEST_DB_PATH = os.path.join(_temp_dir.name, "isolated_test.db")
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.config import settings
settings.database_url = TEST_DATABASE_URL

# Re-bind app.database engine and SessionLocal to isolated temporary SQLite DB
app.database.engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
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

@pytest.fixture(autouse=True, scope="session")
def setup_isolated_test_database():
    """Ensure isolated temp DB tables are initialized before tests and cleaned up after session."""
    Base.metadata.create_all(bind=engine)
    yield
    try:
        _temp_dir.cleanup()
    except Exception:
        pass
