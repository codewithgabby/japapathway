# app/models/system.py
from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class SystemConfiguration(BaseModel):
    __tablename__ = "system_configurations"
    
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

class FeatureFlag(BaseModel):
    __tablename__ = "feature_flags"
    
    feature_name = Column(String(100), unique=True, index=True, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    description = Column(String(255), nullable=True)