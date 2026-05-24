"""
schemas/guidance.py — API contracts for Component C: LLM Advisory outputs.

Defines the request/response shapes for role-gated advisory generation
and retrieval endpoints on the intelligence router.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class GuidanceRequest(BaseModel):
    """Payload to trigger an LLM advisory generation for a specific alert + role."""
    alert_id: int = Field(..., description="ID of the Alert that triggered this advisory request")
    user_role: str = Field(
        ...,
        description='Target role for the advisory. One of: "National Coordinator", "County Veterinarian"',
        examples=["National Coordinator", "County Veterinarian"],
    )


class GuidanceResponse(BaseModel):
    """Serialized Guidance row returned after LLM generation."""
    id: int
    alert_id: int
    user_role: str
    guidance_markdown: Optional[str] = Field(
        None, description="Full role-specific markdown advisory brief from Claude"
    )
    status: str = Field(..., description="PENDING | APPROVED")
    generation_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Provenance: model name, token usage, generation timestamp"
    )
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class GuidanceListResponse(BaseModel):
    """Paginated list of guidance records for an alert."""
    alert_id: int
    total: int
    items: List[GuidanceResponse]
