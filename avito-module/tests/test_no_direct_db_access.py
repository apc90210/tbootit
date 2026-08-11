import glob

def test_no_direct_db_access_in_avito_module():
    """
    Verify zero direct DB imports, SQLAlchemy connections, or raw SQLite calls in avito-module.
    avito-module must communicate with Core strictly via HTTP APIs.
    """
    forbidden_terms = ["create_engine", "SessionLocal", "sqlite3", "technoreboot.db", "data/db"]
    files = glob.glob("app/**/*.py", recursive=True)

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            for term in forbidden_terms:
                assert term not in content, f"Forbidden direct DB term '{term}' found in {file_path}"
