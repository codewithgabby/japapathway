# app/api/v1/users.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.schemas.auth import UserResponse
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )