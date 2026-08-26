from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.pathway import PathwayStatus
from app.services.pathway import PathwayService
from app.services.audit import AuditService
from app.schemas.pathway import (
    PathwayCreate,
    PathwayUpdate,
    PathwayResponse,
    PathwayDetailResponse,
    RoadmapStepCreate,
    RoadmapStepUpdate,
    RoadmapStepResponse,
    StepsReorderRequest,
)

router = APIRouter()


# ============================================================
# Pathway CRUD
# ============================================================


@router.get("/pathways", response_model=List[PathwayResponse])
async def list_pathways(
    country: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """List all pathways with optional filters."""

    pathways = await PathwayService.get_all_pathways(
        db,
        country=country,
        category=category,
        status=status,
        include_inactive=include_inactive,
    )

    result = []

    for pathway in pathways:
        steps = await PathwayService.get_pathway_steps(
            db,
            str(pathway.id),
        )

        pathway.steps_count = len(steps)
        result.append(pathway)

    return result


@router.get(
    "/pathways/{pathway_id}",
    response_model=PathwayDetailResponse,
)
async def get_pathway(
    pathway_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Get pathway with all steps."""

    pathway = await PathwayService.get_pathway_by_id(
        db,
        pathway_id,
    )

    steps = await PathwayService.get_pathway_steps(
        db,
        pathway_id,
    )

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
        steps=[
            RoadmapStepResponse(
                id=str(step.id),
                pathway_id=str(step.pathway_id),
                title=step.title,
                slug=step.slug,
                description=step.description,
                step_order=step.step_order,
                estimated_duration_days=step.estimated_duration_days,
                is_required=step.is_required,
                is_active=step.is_active,
                created_at=step.created_at,
            )
            for step in steps
        ],
    )


@router.post(
    "/pathways",
    response_model=PathwayDetailResponse,
    status_code=201,
)
async def create_pathway(
    data: PathwayCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Create a new pathway with optional steps."""

    pathway = await PathwayService.create_pathway(
        db,
        data.model_dump(),
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "create",
        "pathway",
        str(pathway.id),
        {
            "name": pathway.name,
            "slug": pathway.slug,
        },
    )

    await db.commit()

    steps = await PathwayService.get_pathway_steps(
        db,
        str(pathway.id),
    )

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
        steps=[
            RoadmapStepResponse(
                id=str(step.id),
                pathway_id=str(step.pathway_id),
                title=step.title,
                slug=step.slug,
                description=step.description,
                step_order=step.step_order,
                estimated_duration_days=step.estimated_duration_days,
                is_required=step.is_required,
                is_active=step.is_active,
                created_at=step.created_at,
            )
            for step in steps
        ],
    )


@router.put(
    "/pathways/{pathway_id}",
    response_model=PathwayResponse,
)
async def update_pathway(
    pathway_id: str,
    data: PathwayUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update pathway details."""

    old_pathway = await PathwayService.get_pathway_by_id(
        db,
        pathway_id,
    )

    old_name = old_pathway.name

    pathway = await PathwayService.update_pathway(
        db,
        pathway_id,
        data.model_dump(exclude_none=True),
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "update",
        "pathway",
        str(pathway.id),
        {
            "old": old_name,
            "new": pathway.name,
        },
    )

    await db.commit()

    return pathway


@router.delete(
    "/pathways/{pathway_id}",
    status_code=204,
)
async def delete_pathway(
    pathway_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Soft delete pathway."""

    pathway = await PathwayService.get_pathway_by_id(
        db,
        pathway_id,
    )

    pathway_name = pathway.name

    await PathwayService.delete_pathway(
        db,
        pathway_id,
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "delete",
        "pathway",
        str(pathway_id),
        {
            "name": pathway_name,
        },
    )

    await db.commit()


@router.put(
    "/pathways/{pathway_id}/status",
)
async def change_pathway_status(
    pathway_id: str,
    status: PathwayStatus,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Change pathway status."""

    pathway = await PathwayService.change_pathway_status(
        db,
        pathway_id,
        status.value,
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "update",
        "pathway",
        str(pathway_id),
        {
            "name": pathway.name,
            "status": status.value,
        },
    )

    await db.commit()

    return {
        "id": str(pathway.id),
        "status": pathway.status.value,
    }


# ============================================================
# Step CRUD
# ============================================================


@router.post(
    "/pathways/{pathway_id}/steps",
    response_model=RoadmapStepResponse,
    status_code=201,
)
async def add_step(
    pathway_id: str,
    data: RoadmapStepCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Add a step to a pathway."""

    step = await PathwayService.add_step(
        db,
        pathway_id,
        data.model_dump(),
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "create",
        "roadmap_step",
        str(step.id),
        {
            "title": step.title,
            "pathway_id": pathway_id,
        },
    )

    await db.commit()

    return step


# ============================================================
# IMPORTANT:
# This route MUST come BEFORE /steps/{step_id}
# because "reorder" is a fixed path segment, not a UUID.
# ============================================================


@router.put(
    "/pathways/{pathway_id}/steps/reorder",
    response_model=List[RoadmapStepResponse],
)
async def reorder_steps(
    pathway_id: str,
    data: StepsReorderRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Reorder pathway steps."""

    steps = await PathwayService.reorder_steps(
        db,
        pathway_id,
        [
            {
                "step_id": step.step_id,
                "new_order": step.new_order,
            }
            for step in data.steps
        ],
        str(admin.id),
    )

    await db.commit()

    return steps


@router.put(
    "/pathways/{pathway_id}/steps/{step_id}",
    response_model=RoadmapStepResponse,
)
async def update_step(
    pathway_id: str,
    step_id: str,
    data: RoadmapStepUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update a pathway step."""

    pathway = await PathwayService.get_pathway_by_id(
        db,
        pathway_id,
    )

    step = await PathwayService.get_step(
        db,
        step_id,
    )

    if step.pathway_id != pathway.id:
        raise HTTPException(
            status_code=404,
            detail="Step not found in this pathway",
        )

    step = await PathwayService.update_step(
        db,
        step_id,
        data.model_dump(exclude_none=True),
        str(admin.id),
    )

    await db.commit()

    return step


@router.delete(
    "/pathways/{pathway_id}/steps/{step_id}",
    status_code=204,
)
async def delete_step(
    pathway_id: str,
    step_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Soft delete a pathway step."""

    pathway = await PathwayService.get_pathway_by_id(
        db,
        pathway_id,
    )

    step = await PathwayService.get_step(
        db,
        step_id,
    )

    if step.pathway_id != pathway.id:
        raise HTTPException(
            status_code=404,
            detail="Step not found in this pathway",
        )

    await PathwayService.delete_step(
        db,
        step_id,
        str(admin.id),
    )

    await db.commit()