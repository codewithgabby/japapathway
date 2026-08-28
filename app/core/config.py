from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from typing import List, Optional


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
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5500",
    ]

    # Admin Seed
    SUPERUSER_EMAIL: str
    SUPERUSER_PASSWORD: str

    # AI
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-5.6"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Return DATABASE_URL using the asyncpg PostgreSQL driver."""
        url = self.DATABASE_URL

        if url.startswith("postgres://"):
            return url.replace(
                "postgres://",
                "postgresql+asyncpg://",
                1,
            )

        if url.startswith("postgresql://"):
            return url.replace(
                "postgresql://",
                "postgresql+asyncpg://",
                1,
            )

        return url


settings = Settings()
