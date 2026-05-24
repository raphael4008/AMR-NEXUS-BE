import os
from typing import Optional
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AMR-Nexus One Health Platform"
    API_V1_STR: str = "/api/v1"

    # ── Database ────────────────────────────────────────────────────────────────
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "amr_nexus_db"
    POSTGRES_PORT: int = 5432

    @computed_field
    @property
    def DATABASE_URI(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Cache ───────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── JWT Authentication ──────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── LLM Advisory — Component C ─────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""

    # ── Africa's Talking SMS ────────────────────────────────────────────────────
    AT_USERNAME: str = "sandbox"
    AT_API_KEY: str = "your_at_api_key_here"

    # ── Event Streaming ─────────────────────────────────────────────────────────
    KAFKA_BROKER_URL: str = "localhost:9092"

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
