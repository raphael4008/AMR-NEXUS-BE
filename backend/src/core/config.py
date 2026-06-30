import os
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # ── Project Meta ────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "AMR-Nexus One Health Platform"
    API_V1_STR: str = "/api/v1"
    
    # ── Database (Now using Docker service names) ───────────────────────────────
    POSTGRES_SERVER: str = "amr_nexus_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "secret"
    POSTGRES_DB: str = "amr_nexus"
    POSTGRES_PORT: int = 5432
    
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True

    @computed_field
    @property
    def DATABASE_URI(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Cache & Auth ────────────────────────────────────────────────────────────
    # Must use service name 'amr_nexus_cache' as defined in docker-compose
    REDIS_URL: str = "redis://amr_nexus_cache:6379"
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── External Services ───────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    KAFKA_BROKER_URL: str = "amr_nexus_broker:9092"

    # ── Config ──────────────────────────────────────────────────────────────────
    model_config = SettingsConfigDict(
        # Pydantic will automatically override defaults with matching .env variables
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()