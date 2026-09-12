from pydantic_settings import BaseSettings
from pydantic import model_validator

INSECURE_SECRETS = {"dev-token", "change-me", "admin", "password", "secret", "123456"}

class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "sqlite:///./technoreboot.db"
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

settings = Settings()

