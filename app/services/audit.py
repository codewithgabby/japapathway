# app/services/audit.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List, Dict, Any
from app.models.audit import AuditLog

class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: Optional[str],
        action: str,
        entity_type: str,
        entity_id: str,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes or {},
            ip_address=ip_address
        )
        db.add(audit_log)
        await db.flush()
        return audit_log
    
    @staticmethod
    async def get_logs(
        db: AsyncSession,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AuditLog]:
        query = select(AuditLog)
        
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        
        query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()