import os

def test_no_sqlalchemy_imports():
    base_dir = os.path.join(os.path.dirname(__file__), "..", "app")
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "sqlalchemy" not in content, f"Found 'sqlalchemy' in {file_path}"
                    assert "sqlite3" not in content, f"Found 'sqlite3' in {file_path}"
