import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configs(BaseSettings):
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "salamat")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "salamat")
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "salamat")
    POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.environ.get("POSTGRES_PORT", "5432")
    BOT_TOKEN:str=os.environ.get("BOT_TOKEN")
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    REDIS_BROKER:str="redis://localhost:6379/0"
configs = Configs()
