import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.api.deps import get_db
from src.api.schemas import CommentCreate
from src.db.models import Comment

comments_router = APIRouter()


@comments_router.post(
    "/predictions/{record_id}/comments", status_code=status.HTTP_201_CREATED
)
def create_record_comment(
    record_id: str, comment: CommentCreate, db: Session = Depends(get_db)
) -> Dict[str, str]:
    try:
        new_comment = Comment(
            record_id=uuid.UUID(record_id),
            user_name=comment.user_name,
            text=comment.text,
        )
        db.add(new_comment)
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@comments_router.get("/predictions/{record_id}/comments")
def read_record_comments(
    record_id: str, db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    try:
        comments = (
            db.query(Comment)
            .filter(Comment.record_id == uuid.UUID(record_id))
            .all()
        )
        return [
            {
                "id": c.id,
                "user_name": c.user_name,
                "text": c.text,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
