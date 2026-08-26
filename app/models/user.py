# app/models/user.py
from sqlalchemy import Boolean, Column, Enum, String
from app.constants.roles import UserRole
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    __table_args__ = (
            {"comment": "Application users"},
        )

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    full_name = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        Enum(
            UserRole,
            values_callable=lambda enum_class: [member.value for member in enum_class],
            name="userrole",
        ),
        default=UserRole.APPLICANT,
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    email_verified = Column(
            Boolean,
            default=False,
            nullable=False,
    )

    