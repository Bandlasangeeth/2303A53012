import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    API_BASE_ENDPOINT: str = "http://4.224.186.213"
    AUTH_TOKEN: str = ""  # Configure this in .env

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


config = AppConfig()
