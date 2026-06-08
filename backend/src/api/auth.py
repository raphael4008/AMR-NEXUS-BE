from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.models.base import get_db
from src.models.entities import User
from src.core.security import create_access_token, verify_password

router = APIRouter()

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 1. Query the real PostgreSQL database for the user
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 2. Verify the user exists and the password matches the hash
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Generate the VIP Access Token
    token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {"access_token": token, "token_type": "bearer"}