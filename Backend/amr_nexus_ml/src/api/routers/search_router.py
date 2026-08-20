from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.api.deps import get_db
from src.db.models import AMRIsolateRecord

search_router = APIRouter()


@search_router.get(
    "/query",
    status_code=status.HTTP_200_OK,
    response_model=List[Dict[str, Any]]
)
def search_historical_isolates(
    pathogen_code: Optional[str] = None,
    county: Optional[str] = None,
    mdr_only: bool = False,
    anomaly_only: bool = False,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    try:
        query = db.query(AMRIsolateRecord)
        
        if pathogen_code:
            query = query.filter(AMRIsolateRecord.pathogen_code == pathogen_code.lower().strip())
        if county:
            query = query.filter(AMRIsolateRecord.county == county.strip())
        if mdr_only:
            query = query.filter(AMRIsolateRecord.mdr_flag == True)
        if anomaly_only:
            query = query.filter(AMRIsolateRecord.anomaly_flag == True)
            
        records = query.order_by(desc(AMRIsolateRecord.created_at)).limit(limit).all()
        
        return [
            {
                "record_id": str(r.record_id),
                "timestamp": r.created_at.isoformat(),
                "pathogen_code": r.pathogen_code,
                "antibiotic_class": r.antibiotic_class,
                "sector": r.sector,
                "county": r.county,
                "mdr_probability": float(r.mdr_probability) if r.mdr_probability is not None else 0.0,
                "anomaly_score": float(r.anomaly_score) if r.anomaly_score is not None else 0.0,
                "shap_top_feature": r.shap_top_feature
            }
            for r in records
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Historical record repository lookup failed: {str(e)}"
        )
