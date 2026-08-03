import os
import glob
from app.database import engine

def test_no_destructive_database_calls_in_tests():
    """Verify that no unit test file contains active drop_all or DROP TABLE statements."""
    search_dirs = [
        "tests",
        "/app/tests",
        "../inventory-sales-module/tests"
    ]
    
    for d in search_dirs:
        if os.path.exists(d):
            for py_file in glob.glob(os.path.join(d, "*.py")):
                if "test_no_destructive_test_database_calls.py" in py_file:
                    continue
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    assert "Base.metadata.drop_all" not in content, f"Found forbidden 'Base.metadata.drop_all' call in {py_file}"
                    assert "DROP TABLE" not in content, f"Found forbidden 'DROP TABLE' call in {py_file}"

def test_engine_url_is_strictly_isolated():
    """Assert engine URL is not live production database."""
    url_str = str(engine.url)
    assert "/data/db/technoreboot.db" not in url_str, f"Engine is bound to production database: {url_str}"
    assert "isolated_test.db" in url_str or ":memory:" in url_str or "pytest" in url_str
