# app/api/v1/documents.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.document import DocumentService
from app.services.user_roadmap import UserRoadmapService
from app.schemas.document import (
    UserDocumentChecklistItemResponse,
    UserDocumentStatusUpdate,
    UserDocumentReadinessSummaryResponse
)

router = APIRouter()



async def _resolve_pathway_id(
    db: AsyncSession,
    user_id: str,
    pathway_id: Optional[str] = None,
) -> str:
    """Resolve a pathway belonging to one of the user's active journeys."""
    roadmaps = await UserRoadmapService.get_active_roadmaps(
        db,
        user_id,
    )

    if pathway_id:
        for roadmap in roadmaps:
            if str(roadmap.pathway_id) == str(pathway_id):
                return str(roadmap.pathway_id)

        raise HTTPException(
            status_code=404,
            detail="No active journey found for this pathway.",
        )

    if not roadmaps:
        raise HTTPException(
            status_code=404,
            detail="No active immigration journey found.",
        )

    if len(roadmaps) > 1:
        raise HTTPException(
            status_code=400,
            detail="Multiple active journeys exist. Please specify pathway_id.",
        )

    return str(roadmaps[0].pathway_id)




@router.get(
    "/readiness/checklist",
    response_model=List[UserDocumentChecklistItemResponse],
)
async def get_document_checklist(
    pathway_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the checklist for a selected active pathway."""
    resolved_pathway_id = await _resolve_pathway_id(
        db,
        str(current_user.id),
        pathway_id,
    )

    return await DocumentService.get_checklist_with_details(
        db,
        str(current_user.id),
        resolved_pathway_id,
    )


@router.get(
    "/readiness/checklist/{pathway_id}",
    response_model=List[UserDocumentChecklistItemResponse],
)
async def get_document_checklist_for_pathway(
    pathway_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the checklist for one of the applicant's active pathways."""
    resolved_pathway_id = await _resolve_pathway_id(
        db,
        str(current_user.id),
        pathway_id,
    )

    items = await DocumentService.get_checklist_with_details(
        db,
        str(current_user.id),
        resolved_pathway_id,
    )

    return items


@router.put(
    "/readiness/checklist/{requirement_id}",
    response_model=UserDocumentChecklistItemResponse,
)
async def update_document_status(
    requirement_id: str,
    data: UserDocumentStatusUpdate,
    pathway_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a checklist item for a selected active pathway."""
    resolved_pathway_id = await _resolve_pathway_id(
        db,
        str(current_user.id),
        pathway_id,
    )

    return await DocumentService.update_checklist_item(
        db,
        str(current_user.id),
        resolved_pathway_id,
        requirement_id,
        data.status,
        data.notes,
    )


@router.get(
    "/readiness/summary",
    response_model=UserDocumentReadinessSummaryResponse,
)
async def get_readiness_summary(
    pathway_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get readiness information for a selected active pathway."""
    resolved_pathway_id = await _resolve_pathway_id(
        db,
        str(current_user.id),
        pathway_id,
    )

    return await DocumentService.get_readiness_summary(
        db,
        str(current_user.id),
        resolved_pathway_id,
    )





@router.get(
    "/readiness/summary/{pathway_id}",
    response_model=UserDocumentReadinessSummaryResponse,
)
async def get_readiness_summary_for_pathway(
    pathway_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get readiness summary for one of the applicant's active pathways."""
    resolved_pathway_id = await _resolve_pathway_id(
        db,
        str(current_user.id),
        pathway_id,
    )

    return await DocumentService.get_readiness_summary(
        db,
        str(current_user.id),
        resolved_pathway_id,
    )




@router.get("/readiness/missing", response_model=List[str])
async def get_missing_documents(
    pathway_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get missing required documents for a selected active pathway."""
    resolved_pathway_id = await _resolve_pathway_id(
        db,
        str(current_user.id),
        pathway_id,
    )

    summary = await DocumentService.get_readiness_summary(
        db,
        str(current_user.id),
        resolved_pathway_id,
    )

    return summary["missing_documents"]
