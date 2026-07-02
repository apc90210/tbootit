import os

def test_no_sqlalchemy_imports_in_sales():
    """Ensure no direct DB access in sales module."""
    base_dir = os.path.join(os.path.dirname(__file__), "..", "app")
    sales_files = [
        os.path.join(base_dir, "routers", "sales.py"),
        os.path.join(base_dir, "core_client.py"),
    ]
    
    for file_path in sales_files:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "sqlalchemy" not in content, f"Found 'sqlalchemy' in {file_path}"
                assert "sqlite3" not in content, f"Found 'sqlite3' in {file_path}"
                assert "SessionLocal" not in content, f"Found 'SessionLocal' in {file_path}"
                assert "create_engine" not in content, f"Found 'create_engine' in {file_path}"
