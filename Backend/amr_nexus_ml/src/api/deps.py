from fastapi import Depends
from sqlalchemy.orm import Session
from src.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----- TEMPORARY STUB for development -----
def get_current_user(db: Session = Depends(get_db)):
    from src.db.models import User
    user = db.query(User).first()
    if not user:
        user = User(
            email="admin@amrnexus.com",
            name="Admin",
            hashed_password="dummy",
            role="admin"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
