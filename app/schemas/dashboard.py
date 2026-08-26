# app/schemas/dashboard.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


def _uuid_to_str(v):
    """Convert UUID objects to strings for Pydantic serialization."""
    if isinstance(v, UUID):
        return str(v)
    return v


# ========== User Section ==========

class DashboardUserResponse(BaseModel):
    full_name: str
    email: str
    user_id: str

    _convert_ids = field_validator("user_id", mode="before")(_uuid_to_str)

    class Config:
        from_attributes = True


# ========== Journey Section ==========

class DashboardJourneyNextStep(BaseModel):
    title: Optional[str] = None
    order: Optional[int] = None


class DashboardJourneyResponse(BaseModel):
    has_roadmap: bool = False
    pathway_name: Optional[str] = None
    pathway_slug: Optional[str] = None
    status: Optional[str] = None
    completed_steps: int = 0
    total_steps: int = 0
    completion_percentage: int = 0
    next_step: Optional[DashboardJourneyNextStep] = None


# ========== Readiness Section ==========

class DashboardReadinessResponse(BaseModel):
    has_checklist: bool = False
    pathway_name: Optional[str] = None
    completion_percentage: int = 0
    total_required: int = 0
    completed_required: int = 0
    missing_required: int = 0
    missing_documents: List[str] = Field(default_factory=list)


# ========== SOP/LOE Section ==========

class DashboardDraftInfo(BaseModel):
    draft_id: Optional[str] = None
    version: Optional[int] = None
    generation_status: Optional[str] = None
    warnings_count: int = 0
    missing_information_count: int = 0

    _convert_ids = field_validator("draft_id", mode="before")(_uuid_to_str)


class DashboardSOPDocumentResponse(BaseModel):
    document_id: str
    document_type: str
    title: Optional[str] = None
    status: str
    progress_percentage: int = 0
    answered_questions: int = 0
    total_questions: int = 0
    latest_draft: Optional[DashboardDraftInfo] = None

    _convert_ids = field_validator("document_id", mode="before")(_uuid_to_str)


# ========== Next Action Section ==========

class DashboardNextActionResponse(BaseModel):
    type: str
    title: str
    description: str
    priority: str = "normal"  # "high", "normal", "low"


# ========== Full Dashboard Response ==========

class DashboardResponse(BaseModel):
    user: DashboardUserResponse
    journey: DashboardJourneyResponse
    readiness: DashboardReadinessResponse
    sop_documents: List[DashboardSOPDocumentResponse] = Field(default_factory=list)
    next_action: DashboardNextActionResponse