from fastapi import APIRouter
from src.core.security import create_access_token, ROLE_NATIONAL_COORDINATOR

router = APIRouter()

@router.post("/token")
async def login_for_access_token():
    # Placeholder for actual authentication logic
    # We generate a real JWT so tests and the frontend can pass RoleChecker
    token = create_access_token(data={"sub": "test_user", "role": ROLE_NATIONAL_COORDINATOR})
    return {"access_token": token, "token_type": "bearer"}
