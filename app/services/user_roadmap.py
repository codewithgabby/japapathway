# app/services/user_roadmap.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone
from app.models.pathway import (
    UserRoadmap,
    UserRoadmapStep,
    StepStatus,
    PathwayStatus,
    UserRoadmapStatus,
)
from app.services.pathway import PathwayService
from app.core.exceptions import NotFoundException, BadRequestException

class UserRoadmapService:
    
    @staticmethod
    async def start_roadmap(
        db: AsyncSession, user_id: str, pathway_id: str
    ) -> UserRoadmap:
        # Validate pathway exists and is published
        pathway = await PathwayService.get_pathway_by_id(db, pathway_id)
        if pathway.status != PathwayStatus.PUBLISHED:
            raise BadRequestException("Pathway is not available")
        
        # Check if user already has an active roadmap
        result = await db.execute(
            select(UserRoadmap).where(
                UserRoadmap.user_id == user_id,
                UserRoadmap.status == UserRoadmapStatus.ACTIVE,
                UserRoadmap.is_deleted.is_(False)
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise BadRequestException("You already have an active roadmap")
        
        # Get all active steps
        steps = await PathwayService.get_pathway_steps(db, pathway_id)
        active_steps = [s for s in steps if s.is_active]
        
        if not active_steps:
            raise BadRequestException("Pathway has no steps")
        
        # Create user roadmap
        user_roadmap = UserRoadmap(
            user_id=user_id,
            pathway_id=pathway_id,
        )
        db.add(user_roadmap)
        await db.flush()
        
        # Create user steps
        for step in active_steps:
            user_step = UserRoadmapStep(
                user_roadmap_id=user_roadmap.id,
                roadmap_step_id=step.id,
                status=StepStatus.PENDING
            )
            db.add(user_step)
        
        await db.flush()
        await db.commit()
        return user_roadmap
    
    @staticmethod
    async def get_user_roadmap(db: AsyncSession, user_id: str) -> UserRoadmap:
        result = await db.execute(
            select(UserRoadmap).where(
                UserRoadmap.user_id == user_id,
                UserRoadmap.status == UserRoadmapStatus.ACTIVE,
                UserRoadmap.is_deleted.is_(False)
            )
        )
        roadmap = result.scalar_one_or_none()
        if not roadmap:
            raise NotFoundException("Active roadmap")
        return roadmap
    
    @staticmethod
    async def get_roadmap_by_id(db: AsyncSession, roadmap_id: str) -> UserRoadmap:
        result = await db.execute(
            select(UserRoadmap).where(
                UserRoadmap.id == roadmap_id,
                UserRoadmap.is_deleted.is_(False)
            )
        )
        roadmap = result.scalar_one_or_none()
        if not roadmap:
            raise NotFoundException("Roadmap")
        return roadmap
    
    @staticmethod
    async def get_roadmap_steps(db: AsyncSession, roadmap_id: str) -> List[UserRoadmapStep]:
        result = await db.execute(
            select(UserRoadmapStep).where(
                UserRoadmapStep.user_roadmap_id == roadmap_id,
                UserRoadmapStep.is_deleted.is_(False)
            ).order_by(UserRoadmapStep.created_at)
        )
        user_steps = result.scalars().all()
        
        # Enrich with step details
        for user_step in user_steps:
            step = await PathwayService.get_step(db, user_step.roadmap_step_id)
            user_step.step_title = step.title
            user_step.step_slug = step.slug
            user_step.step_order = step.step_order
            user_step.description = step.description
            user_step.estimated_duration_days = step.estimated_duration_days
        
        # Sort by step order
        user_steps.sort(key=lambda x: x.step_order)
        return user_steps
    
    @staticmethod
    async def update_step_status(
        db: AsyncSession, roadmap_id: str, step_id: str, status: str, notes: Optional[str] = None
    ) -> UserRoadmapStep:
        result = await db.execute(
            select(UserRoadmapStep).where(
                UserRoadmapStep.user_roadmap_id == roadmap_id,
                UserRoadmapStep.roadmap_step_id == step_id,
                UserRoadmapStep.is_deleted.is_(False)
            )
        )
        user_step = result.scalar_one_or_none()
        if not user_step:
            raise NotFoundException("Roadmap step")
        
        try:
            user_step.status = StepStatus(status)
        except ValueError:
            raise BadRequestException(
                f"Invalid roadmap step status: {status}"
            )
        if notes:
            user_step.notes = notes
        
        

        if user_step.status == StepStatus.COMPLETED:
            user_step.completed_at = datetime.now(timezone.utc)
        else:
            user_step.completed_at = None
        
        await db.flush()
        
        # Update roadmap progress
        await UserRoadmapService._update_progress(db, roadmap_id)

        await db.commit()
        
        return user_step
    
    @staticmethod
    async def _update_progress(db: AsyncSession, roadmap_id: str) -> None:
        roadmap = await UserRoadmapService.get_roadmap_by_id(db, roadmap_id)
        
        result = await db.execute(
            select(UserRoadmapStep).where(
                UserRoadmapStep.user_roadmap_id == roadmap_id,
                UserRoadmapStep.is_deleted.is_(False)
            )
        )
        steps = result.scalars().all()
        
        total = len(steps)
        completed = len([s for s in steps if s.status == StepStatus.COMPLETED])
        
        if completed == total and total > 0:
            roadmap.status = UserRoadmapStatus.COMPLETED
        
        await db.flush()
    
    @staticmethod
    async def restart_roadmap(
        db: AsyncSession,
        user_id: str,
    ) -> UserRoadmap:
        current = await UserRoadmapService.get_user_roadmap(
            db,
            user_id,
        )

        # Get the pathway's current active steps first
        steps = await PathwayService.get_pathway_steps(
            db,
            str(current.pathway_id),
        )

        active_steps = [
            step for step in steps
            if step.is_active
        ]

        if not active_steps:
            raise BadRequestException(
                "Pathway has no active steps"
            )

        # Archive the current roadmap only after validation succeeds
        current.status = UserRoadmapStatus.ARCHIVED

        # Create a fresh roadmap using the same pathway
        new_roadmap = UserRoadmap(
            user_id=user_id,
            pathway_id=current.pathway_id,
            status=UserRoadmapStatus.ACTIVE,
        )

        db.add(new_roadmap)
        await db.flush()

        # Create fresh user roadmap steps
        for step in active_steps:
            user_step = UserRoadmapStep(
                user_roadmap_id=new_roadmap.id,
                roadmap_step_id=step.id,
                status=StepStatus.PENDING,
            )
            db.add(user_step)

        await db.flush()

        return new_roadmap
    
    @staticmethod
    async def get_roadmap_summary(db: AsyncSession, user_id: str) -> dict:
        try:
            roadmap = await UserRoadmapService.get_user_roadmap(db, user_id)
            pathway = await PathwayService.get_pathway_by_id(db, roadmap.pathway_id)
            
            # Get next pending step
            steps = await UserRoadmapService.get_roadmap_steps(db, roadmap.id)
            next_step = None
            for step in steps:
                if step.status != StepStatus.COMPLETED:
                    next_step = {
                        "id": str(step.roadmap_step_id),
                        "title": step.step_title,
                        "order": step.step_order
                    }
                    break
            
            completed_steps = sum(
                1 for step in steps
                if step.status == StepStatus.COMPLETED
            )

            total_steps = len(steps)

            progress_percentage = (
                int((completed_steps / total_steps) * 100)
                if total_steps > 0
                else 0
            )

            return {
                "id": str(roadmap.id),
                "pathway_id": str(roadmap.pathway_id),
                "pathway_name": pathway.name,
                "pathway_slug": pathway.slug,
                "status": roadmap.status,
                "completed_steps": completed_steps,
                "total_steps": total_steps,
                "progress_percentage": progress_percentage,
                "next_step": next_step,
            }
        except NotFoundException:
            return {
                "id": None,
                "pathway_id": None,
                "pathway_name": None,
                "pathway_slug": None,
                "status": "no_roadmap",
                "completed_steps": 0,
                "total_steps": 0,
                "progress_percentage": 0,
                "next_step": None
            }