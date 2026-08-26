# app/models/document.py
from sqlalchemy import Column, String, Text, Integer, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class DocumentCategory(BaseModel):
    __tablename__ = "document_categories"

    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    document_types = relationship("DocumentType", back_populates="category")


class DocumentType(BaseModel):
    __tablename__ = "document_types"

    category_id = Column(UUID(as_uuid=True), ForeignKey("document_categories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    category = relationship("DocumentCategory", back_populates="document_types")
    requirements = relationship("PathwayDocumentRequirement", back_populates="document_type")


class PathwayDocumentRequirement(BaseModel):
    __tablename__ = "pathway_document_requirements"

    pathway_id = Column(UUID(as_uuid=True), ForeignKey("immigration_pathways.id"), nullable=False)
    document_type_id = Column(UUID(as_uuid=True), ForeignKey("document_types.id"), nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    instructions = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    document_type = relationship("DocumentType", back_populates="requirements")
    pathway = relationship("ImmigrationPathway", backref="document_requirements")
    user_checks = relationship("UserDocumentChecklist", back_populates="requirement")


class UserDocumentChecklist(BaseModel):
    __tablename__ = "user_document_checklists"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pathway_id = Column(UUID(as_uuid=True), ForeignKey("immigration_pathways.id"), nullable=False)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("pathway_document_requirements.id"), nullable=False)
    status = Column(String(50), default="not_ready", nullable=False)  # ready, not_ready
    notes = Column(Text, nullable=True)

    # Relationships
    requirement = relationship("PathwayDocumentRequirement", back_populates="user_checks")