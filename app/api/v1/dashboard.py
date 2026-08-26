# app/api/v1/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.dashboard import DashboardService
from app.schemas.dashboard import (
    DashboardResponse,
    DashboardUserResponse,
    DashboardJourneyResponse,
    DashboardJourneyNextStep,
    DashboardReadinessResponse,
    DashboardSOPDocumentResponse,
    DashboardDraftInfo,
    DashboardNextActionResponse,
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the authenticated user's immigration journey dashboard.
    Aggregates roadmap, readiness, SOP/LOE, and AI generation state.
    """
    data = await DashboardService.get_dashboard(db, current_user)

    # Build Pydantic response
    return DashboardResponse(
        user=DashboardUserResponse(**data["user"]),
        journey=DashboardJourneyResponse(
            has_roadmap=data["journey"]["has_roadmap"],
            pathway_name=data["journey"]["pathway_name"],
            pathway_slug=data["journey"]["pathway_slug"],
            status=data["journey"]["status"],
            completed_steps=data["journey"]["completed_steps"],
            total_steps=data["journey"]["total_steps"],
            completion_percentage=data["journey"]["completion_percentage"],
            next_step=DashboardJourneyNextStep(**data["journey"]["next_step"]) if data["journey"]["next_step"] else None,
        ),
        readiness=DashboardReadinessResponse(
            has_checklist=data["readiness"]["has_checklist"],
            pathway_name=data["readiness"]["pathway_name"],
            completion_percentage=data["readiness"]["completion_percentage"],
            total_required=data["readiness"]["total_required"],
            completed_required=data["readiness"]["completed_required"],
            missing_required=data["readiness"]["missing_required"],
            missing_documents=data["readiness"]["missing_documents"],
        ),
        sop_documents=[
            DashboardSOPDocumentResponse(
                document_id=doc["document_id"],
                document_type=doc["document_type"],
                title=doc["title"],
                status=doc["status"],
                progress_percentage=doc["progress_percentage"],
                answered_questions=doc["answered_questions"],
                total_questions=doc["total_questions"],
                latest_draft=DashboardDraftInfo(**doc["latest_draft"]) if doc["latest_draft"] else None,
            )
            for doc in data["sop_documents"]
        ],
        next_action=DashboardNextActionResponse(
            type=data["next_action"]["type"],
            title=data["next_action"]["title"],
            description=data["next_action"]["description"],
            priority=data["next_action"]["priority"],
        ),
    )