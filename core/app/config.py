import os
import sys
import tempfile
from pydantic_settings import BaseSettings
from pydantic import model_validator, Field

INSECURE_SECRETS = {"dev-token", "change-me", "admin", "password", "secret", "123456"}

def _is_testing() -> bool:
    return (
        "pytest" in sys.modules
        or "PYTEST_CURRENT_TEST" in os.environ
        or os.environ.get("IS_TESTING") == "1"
        or any("pytest" in str(a).lower() for a in sys.argv)
    )

def _get_default_database_url() -> str:
    if _is_testing():
        return f"sqlite:///{tempfile.gettempdir().replace(chr(92), '/')}/technoreboot_isolated_test.db"
    return "sqlite:///./technoreboot.db"

class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = Field(default_factory=_get_default_database_url)
    storage_root: str = "./data/storage"
    backup_root: str = "./data/backups"
    api_token: str = "dev-token"

    @model_validator(mode="after")
    def check_production_safety(self):
        if self.app_env in ("prod", "production"):
            if not self.api_token or self.api_token.strip().lower() in INSECURE_SECRETS:
                raise ValueError(
                    f"Insecure or default API_TOKEN ('{self.api_token}') is prohibited in production. "
                    "Provide an explicit, secure API_TOKEN."
                )
        return self

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

