# app/schemas/document.py
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# ========== Document Category Schemas ==========

class DocumentCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class DocumentCategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class DocumentCategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    sort_order: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Document Type Schemas ==========

class DocumentTypeCreate(BaseModel):
    category_id: str
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True


class DocumentTypeUpdate(BaseModel):
    category_id: Optional[str] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DocumentTypeResponse(BaseModel):
    id: str
    category_id: str
    category_name: Optional[str] = None
    name: str
    slug: str
    description: Optional[str]
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Pathway Document Requirement Schemas ==========

class PathwayDocumentRequirementCreate(BaseModel):
    pathway_id: str
    document_type_id: str
    is_required: bool = True
    is_active: bool = True
    instructions: Optional[str] = None
    display_order: int = 0


class PathwayDocumentRequirementUpdate(BaseModel):
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    instructions: Optional[str] = None
    display_order: Optional[int] = None


class PathwayDocumentRequirementResponse(BaseModel):
    id: str
    pathway_id: str
    document_type_id: str
    document_name: Optional[str] = None
    category_name: Optional[str] = None
    is_required: bool
    is_active: bool
    instructions: Optional[str]
    display_order: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== User Document Checklist Schemas ==========

class UserDocumentStatusUpdate(BaseModel):
    status: Literal["ready", "not_ready"]
    notes: Optional[str] = None


class UserDocumentChecklistItemResponse(BaseModel):
    id: str
    requirement_id: str
    document_type_id: str
    document_name: str
    category_name: Optional[str]
    is_required: bool
    instructions: Optional[str]
    display_order: int
    status: str
    notes: Optional[str]

    class Config:
        from_attributes = True


class UserDocumentReadinessSummaryResponse(BaseModel):
    pathway_id: str
    pathway_name: str
    pathway_slug: str
    total_required: int
    completed_required: int
    missing_required: int
    total_optional: int
    completed_optional: int
    completion_percentage: int
    missing_documents: List[str] = []
    recommendations: List[str] = []

    class Config:
        from_attributes = True