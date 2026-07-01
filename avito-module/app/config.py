from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AVITO_MODULE_NAME: str = "technoreboot-avito-module"
    AVITO_MODULE_MODE: str = "parser_mvp"
    CORE_API_BASE_URL: str = "http://core:8000"
    AVITO_STORAGE_DIR: str = "/app/data"
    AVITO_REQUEST_DELAY_SECONDS: int = 3
    AVITO_MAX_PAGES_PER_RUN: int = 2

    class Config:
        env_file = ".env"

settings = Settings()
