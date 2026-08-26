# app/models/audit.py
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base
from app.models.base import TimestampMixin

import uuid

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(50), nullable=False)  # create, update, delete, publish, archive
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    changes = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Audit logs are immutable and do not use soft delete