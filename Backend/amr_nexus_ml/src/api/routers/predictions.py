# src/api/routers/predictions.py
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from src.api.deps import get_db
from src.api.schemas import AMRRecordIn, PredictionResponse, CommentCreate
from src.services.prediction_service import PredictionService
from src.db.models import AMRIsolateRecord, Comment
import uuid

router = APIRouter()  # ← changed from prediction_router to router


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    record: AMRRecordIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        service = PredictionService(db)
        result = await service.predict(record, background_tasks)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions")
async def get_predictions(
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    records = db.query(AMRIsolateRecord).order_by(AMRIsolateRecord.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "record_id": str(r.record_id),
            "pathogen_code": r.pathogen_code,
            "county": r.county,
            "mdr_flag": r.mdr_flag,
            "mdr_probability": float(r.mdr_probability) if r.mdr_probability is not None else 0.0,
            "anomaly_detected": r.anomaly_flag,
            "timestamp": r.created_at.isoformat(),
            "shap_summary": r.shap_summary
        }
        for r in records
    ]


@router.delete("/predictions/{record_id}")
async def delete_prediction(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(AMRIsolateRecord).filter(AMRIsolateRecord.record_id == uuid.UUID(record_id)).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(record)
    db.commit()
    return {"status": "deleted"}


@router.post("/predictions/{record_id}/comments")
async def add_comment(
    record_id: str,
    comment: CommentCreate,
    db: Session = Depends(get_db)
):
    new_comment = Comment(
        record_id=uuid.UUID(record_id),
        user_name=comment.user_name,
        text=comment.text
    )
    db.add(new_comment)
    db.commit()
    return {"status": "ok"}


@router.get("/predictions/{record_id}/comments")
async def get_comments(
    record_id: str,
    db: Session = Depends(get_db)
):
    comments = db.query(Comment).filter(Comment.record_id == uuid.UUID(record_id)).order_by(Comment.created_at.desc()).all()
    return [
        {"id": c.id, "user_name": c.user_name, "text": c.text, "created_at": c.created_at.isoformat()}
        for c in comments
    ]