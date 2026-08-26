# app/api/v1/auth.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse
)
from app.services.auth import AuthService
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user, access_token, refresh_token = await AuthService.register(
        db, request.email, request.password, request.full_name
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user, access_token, refresh_token = await AuthService.login(
        db, request.email, request.password
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    access_token, refresh_token = await AuthService.refresh_token(db, request.refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )