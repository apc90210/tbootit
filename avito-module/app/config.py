from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AVITO_MODULE_NAME: str = "technoreboot-avito-module"
    AVITO_MODULE_MODE: str = "parser_mvp"
    CORE_API_BASE_URL: str = "http://core:8000"
    AVITO_STORAGE_DIR: str = "/app/data"
    AVITO_REQUEST_DELAY_SECONDS: int = 3
    AVITO_MAX_PAGES_PER_RUN: int = 2

    # Official Avito API / Autoload credentials (owned exclusively by avito-module)
    AVITO_CLIENT_ID: Optional[str] = None
    AVITO_CLIENT_SECRET: Optional[str] = None
    AVITO_API_BASE: str = "https://api.avito.ru"

    class Config:
        env_file = ".env"

settings = Settings()

