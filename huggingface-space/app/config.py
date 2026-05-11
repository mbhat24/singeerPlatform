from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "Singer Platform"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    DATABASE_URL: str = "sqlite+aiosqlite:///./singer.db"

    UPLOAD_DIR: Path = Path("./uploads")
    OUTPUT_DIR: Path = Path("./outputs")
    MODEL_DIR: Path = Path("./models")

    RVC_MODEL_PATH: str = "./models/rvc"
    MAX_VOICE_SAMPLE_SECONDS: int = 120
    MIN_VOICE_SAMPLE_SECONDS: int = 10
    MAX_UPLOAD_SIZE_MB: int = 50


settings = Settings()
