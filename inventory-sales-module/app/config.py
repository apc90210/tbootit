from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    inventory_sales_module_name: str = "technoreboot-inventory-sales-module"
    core_api_base_url: str = "http://core:8000"
    
    class Config:
        env_file = ".env"

settings = Settings()
