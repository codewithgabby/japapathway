# app/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import setup_exception_handlers

from app.db.session import engine, AsyncSessionLocal

from app.api.v1 import (
    auth,
    sop,
    users,
    system,
    admin_sop,
    pathways,
    admin_pathways,
    documents,
    admin_documents,
    content,
    admin_content,
    dashboard,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ============================================================
    # Startup
    # ============================================================

    # Database schema is managed exclusively by Alembic.
    # Do NOT create tables automatically here.

    # Seed default data
    from app.db.seed import seed_database

    async with AsyncSessionLocal() as session:
        await seed_database(session)

    yield

    # ============================================================
    # Shutdown
    # ============================================================

    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

setup_exception_handlers(app)


# ============================================================
# PUBLIC ROUTERS
# ============================================================

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Users"],
)

app.include_router(
    system.router,
    prefix="/api/v1/system",
    tags=["System"],
)

app.include_router(
    pathways.router,
    prefix="/api/v1",
    tags=["Pathways"],
)

app.include_router(
    documents.router,
    prefix="/api/v1",
    tags=["Readiness"],
)

app.include_router(
    sop.router,
    prefix="/api/v1",
    tags=["SOP Builder"],
)

app.include_router(
    dashboard.router,
    prefix="/api/v1",
    tags=["Dashboard"],
)

# ============================================================
# CONTENT ENGINE
# ============================================================

app.include_router(
    content.router,
    prefix="/api/v1/content",
    tags=["Content Engine"],
)


# ============================================================
# ADMIN / WORKSPACE ROUTERS
# ============================================================

app.include_router(
    system.admin_router,
    prefix="/api/v1/admin",
    tags=["Workspace - System"],
)

app.include_router(
    admin_pathways.router,
    prefix="/api/v1/admin",
    tags=["Workspace - Pathways"],
)

app.include_router(
    admin_documents.router,
    prefix="/api/v1/admin",
    tags=["Workspace - Documents"],
)

app.include_router(
    admin_sop.router,
    prefix="/api/v1/admin",
    tags=["Workspace - SOP Builder"],
)

app.include_router(
    admin_content.router,
    prefix="/api/v1/admin",
    tags=["Workspace - Content Engine"],
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
    }