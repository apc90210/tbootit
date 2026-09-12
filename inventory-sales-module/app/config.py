from pydantic_settings import BaseSettings
from pydantic import model_validator

INSECURE_SECRETS = {"technoreboot_secret_cart_key_mvp", "dev-token", "change-me", "admin", "password", "secret", "123456"}

class Settings(BaseSettings):
    inventory_sales_module_name: str = "technoreboot-inventory-sales-module"
    core_api_base_url: str = "http://core:8000"
    app_env: str = "dev"
    cart_session_secret: str = "technoreboot_secret_cart_key_mvp"

    @model_validator(mode="after")
    def check_production_safety(self):
        if self.app_env in ("prod", "production"):
            if not self.cart_session_secret or self.cart_session_secret.strip().lower() in INSECURE_SECRETS:
                raise ValueError(
                    f"Insecure or default CART_SESSION_SECRET is prohibited in production. "
                    "Provide an explicit, secure CART_SESSION_SECRET."
                )
        return self
    
    class Config:
        env_file = ".env"

settings = Settings()
