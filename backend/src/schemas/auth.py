"""
schemas/auth.py — Pydantic contracts for the authentication API.
All /token endpoint inputs and outputs are validated here.
"""

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Response model for POST /api/v1/token."""
    access_token: str = Field(..., description="Signed JWT Bearer token")
    token_type: str = Field(default="bearer", description="Token scheme")


class LoginRequest(BaseModel):
    """
    Optional JSON-body login schema (for future non-form login flows).
    Currently the /token endpoint uses OAuth2PasswordRequestForm (form data).
    """
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)
