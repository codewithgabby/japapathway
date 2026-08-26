# app/api/v1/documents.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
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


@router.get("/readiness/checklist", response_model=List[UserDocumentChecklistItemResponse])
async def get_document_checklist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's document checklist for their active pathway.
    Creates checklist automatically if not exists.
    """
    # Get user's active roadmap to find pathway
    roadmap = await UserRoadmapService.get_user_roadmap(db, str(current_user.id))
    
    items = await DocumentService.get_checklist_with_details(
        db, str(current_user.id), str(roadmap.pathway_id)
    )
    
    return items


@router.get("/readiness/checklist/{pathway_id}", response_model=List[UserDocumentChecklistItemResponse])
async def get_document_checklist_for_pathway(
    pathway_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get document checklist for a specific pathway.
    """

    items = await DocumentService.get_checklist_with_details(
        db, str(current_user.id), pathway_id
    )

    return items


@router.put("/readiness/checklist/{requirement_id}", response_model=UserDocumentChecklistItemResponse)
async def update_document_status(
    requirement_id: str,
    data: UserDocumentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update status of a document checklist item (ready or not_ready).
    """
    # Get user's active roadmap to find pathway
    roadmap = await UserRoadmapService.get_user_roadmap(db, str(current_user.id))
    
    item = await DocumentService.update_checklist_item(
        db,
        str(current_user.id),
        str(roadmap.pathway_id),
        requirement_id,
        data.status,
        data.notes
    )
    
    return item


@router.get("/readiness/summary", response_model=UserDocumentReadinessSummaryResponse)
async def get_readiness_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get document readiness summary for current user's active pathway.
    Includes completion percentage, missing documents, and recommendations.
    """
    roadmap = await UserRoadmapService.get_user_roadmap(db, str(current_user.id))
    
    summary = await DocumentService.get_readiness_summary(
        db, str(current_user.id), str(roadmap.pathway_id)
    )
    
    return summary


@router.get("/readiness/summary/{pathway_id}", response_model=UserDocumentReadinessSummaryResponse)
async def get_readiness_summary_for_pathway(
    pathway_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get document readiness summary for a specific pathway.
    """
    summary = await DocumentService.get_readiness_summary(
        db, str(current_user.id), pathway_id
    )
    
    return summary


@router.get("/readiness/missing", response_model=List[str])
async def get_missing_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of missing required documents for current user's active pathway.
    """
    roadmap = await UserRoadmapService.get_user_roadmap(db, str(current_user.id))
    
    summary = await DocumentService.get_readiness_summary(
        db, str(current_user.id), str(roadmap.pathway_id)
    )
    
    return summary["missing_documents"]