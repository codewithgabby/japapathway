# app/schemas/system.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class SystemConfigResponse(BaseModel):
    key: str
    value: str
    category: str
    description: Optional[str]
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SystemConfigUpdate(BaseModel):
    value: str
    category: Optional[str] = None
    description: Optional[str] = None

class FeatureFlagResponse(BaseModel):
    feature_name: str
    is_enabled: bool
    description: Optional[str]
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FeatureFlagToggle(BaseModel):
    is_enabled: bool

class PublicConfigResponse(BaseModel):
    branding: Dict[str, Any]
    contact: Dict[str, Any]
    legal: Dict[str, Any]
    social: Dict[str, Any]