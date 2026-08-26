# app/schemas/pathway.py

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.pathway import (
    StepStatus,
    PathwayStatus,
    UserRoadmapStatus,
)


# ============================================================
# Roadmap Step Schemas
# ============================================================

class RoadmapStepCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    step_order: int
    estimated_duration_days: Optional[int] = None
    is_required: bool = True


class RoadmapStepUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    step_order: Optional[int] = None
    estimated_duration_days: Optional[int] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None


class RoadmapStepResponse(BaseModel):
    id: UUID
    pathway_id: UUID
    title: str
    slug: str
    description: Optional[str]
    step_order: int
    estimated_duration_days: Optional[int]
    is_required: bool
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# Immigration Pathway Schemas
# ============================================================

class PathwayCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    country: str = "Canada"
    category: str
    steps: List[RoadmapStepCreate] = Field(default_factory=list)


class PathwayUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PathwayResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    country: str
    icon: Optional[str]
    color: Optional[str]
    category: str
    status: PathwayStatus
    version: int
    sort_order: int
    is_active: bool
    steps_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PathwayDetailResponse(PathwayResponse):
    steps: List[RoadmapStepResponse] = Field(default_factory=list)


# ============================================================
# User Roadmap Schemas
# ============================================================

class UserRoadmapStartRequest(BaseModel):
    pathway_id: UUID


class UserRoadmapStepUpdate(BaseModel):
    status: StepStatus
    notes: Optional[str] = None


class UserRoadmapStepResponse(BaseModel):
    id: UUID
    roadmap_step_id: UUID
    step_title: str
    step_slug: str
    step_order: int
    description: Optional[str]
    estimated_duration_days: Optional[int]
    status: StepStatus
    completed_at: Optional[datetime]
    notes: Optional[str]

    class Config:
        from_attributes = True


class UserRoadmapResponse(BaseModel):
    id: UUID
    pathway_id: UUID
    pathway_name: str
    pathway_slug: str
    status: UserRoadmapStatus
    progress_percentage: int
    steps: List[UserRoadmapStepResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UserRoadmapSummaryResponse(BaseModel):
    id: UUID
    pathway_name: str
    pathway_slug: str
    status: UserRoadmapStatus
    progress_percentage: int

    class Config:
        from_attributes = True


# ============================================================
# Reorder Schemas
# ============================================================

class StepReorderRequest(BaseModel):
    step_id: UUID
    new_order: int


class StepsReorderRequest(BaseModel):
    steps: List[StepReorderRequest]