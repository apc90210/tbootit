import os
import sys
import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

def _is_test_environment() -> bool:
    if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("IS_TESTING") == "1":
        return True
    for arg in sys.argv:
        if "pytest" in str(arg).lower():
            return True
    return False

# Fail-safe protection: tests must NEVER connect to canonical development/production DB
if _is_test_environment():
    norm_url = str(settings.database_url).replace("\\", "/").lower()
    for forbidden in ["data/db/technoreboot.db", "/srv/technoreboot"]:
        if forbidden in norm_url:
            raise RuntimeError(
                f"FATAL SECURITY VIOLATION: Test environment attempted to bind to canonical DB: {settings.database_url}"
            )

engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)

@event.listens_for(engine, "connect")
def configure_sqlite_connection(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.create_function("lower", 1, lambda s: s.lower() if s is not None else None)
        dbapi_connection.create_function("upper", 1, lambda s: s.upper() if s is not None else None)
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
