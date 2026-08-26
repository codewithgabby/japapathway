# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "JapaPathway"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    APP_DESCRIPTION: str = "Digital Immigration Journey Platform"
    
    # Database
    DATABASE_URL: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5500"]
    
    # Admin Seed
    SUPERUSER_EMAIL: str
    SUPERUSER_PASSWORD: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )  
    
settings = Settings()