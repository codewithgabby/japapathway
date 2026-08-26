# app/models/sop.py
from sqlalchemy import Column, String, Text, Integer, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class DocumentTemplateStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DocumentType(str, enum.Enum):
    SOP = "sop"
    LOE = "loe"


class ApplicantDocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    GENERATING = "generating"
    GENERATED = "generated"
    UNDER_REVIEW = "under_review"
    FINAL = "final"


class QuestionType(str, enum.Enum):
    TEXT = "text"
    LONG_TEXT = "long_text"


class GenerationStatus(str, enum.Enum):
    GENERATED = "generated"
    NEEDS_CLARIFICATION = "needs_clarification"
    FAILED = "failed"


class DocumentTemplate(BaseModel):
    __tablename__ = "document_templates"

    pathway_id = Column(UUID(as_uuid=True), ForeignKey("immigration_pathways.id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(DocumentTemplateStatus), default=DocumentTemplateStatus.DRAFT, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    admin_guidance = Column(Text, nullable=True)
    ai_guidance = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    pathway = relationship("ImmigrationPathway", backref="document_templates")
    sections = relationship("DocumentTemplateSection", back_populates="template", order_by="DocumentTemplateSection.order_index")
    applicant_documents = relationship("ApplicantDocument", back_populates="template")


class DocumentTemplateSection(BaseModel):
    __tablename__ = "document_template_sections"

    template_id = Column(UUID(as_uuid=True), ForeignKey("document_templates.id"), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    purpose = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)
    admin_guidance = Column(Text, nullable=True)
    ai_guidance = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    template = relationship("DocumentTemplate", back_populates="sections")
    questions = relationship("DocumentTemplateQuestion", back_populates="section", order_by="DocumentTemplateQuestion.order_index")


class DocumentTemplateQuestion(BaseModel):
    __tablename__ = "document_template_questions"

    section_id = Column(UUID(as_uuid=True), ForeignKey("document_template_sections.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), default=QuestionType.LONG_TEXT, nullable=False)
    help_text = Column(Text, nullable=True)
    placeholder = Column(Text, nullable=True)
    admin_guidance = Column(Text, nullable=True)
    ai_guidance = Column(Text, nullable=True)
    is_required = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    order_index = Column(Integer, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    section = relationship("DocumentTemplateSection", back_populates="questions")
    responses = relationship("ApplicantDocumentResponse", back_populates="question")


class ApplicantDocument(BaseModel):
    __tablename__ = "applicant_documents"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pathway_id = Column(UUID(as_uuid=True), ForeignKey("immigration_pathways.id"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("document_templates.id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    status = Column(Enum(ApplicantDocumentStatus), default=ApplicantDocumentStatus.DRAFT, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    current_section_order = Column(Integer, default=0, nullable=False)
    title = Column(String(255), nullable=True)  # e.g., "LOE - Study Gap"
    reason = Column(Text, nullable=True)  # For LOE: what this LOE explains

    # Relationships
    template = relationship("DocumentTemplate", back_populates="applicant_documents")
    responses = relationship("ApplicantDocumentResponse", back_populates="applicant_document")
    drafts = relationship(
        "ApplicantDocumentDraft",
        back_populates="applicant_document",
        order_by="ApplicantDocumentDraft.created_at",
    )
    related_documents = relationship(
        "ApplicantDocumentRelationship",
        foreign_keys="ApplicantDocumentRelationship.source_document_id",
        back_populates="source_document",
    )
    source_relationships = relationship(
        "ApplicantDocumentRelationship",
        foreign_keys="ApplicantDocumentRelationship.related_document_id",
        back_populates="related_document",
    )

class ApplicantDocumentResponse(BaseModel):
    __tablename__ = "applicant_document_responses"

    applicant_document_id = Column(UUID(as_uuid=True), ForeignKey("applicant_documents.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("document_template_questions.id"), nullable=False)
    answer_text = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    applicant_document = relationship("ApplicantDocument", back_populates="responses")
    question = relationship("DocumentTemplateQuestion", back_populates="responses")

class ApplicantDocumentDraft(BaseModel):
    __tablename__ = "applicant_document_drafts"

    applicant_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applicant_documents.id"),
        nullable=False,
    )
    section_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_template_sections.id"),
        nullable=False,
    )
    content = Column(Text, nullable=True)
    ai_provider = Column(String(100), nullable=True)
    ai_model = Column(String(100), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)

    # Sprint 6 — AI generation metadata
    generation_status = Column(
        Enum(GenerationStatus),
        default=GenerationStatus.GENERATED,
        nullable=False,
    )
    missing_information = Column(JSONB, nullable=True)
    warnings = Column(JSONB, nullable=True)
    knowledge_sources = Column(JSONB, nullable=True)
    source_draft_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applicant_document_drafts.id"),
        nullable=True,
    )
    generation_metadata = Column(JSONB, nullable=True)

    # Relationships
    applicant_document = relationship(
       "ApplicantDocument",
       back_populates="drafts",
    )
    section = relationship("DocumentTemplateSection")


class ApplicantDocumentRelationship(BaseModel):
    __tablename__ = "applicant_document_relationships"

    source_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applicant_documents.id"),
        nullable=False,
    )
    related_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applicant_documents.id"),
        nullable=False,
    )
    relationship_type = Column(
        String(50),
        default="related",
        nullable=False,
    )

    # Relationships
    source_document = relationship(
        "ApplicantDocument",
        foreign_keys=[source_document_id],
        back_populates="related_documents",
    )
    related_document = relationship(
        "ApplicantDocument",
        foreign_keys=[related_document_id],
        back_populates="source_relationships",
    )