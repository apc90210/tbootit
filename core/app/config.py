from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "sqlite:///./technoreboot.db"
    storage_root: str = "./data/storage"
    backup_root: str = "./data/backups"
    api_token: str = "dev-token"

    class Config:
        env_file = ".env"

settings = Settings()
