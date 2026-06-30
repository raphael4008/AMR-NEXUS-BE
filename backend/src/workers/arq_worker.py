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


# ── Task: Decision Support (LLM Advisory) ─────────────────────────────────────────

async def run_decision_support(ctx: dict, alert_id: str, target_role: str) -> dict:
    """
    ARQ task: generates LLM advisory for a specific alert and target role.
    Persists GuidanceBrief with status COMPLETED on success.
    """
    from src.models.base import AsyncSessionLocal
    from src.services.intelligence.llm_advisory import LLMAdvisoryEngine
    from src.models.entities import GuidanceBrief
    from sqlalchemy import update

    logger.info("Running decision support for alert %s, role=%s", alert_id, target_role)

    try:
        async with AsyncSessionLocal() as db:
            advisory_engine = LLMAdvisoryEngine()
            brief = await advisory_engine.trigger_role_guidance(
                uuid.UUID(alert_id), target_role, db
            )
            if brief:
                # Mark as COMPLETED so the GET endpoint can return it
                await db.execute(
                    update(GuidanceBrief)
                    .where(GuidanceBrief.id == brief.id)
                    .values(status="COMPLETED")
                )
                await db.commit()
                logger.info("Decision support completed for alert %s", alert_id)
                return {"status": "completed", "brief_id": str(brief.id)}
            return {"status": "no_brief"}
    except Exception as exc:
        logger.error("Decision support failed for alert %s: %s", alert_id, exc, exc_info=True)
        raise


# ── Task: Report Delivery (webhook) ────────────────────────────────────────────────

async def run_report_delivery(ctx: dict, report_id: str, email: str, format: str, report_type: str) -> dict:
    """
    ARQ task: delivers a scheduled report via webhook.
    Marks ScheduledReport as DELIVERED on success, FAILED on error.
    """
    from src.models.base import AsyncSessionLocal
    from src.models.entities import ScheduledReport
    from src.core.config import settings
    from sqlalchemy import update, select
    from datetime import datetime, timezone
    import httpx

    logger.info("Delivering report %s (%s) to %s", report_id, format, email)

    try:
        async with AsyncSessionLocal() as db:
            # Build report payload (summary data)
            webhook_payload = {
                "report_id":   report_id,
                "recipient":   email,
                "format":      format,
                "report_type": report_type,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "message":     f"AMR-Nexus {report_type} report for {email}",
            }

            # Deliver via webhook if configured
            webhook_url = getattr(settings, "REPORT_WEBHOOK_URL", None)
            delivered = False
            if webhook_url:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(webhook_url, json=webhook_payload)
                    resp.raise_for_status()
                    delivered = True
                    logger.info("Report %s delivered via webhook", report_id)
            else:
                logger.warning("REPORT_WEBHOOK_URL not configured — report %s not delivered", report_id)

            # Update status
            new_status = "DELIVERED" if delivered else "FAILED"
            await db.execute(
                update(ScheduledReport)
                .where(ScheduledReport.id == report_id)
                .values(status=new_status, delivered_at=datetime.now(timezone.utc))
            )
            await db.commit()
            return {"status": new_status, "report_id": report_id}

    except Exception as exc:
        logger.error("Report delivery failed for %s: %s", report_id, exc, exc_info=True)
        raise



# ── Worker Settings (arq 0.28 compatible) ────────────────────────────────────

class WorkerSettings:
    """
    ARQ worker configuration for arq >= 0.28.

    Start with:
        cd backend && arq src.workers.arq_worker.WorkerSettings

    Environment variables read from same .env as FastAPI.
    """

    functions = [run_anomaly_pipeline, run_decision_support, run_report_delivery]

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
