import os
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # ── Project Meta ────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "AMR-Nexus One Health Platform"
    API_V1_STR: str = "/api/v1"
    
    # ── CORS Origins ────────────────────────────────────────────────────────────
    FRONTEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://dashboard.amr-nexus.org"
    ]

    # ── Database ────────────────────────────────────────────────────────────────
    POSTGRES_SERVER: str = "127.0.0.1"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "secret"
    POSTGRES_DB: str = "amr_nexus"
    POSTGRES_PORT: int = 5432
    
    # Database Pool Settings (Explicitly defined to avoid AttributeError)
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True

    @computed_field
    @property
    def DATABASE_URI(self) -> str:
        # Uses asyncpg driver for asynchronous SQLAlchemy support
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Cache & Auth ────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── External Services ───────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    AT_USERNAME: str = "sandbox"
    AT_API_KEY: str = "your_api_key_here"
    KAFKA_BROKER_URL: str = "localhost:9092"

    # ── Config ──────────────────────────────────────────────────────────────────
    model_config = SettingsConfigDict(
        # Look for .env in the project root
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

# Instantiate the settings object
settings = Settings()