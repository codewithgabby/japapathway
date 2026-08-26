# app/schemas/sop.py

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.sop import (
    DocumentTemplateStatus,
    DocumentType,
    ApplicantDocumentStatus,
    QuestionType,
    GenerationStatus,
)


def _uuid_to_str(v):
    """Convert UUID objects to strings for Pydantic serialization."""
    if isinstance(v, UUID):
        return str(v)
    return v


# ============================================================
# Document Template Schemas
# ============================================================

class DocumentTemplateCreate(BaseModel):
    pathway_id: str
    document_type: DocumentType
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    admin_guidance: Optional[str] = None
    ai_guidance: Optional[str] = None


class DocumentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    admin_guidance: Optional[str] = None
    ai_guidance: Optional[str] = None
    is_active: Optional[bool] = None


class DocumentTemplateResponse(BaseModel):
    id: str
    pathway_id: str
    document_type: DocumentType
    name: str
    slug: str
    description: Optional[str]
    status: DocumentTemplateStatus
    version: int
    admin_guidance: Optional[str]
    ai_guidance: Optional[str]
    is_active: bool
    sections_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    _convert_ids = field_validator(
        "id", "pathway_id", mode="before"
    )(_uuid_to_str)

    class Config:
        from_attributes = True


class DocumentTemplateDetailResponse(DocumentTemplateResponse):
    sections: List["DocumentTemplateSectionResponse"] = Field(
        default_factory=list
    )


# ============================================================
# Section Schemas
# ============================================================

class DocumentTemplateSectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    purpose: Optional[str] = None
    order_index: int
    admin_guidance: Optional[str] = None
    ai_guidance: Optional[str] = None


class DocumentTemplateSectionUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    order_index: Optional[int] = None
    admin_guidance: Optional[str] = None
    ai_guidance: Optional[str] = None
    is_active: Optional[bool] = None


class DocumentTemplateSectionResponse(BaseModel):
    id: str
    template_id: str
    name: str
    slug: str
    description: Optional[str]
    purpose: Optional[str]
    order_index: int
    admin_guidance: Optional[str]
    ai_guidance: Optional[str]
    is_active: bool
    questions_count: Optional[int] = 0
    created_at: Optional[datetime] = None

    _convert_ids = field_validator(
        "id", "template_id", mode="before"
    )(_uuid_to_str)

    class Config:
        from_attributes = True


class DocumentTemplateSectionDetailResponse(
    DocumentTemplateSectionResponse
):
    questions: List["DocumentTemplateQuestionResponse"] = Field(
        default_factory=list
    )


# ============================================================
# Question Schemas
# ============================================================

class DocumentTemplateQuestionCreate(BaseModel):
    question_text: str = Field(min_length=1)
    question_type: QuestionType = QuestionType.LONG_TEXT
    help_text: Optional[str] = None
    placeholder: Optional[str] = None
    admin_guidance: Optional[str] = None
    ai_guidance: Optional[str] = None
    is_required: bool = True
    order_index: int


class DocumentTemplateQuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    help_text: Optional[str] = None
    placeholder: Optional[str] = None
    admin_guidance: Optional[str] = None
    ai_guidance: Optional[str] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    order_index: Optional[int] = None


class DocumentTemplateQuestionResponse(BaseModel):
    id: str
    section_id: str
    question_text: str
    question_type: QuestionType
    help_text: Optional[str]
    placeholder: Optional[str]
    admin_guidance: Optional[str]
    ai_guidance: Optional[str]
    is_required: bool
    is_active: bool
    order_index: int

    _convert_ids = field_validator(
        "id", "section_id", mode="before"
    )(_uuid_to_str)

    class Config:
        from_attributes = True


# ============================================================
# Applicant Document Schemas
# ============================================================

class ApplicantDocumentCreate(BaseModel):
    pathway_id: str
    template_id: str
    document_type: DocumentType
    title: Optional[str] = None
    reason: Optional[str] = None


class ApplicantDocumentResponseSchema(BaseModel):
    id: str
    user_id: str
    pathway_id: str
    template_id: str
    document_type: DocumentType
    status: ApplicantDocumentStatus
    version: int
    current_section_order: int
    title: Optional[str]
    reason: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    _convert_ids = field_validator(
        "id",
        "user_id",
        "pathway_id",
        "template_id",
        mode="before",
    )(_uuid_to_str)

    class Config:
        from_attributes = True


class ApplicantDocumentDetailResponse(
    ApplicantDocumentResponseSchema
):
    responses: List["ApplicantAnswerResponse"] = Field(
        default_factory=list
    )
    drafts: List["ApplicantDraftResponse"] = Field(
        default_factory=list
    )


# ============================================================
# Applicant Answer Schemas
# ============================================================

class ApplicantAnswerCreate(BaseModel):
    question_id: str
    answer_text: str = Field(min_length=1)


class ApplicantAnswersBatchCreate(BaseModel):
    answers: List[ApplicantAnswerCreate]


class ApplicantAnswerUpdate(BaseModel):
    answer_text: str = Field(min_length=1)


class ApplicantAnswerResponse(BaseModel):
    id: str
    question_id: str
    question_text: Optional[str] = None
    answer_text: Optional[str]
    is_required: Optional[bool] = None
    is_answered: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    _convert_ids = field_validator(
        "id", "question_id", mode="before"
    )(_uuid_to_str)

    class Config:
        from_attributes = True


# ============================================================
# Draft Schemas
# ============================================================

class ApplicantDraftResponse(BaseModel):
    id: str
    section_id: str
    section_name: Optional[str] = None
    content: Optional[str]
    ai_provider: Optional[str]
    ai_model: Optional[str]
    version: int
    is_current: bool

    generation_status: Optional[GenerationStatus] = None
    missing_information: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    knowledge_sources: Optional[List[Dict[str, Any]]] = None
    source_draft_id: Optional[str] = None
    generation_metadata: Optional[Dict[str, Any]] = None

    created_at: Optional[datetime] = None

    _convert_ids = field_validator(
        "id",
        "section_id",
        "source_draft_id",
        mode="before",
    )(_uuid_to_str)

    class Config:
        from_attributes = True


# ============================================================
# Sprint 6 — AI Generation Request Schemas
# ============================================================

class GenerateDraftRequest(BaseModel):
    section_id: str


class RegenerateDraftRequest(BaseModel):
    section_id: str
    instruction: Optional[str] = None


class ImproveDraftRequest(BaseModel):
    section_id: str
    instruction: str = Field(min_length=1)


class FinalizeDraftRequest(BaseModel):
    draft_id: str


# ============================================================
# Sprint 6 — AI Generation Response Schemas
# ============================================================

class GenerateDraftResponse(BaseModel):
    status: str
    content: Optional[str] = None
    missing_information: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    knowledge_sources: Optional[List[Dict[str, Any]]] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    draft_id: Optional[str] = None
    draft_version: Optional[int] = None
    draft: Optional[Dict[str, Any]] = None
    generation_status: Optional[str] = None

class FinalizeDraftResponse(BaseModel):
    status: str
    document_status: ApplicantDocumentStatus
    draft_id: str
    draft_version: int
    message: str


# ============================================================
# Existing Draft Request Schemas
# ============================================================

class DraftRegenerateRequest(BaseModel):
    section_id: str


class DraftFinalizeRequest(BaseModel):
    section_id: str


# ============================================================
# Progress Schemas
# ============================================================

class ApplicantDocumentProgressResponse(BaseModel):
    document_id: str
    document_type: DocumentType
    status: str
    total_sections: int
    completed_sections: int
    total_questions: int
    answered_questions: int
    progress_percentage: int
    current_section_order: int

    class Config:
        from_attributes = True


# ============================================================
# Relationship Schemas
# ============================================================

class DocumentRelationshipCreate(BaseModel):
    related_document_id: str
    relationship_type: str = "related"


class DocumentRelationshipResponse(BaseModel):
    id: str
    source_document_id: str
    related_document_id: str
    relationship_type: str
    created_at: Optional[datetime] = None

    _convert_ids = field_validator(
        "id",
        "source_document_id",
        "related_document_id",
        mode="before",
    )(_uuid_to_str)

    class Config:
        from_attributes = True