# app/schemas/content.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


def _uuid_to_str(v):
    """Convert UUID objects to strings for Pydantic serialization."""
    if isinstance(v, UUID):
        return str(v)
    return v


# ========== Content Category Schemas ==========

class ContentCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class ContentCategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ContentCategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    status: str
    version: int
    is_active: bool
    articles_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    _convert_ids = field_validator('id', mode='before')(_uuid_to_str)

    class Config:
        from_attributes = True


# ========== Content Article Schemas ==========

class ContentArticleCreate(BaseModel):
    category_id: str
    pathway_id: str
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    summary: Optional[str] = None
    content: Optional[str] = None


class ContentArticleUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None


class ContentArticleResponse(BaseModel):
    id: str
    category_id: str
    pathway_id: str
    title: str
    slug: str
    summary: Optional[str]
    content: Optional[str]
    status: str
    version: int
    is_active: bool
    category_name: Optional[str] = None
    pathway_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    _convert_ids = field_validator('id', 'category_id', 'pathway_id', mode='before')(_uuid_to_str)

    class Config:
        from_attributes = True


# ========== Content Version Schemas ==========

class ContentVersionResponse(BaseModel):
    id: str
    article_id: str
    version: int
    title: str
    summary: Optional[str]
    content: Optional[str]
    status: str
    created_at: Optional[datetime] = None

    _convert_ids = field_validator('id', 'article_id', mode='before')(_uuid_to_str)

    class Config:
        from_attributes = True


# ========== Status Update Schemas ==========

class ContentStatusUpdate(BaseModel):
    status: str = Field(..., description="draft, published, or archived")