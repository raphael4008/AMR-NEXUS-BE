"""
main.py — AMR-Nexus One Health Platform v2.0 Application Factory

July 14 Rev 2 entry point. Configures:
  - CORS for independent frontend deployments
  - Lifespan event: DB connectivity check + version logging on startup
  - Unified route prefixes via settings.API_V1_STR
  - /health liveness probe for container orchestration
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.api.auth import router as auth_router
from src.api.backbone import router as backbone_router
from src.api.intelligence import router as intelligence_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("amr_nexus")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: verify DB connectivity and log platform version.
    Shutdown: (reserved for cleanup hooks).
    """
    from src.models.base import engine
    from sqlalchemy import text

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(
            "✅ AMR-Nexus v2.0 — July 14 Rev 2 online | DB: %s",
            settings.POSTGRES_DB,
        )
    except Exception as exc:
        logger.warning(
            "⚠️  DB connectivity check failed at startup (expected if DB not running): %s", exc
        )

    yield
    logger.info("AMR-Nexus shutting down.")


# ── Application Factory ───────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "AMR-Nexus One Health Platform — Decision-Support, Adaptive Intelligence & "
        "Early Warning System for Antimicrobial Resistance surveillance in Kenya. "
        "July 14, 2026 Rev 2 Architecture."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route Mounting ────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(backbone_router, prefix=settings.API_V1_STR, tags=["Data Backbone"])
app.include_router(intelligence_router, prefix=settings.API_V1_STR, tags=["AI Dashboard Insights"])


# ── Health Probe ──────────────────────────────────────────────────────────────────

@app.get("/health", status_code=200, tags=["System Health"])
async def health_check():
    """Kubernetes/Docker liveness probe. Returns 200 when the application is running."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": settings.PROJECT_NAME,
    }


# ── Dev Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
