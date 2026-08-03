import os
import glob

def test_no_sqlalchemy_or_sqlite_imports_in_repairs_module():
    app_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app")
    py_files = glob.glob(os.path.join(app_dir, "**", "*.py"), recursive=True)

    forbidden_keywords = [
        "sqlalchemy",
        "sqlite3",
        "create_engine",
        "SessionLocal",
        "technoreboot.db",
        "data/db",
        "SELECT ",
        "INSERT INTO"
    ]

    for py_file in py_files:
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
            for kw in forbidden_keywords:
                assert kw not in content, f"Found forbidden keyword '{kw}' in {py_file}"
