from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.core.security import (
    create_access_token, 
    verify_password, 
    get_password_hash, 
    ROLE_NATIONAL_COORDINATOR, 
    ROLE_COUNTY_VETERINARIAN
)

router = APIRouter()

# Static user database for proof-of-concept
DEMO_USERS = {
    "national_admin": {
        "password_hash": get_password_hash("admin123"),
        "role": ROLE_NATIONAL_COORDINATOR
    },
    "county_vet_kiambu": {
        "password_hash": get_password_hash("vet123"),
        "role": ROLE_COUNTY_VETERINARIAN
    }
}

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = DEMO_USERS.get(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token(
        data={"sub": form_data.username, "role": user["role"]}
    )
    return {"access_token": token, "token_type": "bearer"}
