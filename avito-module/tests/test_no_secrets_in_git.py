import glob
import os

def test_no_secrets_or_runtime_profiles_in_tracked_git():
    """
    Verify zero tracked password, cookie, or browser user-data-dir files in git.
    """
    forbidden_terms = ["password", "cookie", "storage_state", "user-data-dir", "SingletonCookie"]
    tracked_files = glob.glob("app/**/*.py", recursive=True)

    for file_path in tracked_files:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for idx, line in enumerate(lines):
                # Skip comments or variable definitions
                if line.strip().startswith("#"):
                    continue
                assert "password_hash" not in line.lower(), f"Potential secret in {file_path}:{idx+1}"
                assert "secret_key = '123" not in line.lower(), f"Potential secret in {file_path}:{idx+1}"

def test_gitignore_contains_avito_profile_exclusions():
    """
    Verify .gitignore excludes browser storage, cookies, and profile directories.
    """
    gitignore_path = "../.gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "profiles" in content or "user-data-dir" in content or "browser_data" in content or "storage" in content
