# app/api/v1/pathways.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.pathway import StepStatus
from app.models.user import User
from app.services.pathway import PathwayService
from app.services.user_roadmap import UserRoadmapService
from app.schemas.pathway import (
    PathwayResponse,
    PathwayDetailResponse,
    UserRoadmapStartRequest,
    UserRoadmapStepUpdate,
    UserRoadmapResponse,
    UserRoadmapStepResponse,
    UserRoadmapSummaryResponse,
    RoadmapStepResponse,
)

router = APIRouter()

# ========== Public Pathway Endpoints ==========

@router.get("/pathways", response_model=List[PathwayResponse])
async def list_available_pathways(
    country: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all published pathways available to applicants"""
    pathways = await PathwayService.get_all_pathways(
        db, country=country, category=category, 
        status="published", include_inactive=False
    )
    
    result = []
    for p in pathways:
        steps = await PathwayService.get_pathway_steps(db, str(p.id))
        p.steps_count = len(steps)
        result.append(p)
    
    return result

@router.get("/pathways/{pathway_slug}", response_model=PathwayDetailResponse)
async def get_pathway_details(
    pathway_slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get pathway details with all steps"""
    pathway = await PathwayService.get_pathway_by_slug(db, pathway_slug)
    steps = await PathwayService.get_pathway_steps(db, str(pathway.id))
    
    return PathwayDetailResponse(
        id=str(pathway.id),
        name=pathway.name,
        slug=pathway.slug,
        description=pathway.description,
        country=pathway.country,
        icon=pathway.icon,
        color=pathway.color,
        category=pathway.category,
        status=pathway.status,
        version=pathway.version,
        sort_order=pathway.sort_order,
        is_active=pathway.is_active,
        steps_count=len(steps),
        created_at=pathway.created_at,
        updated_at=pathway.updated_at,
        steps=[RoadmapStepResponse(
            id=str(s.id),
            pathway_id=str(s.pathway_id),
            title=s.title,
            slug=s.slug,
            description=s.description,
            step_order=s.step_order,
            estimated_duration_days=s.estimated_duration_days,
            is_required=s.is_required,
            is_active=s.is_active,
            created_at=s.created_at
        ) for s in steps]
    )

# ========== User Roadmap Endpoints ==========

@router.get("/my-roadmap", response_model=UserRoadmapResponse)
async def get_my_roadmap(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's active roadmap"""
    roadmap = await UserRoadmapService.get_user_roadmap(db, str(current_user.id))
    pathway = await PathwayService.get_pathway_by_id(db, str(roadmap.pathway_id))
    steps = await UserRoadmapService.get_roadmap_steps(db, str(roadmap.id))

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
    
    return UserRoadmapResponse(
        id=str(roadmap.id),
        pathway_id=str(roadmap.pathway_id),
        pathway_name=pathway.name,
        pathway_slug=pathway.slug,
        status=roadmap.status,
        progress_percentage=progress_percentage,
        steps=[UserRoadmapStepResponse(
            id=str(s.id),
            roadmap_step_id=str(s.roadmap_step_id),
            step_title=s.step_title,
            step_slug=s.step_slug,
            step_order=s.step_order,
            description=s.description,
            estimated_duration_days=s.estimated_duration_days,
            status=s.status,
            completed_at=s.completed_at,
            notes=s.notes
        ) for s in steps]
    )

@router.get("/my-roadmap/summary", response_model=UserRoadmapSummaryResponse)
async def get_roadmap_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get roadmap summary for dashboard"""
    summary = await UserRoadmapService.get_roadmap_summary(db, str(current_user.id))
    return summary

@router.post("/my-roadmap/start", response_model=UserRoadmapResponse, status_code=201)
async def start_roadmap(
    data: UserRoadmapStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new immigration roadmap"""
    roadmap = await UserRoadmapService.start_roadmap(
        db, str(current_user.id), data.pathway_id
    )
    pathway = await PathwayService.get_pathway_by_id(db, str(roadmap.pathway_id))
    steps = await UserRoadmapService.get_roadmap_steps(db, str(roadmap.id))

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
    
    return UserRoadmapResponse(
        id=str(roadmap.id),
        pathway_id=str(roadmap.pathway_id),
        pathway_name=pathway.name,
        pathway_slug=pathway.slug,
        status=roadmap.status,
        progress_percentage=progress_percentage,
        steps=[UserRoadmapStepResponse(
            id=str(s.id),
            roadmap_step_id=str(s.roadmap_step_id),
            step_title=s.step_title,
            step_slug=s.step_slug,
            step_order=s.step_order,
            description=s.description,
            estimated_duration_days=s.estimated_duration_days,
            status=s.status,
            completed_at=s.completed_at,
            notes=s.notes
        ) for s in steps]
    )

@router.put("/my-roadmap/steps/{step_id}", response_model=UserRoadmapStepResponse)
async def update_step_status(
    step_id: str,
    data: UserRoadmapStepUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update roadmap step status"""
    roadmap = await UserRoadmapService.get_user_roadmap(db, str(current_user.id))
    step = await UserRoadmapService.update_step_status(
        db, str(roadmap.id), step_id, data.status.value, data.notes
    )
    
    step_data_list = await UserRoadmapService.get_roadmap_steps(
        db, str(roadmap.id)
    ) 

    step_data = next(
        (item for item in step_data_list if item.id == step.id),
        None,
    )

    if step_data is None:
        raise HTTPException(
            status_code=404,
            detail="Roadmap step not found",
        )

    return UserRoadmapStepResponse(
    id=str(step.id),
    roadmap_step_id=str(step.roadmap_step_id),
    step_title=step_data.step_title,
    step_slug=step_data.step_slug,
    step_order=step_data.step_order,
    description=step_data.description,
    estimated_duration_days=step_data.estimated_duration_days,
    status=step.status,
    completed_at=step.completed_at,
    notes=step.notes,
)

@router.post("/my-roadmap/restart", response_model=UserRoadmapResponse)
async def restart_roadmap(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restart current roadmap"""
    roadmap = await UserRoadmapService.restart_roadmap(db, str(current_user.id))
    pathway = await PathwayService.get_pathway_by_id(db, str(roadmap.pathway_id))
    steps = await UserRoadmapService.get_roadmap_steps(db, str(roadmap.id))

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
    
    return UserRoadmapResponse(
        id=str(roadmap.id),
        pathway_id=str(roadmap.pathway_id),
        pathway_name=pathway.name,
        pathway_slug=pathway.slug,
        status=roadmap.status,
        progress_percentage=progress_percentage,
        steps=[UserRoadmapStepResponse(
            id=str(s.id),
            roadmap_step_id=str(s.roadmap_step_id),
            step_title=s.step_title,
            step_slug=s.step_slug,
            step_order=s.step_order,
            description=s.description,
            estimated_duration_days=s.estimated_duration_days,
            status=s.status,
            completed_at=s.completed_at,
            notes=s.notes
        ) for s in steps]
    )