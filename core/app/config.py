from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "sqlite:///./technoreboot.db"
    storage_root: str = "./data/storage"
    backup_root: str = "./data/backups"
    api_token: str = "dev-token"

    # Optional Avito API Capability Configuration
    avito_client_id: Optional[str] = None
    avito_client_secret: Optional[str] = None
    avito_api_base: str = "https://api.avito.ru"

    class Config:
        env_file = ".env"

settings = Settings()
