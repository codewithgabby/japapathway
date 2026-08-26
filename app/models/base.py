from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    deleted_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    __abstract__ = True

    __mapper_args__ = {
        "eager_defaults": True,
    }

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    def soft_delete(self, deleted_by_id=None):
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by_id