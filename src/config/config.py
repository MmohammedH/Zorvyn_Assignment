from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings

from enums.enums import Environment


class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="Finance System")
    app_version: str = Field(default="0.1.0")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Database — defaults to SQLite for easy local setup
    db_driver: str = Field(default="sqlite+aiosqlite")
    db_path: str = Field(default="./finance.db")

    # PostgreSQL fields (used when db_driver is postgresql+asyncpg)
    db_username: str = Field(default="")
    db_password: str = Field(default="")
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_name: str = Field(default="finance")

    # JWT
    jwt_secret_key: str = Field(default="dev-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60)

    # Admin seed account (created on first startup if no users exist)
    seed_admin_email: str = Field(default="admin@example.com")
    seed_admin_password: str = Field(default="Admin@12345")
    seed_admin_name: str = Field(default="System Admin")

    @property
    def database_url(self) -> str:
        if "sqlite" in self.db_driver:
            return f"{self.db_driver}:///{self.db_path}"
        return (
            f"{self.db_driver}://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def is_dev(self) -> bool:
        return self.environment in (Environment.DEVELOPMENT, Environment.STAGING)

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
