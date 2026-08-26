# app/models/content.py
from sqlalchemy import Column, String, Text, Integer, Boolean, Enum, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentCategory(BaseModel):
    __tablename__ = "content_categories"

    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    articles = relationship("ContentArticle", back_populates="category")


class ContentArticle(BaseModel):
    __tablename__ = "content_articles"

    category_id = Column(UUID(as_uuid=True), ForeignKey("content_categories.id"), nullable=False)
    pathway_id = Column(UUID(as_uuid=True), ForeignKey("immigration_pathways.id"), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    category = relationship("ContentCategory", back_populates="articles")
    pathway = relationship("ImmigrationPathway", backref="content_articles")
    versions = relationship("ContentVersion", back_populates="article", order_by="ContentVersion.version")


class ContentVersion(BaseModel):
    __tablename__ = "content_versions"

    article_id = Column(UUID(as_uuid=True), ForeignKey("content_articles.id"), nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    article = relationship("ContentArticle", back_populates="versions")