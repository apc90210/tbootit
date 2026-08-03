import os
import pytest

# CRITICAL: Isolate pytest from live production database (/data/db/technoreboot.db)
TEST_DB_PATH = "./test_core_isolated.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.config import settings
settings.database_url = TEST_DATABASE_URL

# Re-bind app.database engine to isolated test DB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.database

app.database.engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
app.database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app.database.engine)
app.database.settings.database_url = TEST_DATABASE_URL

from app.database import Base, engine

@pytest.fixture(autouse=True, scope="session")
def setup_isolated_test_database():
    """Ensure test DB is initialized before session and cleaned up after session."""
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass
