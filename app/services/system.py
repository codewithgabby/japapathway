# app/services/system.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from app.models.system import SystemConfiguration, FeatureFlag
from app.core.exceptions import NotFoundException

class SystemService:
    @staticmethod
    async def get_public_configs(db: AsyncSession) -> Dict[str, Dict[str, Any]]:
        result = await db.execute(
            select(SystemConfiguration).where(
                SystemConfiguration.is_public.is_(True),
                SystemConfiguration.is_deleted.is_(False)
            )
        )
        configs = result.scalars().all()
        
        public_config = {
            "branding": {},
            "contact": {},
            "legal": {},
            "social": {},
            "footer": {},
            "seo": {}
        }
        
        for config in configs:
            if config.category in public_config:
                public_config[config.category][config.key] = config.value
        
        return public_config
    
    @staticmethod
    async def get_all_configs(db: AsyncSession) -> List[SystemConfiguration]:
        result = await db.execute(
            select(SystemConfiguration).where(SystemConfiguration.is_deleted.is_(False))
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_config(
        db: AsyncSession, key: str, value: str, user_id: str,
        category: Optional[str] = None, description: Optional[str] = None
    ) -> SystemConfiguration:
        result = await db.execute(
            select(SystemConfiguration).where(
                SystemConfiguration.key == key,
                SystemConfiguration.is_deleted.is_(False)
            )
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise NotFoundException("Configuration")
        
        config.value = value
        config.updated_by = user_id
        if category:
            config.category = category
        if description:
            config.description = description
        
        await db.flush()
        await db.refresh(config)
        return config
    
    @staticmethod
    async def seed_default_configs(db: AsyncSession) -> None:
        defaults = [
            {"key": "app_name", "value": "APP_NAME", "category": "branding", "description": "Application name", "is_public": True},
            {"key": "logo_url", "value": "/assets/logo.svg", "category": "branding", "description": "Logo URL", "is_public": True},
            {"key": "favicon_url", "value": "/assets/favicon.ico", "category": "branding", "description": "Favicon URL", "is_public": True},
            {"key": "primary_color", "value": "#4F46E5", "category": "branding", "description": "Primary brand color", "is_public": True},
            {"key": "secondary_color", "value": "#818CF8", "category": "branding", "description": "Secondary brand color", "is_public": True},
            {"key": "accent_color", "value": "#C7D2FE", "category": "branding", "description": "Accent color", "is_public": True},
            {"key": "support_email", "value": "support@appname.com", "category": "contact", "description": "Support email", "is_public": True},
            {"key": "support_phone", "value": "", "category": "contact", "description": "Support phone", "is_public": True},
            {"key": "contact_address", "value": "", "category": "contact", "description": "Physical address", "is_public": True},
            {"key": "terms_url", "value": "/terms", "category": "legal", "description": "Terms of service URL", "is_public": True},
            {"key": "privacy_url", "value": "/privacy", "category": "legal", "description": "Privacy policy URL", "is_public": True},
            {"key": "refund_policy_url", "value": "/refund-policy", "category": "legal", "description": "Refund policy URL", "is_public": True},
            {"key": "facebook_url", "value": "", "category": "social", "description": "Facebook URL", "is_public": True},
            {"key": "twitter_url", "value": "", "category": "social", "description": "Twitter URL", "is_public": True},
            {"key": "linkedin_url", "value": "", "category": "social", "description": "LinkedIn URL", "is_public": True},
            {"key": "instagram_url", "value": "", "category": "social", "description": "Instagram URL", "is_public": True},
            {"key": "footer_text", "value": "© 2024 APP_NAME. All rights reserved.", "category": "footer", "description": "Footer text", "is_public": True},
            {"key": "copyright_text", "value": "APP_NAME", "category": "footer", "description": "Copyright text", "is_public": True},
            {"key": "meta_title", "value": "APP_NAME - Digital Immigration Journey Platform", "category": "seo", "description": "Meta title", "is_public": True},
            {"key": "meta_description", "value": "Your digital immigration journey platform", "category": "seo", "description": "Meta description", "is_public": True},
        ]
        
        for config_data in defaults:
            result = await db.execute(
                select(SystemConfiguration).where(SystemConfiguration.key == config_data["key"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                config = SystemConfiguration(**config_data)
                db.add(config)
        
        await db.flush()
    
    @staticmethod
    async def get_all_features(db: AsyncSession) -> List[FeatureFlag]:
        result = await db.execute(
            select(FeatureFlag).where(FeatureFlag.is_deleted.is_(False))
        )
        return result.scalars().all()
    
    @staticmethod
    async def is_feature_enabled(db: AsyncSession, feature_name: str) -> bool:
        result = await db.execute(
            select(FeatureFlag).where(
                FeatureFlag.feature_name == feature_name,
                FeatureFlag.is_deleted.is_(False)
            )
        )
        feature = result.scalar_one_or_none()
        
        if not feature:
            return False
        
        return feature.is_enabled
    
    @staticmethod
    async def toggle_feature(db: AsyncSession, feature_name: str, is_enabled: bool) -> FeatureFlag:
        result = await db.execute(
            select(FeatureFlag).where(
                FeatureFlag.feature_name == feature_name,
                FeatureFlag.is_deleted.is_(False)
            )
        )
        feature = result.scalar_one_or_none()
        
        if not feature:
            raise NotFoundException("Feature flag")
        
        feature.is_enabled = is_enabled
        await db.flush()
        await db.refresh(feature)
        return feature
    
    @staticmethod
    async def seed_default_features(db: AsyncSession) -> None:
        features = [
            {"feature_name": "sop_builder", "is_enabled": True, "description": "SOP Builder module"},
            {"feature_name": "consultation_booking", "is_enabled": True, "description": "Consultation booking module"},
            {"feature_name": "readiness_checker", "is_enabled": True, "description": "Document readiness checker"},
            {"feature_name": "journey_builder", "is_enabled": True, "description": "Immigration journey builder"},
            {"feature_name": "content_engine", "is_enabled": True, "description": "Content engine / knowledge base"},
            {"feature_name": "ai_sop_generation", "is_enabled": True, "description": "AI-powered SOP generation"},
        ]
        
        for feature_data in features:
            result = await db.execute(
                select(FeatureFlag).where(FeatureFlag.feature_name == feature_data["feature_name"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                feature = FeatureFlag(**feature_data)
                db.add(feature)
        
        await db.flush()