# app/api/v1/system.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_admin_user
from app.services.system import SystemService
from app.schemas.system import (
    SystemConfigResponse,
    SystemConfigUpdate,
    FeatureFlagResponse,
    FeatureFlagToggle,
    PublicConfigResponse
)
from app.models.user import User
from typing import List

router = APIRouter()

@router.get("/config", response_model=PublicConfigResponse)
async def get_public_config(db: AsyncSession = Depends(get_db)):
    configs = await SystemService.get_public_configs(db)
    return PublicConfigResponse(**configs)

# Admin endpoints for system configuration
admin_router = APIRouter()

@admin_router.get("/config", response_model=List[SystemConfigResponse])
async def get_all_configs(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    configs = await SystemService.get_all_configs(db)
    return [SystemConfigResponse(
        key=c.key,
        value=c.value,
        category=c.category,
        description=c.description,
        updated_at=c.updated_at
    ) for c in configs]

@admin_router.put("/config/{key}", response_model=SystemConfigResponse)
async def update_config(
    key: str,
    update: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    config = await SystemService.update_config(
        db, key, update.value, str(admin.id), update.category, update.description
    )
    return SystemConfigResponse(
        key=config.key,
        value=config.value,
        category=config.category,
        description=config.description,
        updated_at=config.updated_at
    )

@admin_router.get("/features", response_model=List[FeatureFlagResponse])
async def get_features(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    features = await SystemService.get_all_features(db)
    return [FeatureFlagResponse(
        feature_name=f.feature_name,
        is_enabled=f.is_enabled,
        description=f.description,
        updated_at=f.updated_at
    ) for f in features]

@admin_router.put("/features/{feature_name}/toggle", response_model=FeatureFlagResponse)
async def toggle_feature(
    feature_name: str,
    toggle: FeatureFlagToggle,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    feature = await SystemService.toggle_feature(db, feature_name, toggle.is_enabled)
    return FeatureFlagResponse(
        feature_name=feature.feature_name,
        is_enabled=feature.is_enabled,
        description=feature.description,
        updated_at=feature.updated_at
    )