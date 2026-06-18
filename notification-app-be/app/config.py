import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    EVALUATION_API_BASE_URL: str = "http://4.224.186.213"
    ACCESS_TOKEN: str = "" # Provide this in .env

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
