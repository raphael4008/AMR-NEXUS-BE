"""
api/users.py — AMR-Nexus User Profile & Preferences Router v2.2

Endpoints:
  GET  /api/v1/users/me               — Returns authenticated user's profile
  PUT  /api/v1/users/me               — Updates name/email
  GET  /api/v1/users/me/preferences   — Returns notification + retention preferences
  PUT  /api/v1/users/me/preferences   — Saves notification + retention preferences

All data sourced from the database — no hardcoded or mock values.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from src.models.base import get_db
from src.models.entities import User
from src.core.security import RoleChecker, TokenData

logger = logging.getLogger("amr_nexus.api.users")
router = APIRouter(tags=["User Profile"])


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class UserProfileResponse(BaseModel):
    username: str
    name:     Optional[str] = None
    email:    Optional[str] = None
    role:     Optional[str] = None
    county:   Optional[str] = None
    is_active: bool = True


class UserProfileUpdate(BaseModel):
    name:  Optional[str] = None
    email: Optional[str] = None


class UserPreferences(BaseModel):
    anomaly_alerts:     bool = True
    high_mdr_alerts:    bool = True
    weekly_report:      bool = False
    retention_days:     int  = 365
    report_format:      str  = "pdf"
    report_schedule:    str  = "weekly"


# ── GET /users/me ─────────────────────────────────────────────────────────────

@router.get("/users/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(RoleChecker(["National Coordinator", "County Veterinarian", "County Clinician"])),
) -> UserProfileResponse:
    """Returns the authenticated user's profile from the database."""
    result = await db.execute(select(User).where(User.username == current_user.username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User profile not found.")

    return UserProfileResponse(
        username=user.username,
        name=user.name,
        email=user.email,
        role=user.role,
        county=user.county,
        is_active=user.is_active,
    )


# ── PUT /users/me ─────────────────────────────────────────────────────────────

@router.put("/users/me", response_model=UserProfileResponse)
async def update_user_profile(
    payload:      UserProfileUpdate,
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(RoleChecker(["National Coordinator", "County Veterinarian", "County Clinician"])),
) -> UserProfileResponse:
    """Updates name and/or email for the authenticated user."""
    result = await db.execute(select(User).where(User.username == current_user.username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User profile not found.")

    update_values: Dict[str, Any] = {}
    if payload.name is not None:
        update_values["name"] = payload.name
    if payload.email is not None:
        update_values["email"] = payload.email

    if update_values:
        await db.execute(
            update(User)
            .where(User.username == current_user.username)
            .values(**update_values)
        )
        await db.commit()
        await db.refresh(user)

    logger.info("Profile updated for user %s", current_user.username)

    return UserProfileResponse(
        username=user.username,
        name=user.name,
        email=user.email,
        role=user.role,
        county=user.county,
        is_active=user.is_active,
    )


# ── GET /users/me/preferences ─────────────────────────────────────────────────

@router.get("/users/me/preferences", response_model=UserPreferences)
async def get_user_preferences(
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(RoleChecker(["National Coordinator", "County Veterinarian", "County Clinician"])),
) -> UserPreferences:
    """Returns notification and data preferences from the database."""
    result = await db.execute(select(User).where(User.username == current_user.username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Preferences stored as JSON in user.preferences column
    prefs = user.preferences or {}
    return UserPreferences(
        anomaly_alerts=prefs.get("anomaly_alerts", True),
        high_mdr_alerts=prefs.get("high_mdr_alerts", True),
        weekly_report=prefs.get("weekly_report", False),
        retention_days=prefs.get("retention_days", 365),
        report_format=prefs.get("report_format", "pdf"),
        report_schedule=prefs.get("report_schedule", "weekly"),
    )


# ── PUT /users/me/preferences ─────────────────────────────────────────────────

@router.put("/users/me/preferences", response_model=UserPreferences)
async def save_user_preferences(
    payload:      UserPreferences,
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(RoleChecker(["National Coordinator", "County Veterinarian", "County Clinician"])),
) -> UserPreferences:
    """Persists user notification and data preferences to the database."""
    result = await db.execute(select(User).where(User.username == current_user.username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    await db.execute(
        update(User)
        .where(User.username == current_user.username)
        .values(preferences=payload.model_dump())
    )
    await db.commit()
    logger.info("Preferences saved for user %s", current_user.username)
    return payload
