"""
api/auth.py — AMR-Nexus Authentication Router

Security hardening:
  1. Async SQLAlchemy 2.0 — no sync blocking
  2. Dummy-hash constant-time — prevents username enumeration via timing
  3. Pydantic response_model — typed contract
  4. SlowAPI rate limit — 10 attempts/minute per IP on /token
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.base import get_db
from src.models.entities import User
from src.core.security import (
    create_access_token,
    verify_password,
    _DUMMY_HASH,
)
from src.core.rate_limiter import limiter
from src.schemas.auth import TokenResponse

logger = logging.getLogger("amr_nexus.api.auth")
router = APIRouter()


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Obtain a Bearer access token",
    description=(
        "Authenticates via username + password form data. "
        "Rate-limited to 10 attempts per minute per IP. "
        "Responds in constant time regardless of whether the username exists."
    ),
)
@limiter.limit("10/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Issues a signed JWT on successful authentication.

    Security notes:
    - Always runs bcrypt verify_password() even when the user is not found
      (_DUMMY_HASH) to prevent username enumeration via response-time analysis.
    - Returns HTTP 401 with identical generic message for both 'user not found'
      and 'wrong password' — no information leakage.
    """
    # 1. Async DB lookup
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()

    # 2. Constant-time bcrypt — always runs regardless of user existence
    candidate_hash = user.hashed_password if user else _DUMMY_HASH
    password_ok = verify_password(form_data.password, candidate_hash)

    # 3. Unified 401 — same message for 'no user' and 'wrong password'
    if not user or not user.is_active or not password_ok:
        logger.warning("Failed login attempt for username=%r", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Issue signed JWT with role claim
    token = create_access_token(data={"sub": user.username, "role": user.role})
    logger.info("Successful login for username=%r role=%r", user.username, user.role)
    return TokenResponse(access_token=token)