"""
workers/arq_worker.py — AMR-Nexus ARQ Worker Process (arq >= 0.28)

Run as a separate process:
    cd backend && arq src.workers.arq_worker.WorkerSettings

Design:
  - Pure async tasks — no sync executor wrappers
  - Each task opens its own AsyncSession (not shared with FastAPI)
  - ARQ manages its own Redis connection pool separately from FastAPI's pool
"""

import logging
import uuid
from typing import List

from arq.connections import RedisSettings

from src.core.config import settings

logger = logging.getLogger("amr_nexus.worker")


# ── Task: Anomaly Detection Pipeline ─────────────────────────────────────────

async def run_anomaly_pipeline(ctx: dict, record_ids: List[str]) -> dict:
    """
    ARQ task: fetches newly ingested AMR records, runs the anomaly engine,
    persists alerts, and triggers downstream tasks (LLM advisory, SMS).

    Args:
        ctx: ARQ context (contains 'redis', job metadata, etc.)
        record_ids: UUID strings for newly inserted AMRRecord rows.

    Returns:
        Summary dict with counts of records processed and alerts created.
    """
    from src.models.base import AsyncSessionLocal
    from src.services.ml_engine.anomaly_detector import AMRAnomalyEngine

    logger.info("Starting anomaly pipeline for %d record(s)", len(record_ids))
    uuids = [uuid.UUID(rid) for rid in record_ids]
    alerts_created: List[uuid.UUID] = []

    try:
        async with AsyncSessionLocal() as db:
            engine = AMRAnomalyEngine()
            alert_ids = await engine.execute_analysis_pipeline(uuids, db)
            alerts_created.extend(alert_ids)
            logger.info("Anomaly engine produced %d alert(s)", len(alert_ids))

            for alert_id in alert_ids:
                try:
                    await engine.trigger_downstream_tasks(alert_id, db)
                except Exception as exc:
                    logger.error("Downstream task failed for alert %s: %s", alert_id, exc)

    except Exception as exc:
        logger.error("Anomaly pipeline failed: %s", exc, exc_info=True)
        raise

    return {
        "records_processed": len(record_ids),
        "alerts_created": len(alerts_created),
        "alert_ids": [str(aid) for aid in alerts_created],
    }


# ── Worker Settings (arq 0.28 compatible) ────────────────────────────────────

class WorkerSettings:
    """
    ARQ worker configuration for arq >= 0.28.

    Start with:
        cd backend && arq src.workers.arq_worker.WorkerSettings

    Environment variables read from same .env as FastAPI.
    """

    functions = [run_anomaly_pipeline]

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

    # Max concurrent jobs — tune relative to DB pool size
    max_jobs = 10

    # Per-job timeout in seconds (5 min for large batches)
    job_timeout = 300

    # Retry failed jobs up to 3 times
    max_tries = 3

    # Keep results 24h for debugging
    keep_result = 86_400  # seconds

    @staticmethod
    async def on_startup(ctx: dict):
        logger.info("AMR-Nexus ARQ worker started | Redis: %s", settings.REDIS_URL)

    @staticmethod
    async def on_shutdown(ctx: dict):
        logger.info("AMR-Nexus ARQ worker shut down cleanly.")
