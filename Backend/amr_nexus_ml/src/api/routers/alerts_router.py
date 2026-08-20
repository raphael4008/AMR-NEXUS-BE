# src/api/routers/alerts.py
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.api.deps import get_db
from src.db.models import AMRIsolateRecord
from src.core.config import settings

alerts_router = APIRouter()


@alerts_router.get("", response_model=List[Dict[str, Any]])
@alerts_router.get("/active", response_model=List[Dict[str, Any]])
async def get_active_priority_alerts(
    county: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Returns active alerts (anomalies + high MDR probability) with SHAP explanations.
    """
    try:
        
        query = db.query(AMRIsolateRecord).filter(
            (AMRIsolateRecord.anomaly_flag == True) |
            (AMRIsolateRecord.mdr_probability >= 0.85)
        )
        if county:
            query = query.filter(AMRIsolateRecord.county == county)

        records = query.order_by(desc(AMRIsolateRecord.created_at)).limit(limit).all()

        alerts = []
        for r in records:
            # Determine severity
            if r.anomaly_flag and r.mdr_probability >= 0.85:
                severity = "high"
            elif r.anomaly_flag:
                severity = "medium"
            else:
                severity = "medium"  #

            alerts.append({
                "id": f"alert-{r.record_id}",
                "message": f" {'Anomaly' if r.anomaly_flag else 'High MDR'} detected: "
                           f"{r.pathogen_code.upper()} in {r.county}",
                "timestamp": r.created_at.isoformat(),
                "severity": severity,
                "type": "anomaly" if r.anomaly_flag else "trend",
                "acknowledged": False,
                "details": f"Anomaly score: {r.anomaly_score:.3f} | MDR prob: {r.mdr_probability*100:.1f}%",
                "pathogen_code": r.pathogen_code,
                "resistance_pattern": r.sir_result if r.sir_result else "Unknown",
                "county": r.county,
                "shap_summary": r.shap_summary or "No SHAP explanation available."
            })

        return alerts
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@alerts_router.get("/count")
async def get_alerts_count(
    county: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    """
    Returns count of active, unacknowledged alerts (for the notification bell).
    """
    try:
        seven_days_ago = datetime.utcnow() - timedelta(days=settings.ALERT_ANOMALY_DAYS)
        query = db.query(AMRIsolateRecord).filter(
            AMRIsolateRecord.anomaly_flag == True,
            AMRIsolateRecord.created_at >= seven_days_ago
        )
        if county:
            query = query.filter(AMRIsolateRecord.county == county)

        anomaly_count = query.count()

        
        high_mdr_query = db.query(AMRIsolateRecord).filter(
            AMRIsolateRecord.mdr_probability >= 0.30,
            AMRIsolateRecord.created_at >= seven_days_ago
        )
        if county:
            high_mdr_query = high_mdr_query.filter(AMRIsolateRecord.county == county)

        high_mdr_count = high_mdr_query.count()

        total = anomaly_count + high_mdr_count
        return {"count": total}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


#