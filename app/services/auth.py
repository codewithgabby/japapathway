# app/services/auth.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Tuple
from app.models.user import User, UserRole
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.exceptions import UnauthorizedException, BadRequestException, NotFoundException

class AuthService:
    @staticmethod
    async def register(db: AsyncSession, email: str, password: str, full_name: str) -> Tuple[User, str, str]:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email, User.is_deleted.is_(False)))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise BadRequestException("Email already registered")
        
        # Create user
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role=UserRole.APPLICANT
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

        await db.commit()

        access_token = create_access_token(
            {"sub": str(user.id), "role": user.role.value}
        )
        refresh_token = create_refresh_token(
            {"sub": str(user.id)}
        )
        
        return user, access_token, refresh_token
    
    @staticmethod
    async def login(db: AsyncSession, email: str, password: str) -> Tuple[User, str, str]:
        result = await db.execute(
            select(User).where(User.email == email, User.is_deleted.is_(False))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise UnauthorizedException("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")
        
        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")
        
        access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return user, access_token, refresh_token
    
    @staticmethod
    async def refresh_token(db: AsyncSession, refresh_token_str: str) -> Tuple[str, str]:
        payload = decode_token(refresh_token_str)
        
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")
        
        user_id = payload.get("sub")
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.is_deleted.is_(False),
                User.is_active.is_(True),
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise UnauthorizedException("User not found")
        
        new_access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
        new_refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return new_access_token, new_refresh_token
    
    @staticmethod
    async def get_current_user(db: AsyncSession, user_id: str) -> User:
        result = await db.execute(
            select(User).where(User.id == user_id, User.is_deleted.is_(False))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException("User")
        
        return user

    @staticmethod
    async def email_exists(db: AsyncSession, email: str) -> bool:
        result = await db.execute(
            select(User).where(
                User.email == email,
                User.is_deleted.is_(False),
            )
        )

        return result.scalar_one_or_none() is not None