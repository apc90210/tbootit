import os
from app.config import settings
from app.database import engine

def test_pytest_database_isolation():
    """Verify that pytest is isolated from live production database /data/db/technoreboot.db."""
    # Assert database URL is not the live container DB path
    assert "/data/db/technoreboot.db" not in str(engine.url)
    assert "isolated_test.db" in settings.database_url or "pytest" in settings.database_url or ":memory:" in settings.database_url
