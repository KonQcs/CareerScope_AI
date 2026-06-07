from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="CareerScope AI", alias="APP_NAME")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    database_url: str = Field(
        default="sqlite:///./data/careerscope.db",
        alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
