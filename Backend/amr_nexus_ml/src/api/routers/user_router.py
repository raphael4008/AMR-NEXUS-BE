from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.config import settings
from src.api.deps import get_db, get_current_user
from src.db.models import UserTemplate, User 

user_router = APIRouter()


@user_router.get("/profile")
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "assigned_county": current_user.assigned_county,
    }


@user_router.get("/templates", response_model=List[Dict[str, Any]])
def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    templates = db.query(UserTemplate).filter(
        UserTemplate.user_id == current_user.id
    ).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "form_data": t.form_data,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in templates
    ]


@user_router.post("/templates", response_model=Dict[str, Any])
def save_template(
    name: str,
    form_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:

    existing = db.query(UserTemplate).filter(
        UserTemplate.user_id == current_user.id,
        UserTemplate.name == name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A template with this name already exists."
        )
    template = UserTemplate(
        user_id=current_user.id,
        name=name,
        form_data=form_data
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return {
        "id": template.id,
        "name": template.name,
        "form_data": template.form_data,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    }


@user_router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    template = db.query(UserTemplate).filter(
        UserTemplate.id == template_id,
        UserTemplate.user_id == current_user.id
    ).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or does not belong to you."
        )
    db.delete(template)
    db.commit()
    return {"message": "Template deleted successfully."}