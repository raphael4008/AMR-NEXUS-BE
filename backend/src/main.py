"""
main.py — AMR-Nexus One Health Platform v2.1 Application Factory

Lifespan manages:
  1. PostgreSQL async engine — validated on startup, disposed on shutdown
  2. ARQ Redis pool — shared across request handlers via app.state.redis_pool
  3. SlowAPI rate limiting — decorator-based, no Redis required
"""

import logging
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from src.core.config import settings
from src.core.rate_limiter import limiter
from src.api.auth import router as auth_router
from src.api.backbone import router as backbone_router
from src.api.intelligence import router as intelligence_router
from src.models.base import engine
from src.models.entities import AMRRecord, Alert, GuidanceBrief  # noqa: F401

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("amr_nexus")


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Validate DB
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connected | DB: %s", settings.POSTGRES_DB)
    except Exception as exc:
        logger.critical("❌ Database connection failed: %s", exc)
        raise

    # 2. ARQ Redis pool
    try:
        app.state.redis_pool = await create_pool(
            RedisSettings.from_dsn(settings.REDIS_URL)
        )
        logger.info("✅ ARQ Redis pool ready | %s", settings.REDIS_URL)
    except Exception as exc:
        logger.error("❌ ARQ Redis pool failed: %s", exc)
        app.state.redis_pool = None

    logger.info("🚀 AMR-Nexus v2.1 online")

    yield  # Application running

    # Shutdown
    if getattr(app.state, "redis_pool", None):
        await app.state.redis_pool.aclose()
        logger.info("ARQ Redis pool closed.")
    await engine.dispose()
    logger.info("AMR-Nexus shutting down cleanly.")


# ── App Factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)

# ── Rate Limiter (SlowAPI) ────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
dev_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:5174",
]
allowed_origins = list(set(list(settings.FRONTEND_CORS_ORIGINS) + dev_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth_router,        prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(backbone_router,    prefix=settings.API_V1_STR, tags=["Data Backbone"])
app.include_router(intelligence_router, prefix=settings.API_V1_STR, tags=["AI Dashboard Insights"])


# ── Health Probe ──────────────────────────────────────────────────────────────
@app.get("/health", status_code=200, tags=["System Health"])
async def health_check():
    return {"status": "healthy", "version": "2.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=True)