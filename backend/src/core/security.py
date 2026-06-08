from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from src.core.config import settings

# ── Constants ───────────────────────────────────────────────────────────────────
ROLE_NATIONAL_COORDINATOR = "National Coordinator"
ROLE_COUNTY_VETERINARIAN = "County Veterinarian"
ROLE_COUNTY_CLINICIAN = "County Clinician"

# ── Crypto context ──────────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token")


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


# ── Password helpers ─────────────────────────────────────────────────────────────
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ── Token generation ─────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ── Token verification ───────────────────────────────────────────────────────────
async def get_current_user_token(
    token: str = Depends(oauth2_scheme),
) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        return TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception


# ── Role-based access control ────────────────────────────────────────────────────
class RoleChecker:
    """
    Injectable FastAPI dependency for role-gated endpoints.

    Usage:
        @router.get("/endpoint")
        async def my_route(
            user: TokenData = Depends(RoleChecker(["County Veterinarian"]))
        ):
            ...

    National Coordinator always passes regardless of the allowed_roles list.
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, current_user: TokenData = Depends(get_current_user_token)
    ) -> TokenData:
        # National Coordinator has platform-wide superuser access (global systems bypass)
        if current_user.role == ROLE_NATIONAL_COORDINATOR:
            return current_user
            
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access restricted. Required roles: {self.allowed_roles}. "
                    f"Your role: {current_user.role}"
                ),
            )
            
        # If the claims match 'County Veterinarian' (or similar allowed scoped role), 
        # we enforce scoped resource validation limits by verifying the role passes.
        return current_user
