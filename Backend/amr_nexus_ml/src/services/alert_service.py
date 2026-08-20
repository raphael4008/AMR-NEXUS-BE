from datetime import datetime, timedelta
from typing import List, Any
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from src.core.config import settings
from src.db.models import AMRIsolateRecord
from src.utils.logger import logger


def determine_severity(record: Any) -> str:
    """
    Classifies alert severity into rigorous tiers:
    - critical: XDR classification, extreme resistance (>= 85%) + anomaly, or MDR prob >= 0.90
    - high: MDR classification, high resistance (>= 70%), or high MDR prob >= 0.70
    - medium: Standard anomaly flags or moderate trends
    """
    classification = getattr(record, "classification", "").upper()
    resistance_pct = getattr(record, "resistance_percent", 0.0) or 0.0
    is_anomaly = getattr(record, "anomaly_flag", False)
    mdr_prob = getattr(record, "mdr_probability", 0.0) or 0.0

    if "XDR" in classification or (resistance_pct >= 85.0 and is_anomaly) or mdr_prob >= 0.90:
        return "critical"
    elif "MDR" in classification or resistance_pct >= 70.0 or mdr_prob >= 0.70 or is_anomaly:
        return "high"
    else:
        return "medium"


async def broadcast_alert(payload: dict) -> None:
    """
    Broadcasts the tiered alert payload to connected clients via Socket.IO.
    """
    try:
        from src.main import sio
        await sio.emit("amr_alert", payload)
        logger.info(f"Socket.IO broadcasted {payload['severity']} alert for pathogen {payload.get('pathogen_code')}")
    except Exception as e:
        logger.error(f"Failed to broadcast Socket.IO alert: {str(e)}")


def trigger_alert(record: Any, background_tasks: BackgroundTasks) -> None:
    """
    Evaluates a new record, determines its severity tier, and schedules a background broadcast.
    """
    severity = determine_severity(record)
    
    raw_id = getattr(record, "record_id", getattr(record, "id", None))
    
    payload = {
        "id": str(raw_id) if raw_id is not None else None,
        "severity": severity,
        "pathogen_code": getattr(record, "pathogen_code", "Unknown"),
        "county": getattr(record, "county", "Unknown"),
        "sector": getattr(record, "sector", "Unknown"),
        "resistance_percent": getattr(record, "resistance_percent", 0.0),
        "classification": getattr(record, "classification", "Standard"),
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"[{severity.upper()}] AMR Alert: {getattr(record, 'pathogen_code', 'Pathogen').upper()} detected in {getattr(record, 'county', 'County')} county."
    }

    if background_tasks:
        background_tasks.add_task(broadcast_alert, payload)
    else:
        import asyncio
        asyncio.create_task(broadcast_alert(payload))

def get_active_alerts(db: Session) -> List[AMRIsolateRecord]:
    seven_days_ago = datetime.utcnow() - timedelta(days=int(settings.ALERT_ANOMALY_DAYS))
    return (
        db.query(AMRIsolateRecord)
        .filter(
            (AMRIsolateRecord.anomaly_flag == True) | (AMRIsolateRecord.mdr_probability >= 0.70),
            AMRIsolateRecord.created_at >= seven_days_ago,
        )
        .order_by(AMRIsolateRecord.created_at.desc())
        .limit(20)
        .all()
    )