# app/services/dashboard.py
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.user_roadmap import UserRoadmapService
from app.services.document import DocumentService
from app.services.sop import SOPService
from app.core.exceptions import NotFoundException, BadRequestException


class DashboardService:
    """
    Aggregation/read-model layer for the applicant dashboard.
    Collects state from existing domain services. No business logic duplication.
    """

    @staticmethod
    async def get_dashboard(
        db: AsyncSession,
        user: User,
    ) -> Dict[str, Any]:
        """
        Build the full dashboard response for the authenticated user.
        """
        user_id = str(user.id)

        # Gather all sections in parallel (conceptually)
        user_section = DashboardService._build_user_section(user)
        journey_section = await DashboardService._build_journey_section(db, user_id)
        readiness_section = await DashboardService._build_readiness_section(db, user_id)
        sop_section = await DashboardService._build_sop_section(db, user_id)

        # Determine next action from existing state
        next_action = DashboardService._determine_next_action(
            journey_section,
            readiness_section,
            sop_section,
        )

        return {
            "user": user_section,
            "journey": journey_section,
            "readiness": readiness_section,
            "sop_documents": sop_section,
            "next_action": next_action,
        }

    # ========== Section Builders ==========

    @staticmethod
    def _build_user_section(user: User) -> Dict[str, Any]:
        return {
            "full_name": user.full_name,
            "email": user.email,
            "user_id": str(user.id),
        }

    @staticmethod
    async def _build_journey_section(
        db: AsyncSession,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Return all active journeys while preserving the legacy single-journey
        fields for backward compatibility.
        """
        summaries = await UserRoadmapService.get_all_roadmap_summaries(
            db,
            user_id,
        )

        journeys = [
            {
                "id": summary.get("id"),
                "pathway_id": summary.get("pathway_id"),
                "has_roadmap": True,
                "pathway_name": summary.get("pathway_name"),
                "pathway_slug": summary.get("pathway_slug"),
                "status": summary.get("status"),
                "completed_steps": summary.get("completed_steps", 0),
                "total_steps": summary.get("total_steps", 0),
                "completion_percentage": summary.get(
                    "progress_percentage", 0
                ),
                "next_step": summary.get("next_step"),
            }
            for summary in summaries
        ]

        # Preserve the existing single-journey response fields temporarily.
        if journeys:
            primary_journey = journeys[0]
            return {
                **primary_journey,
                "journeys": journeys,
                "journey_count": len(journeys),
            }

        return {
            "id": None,
            "pathway_id": None,
            "has_roadmap": False,
            "pathway_name": None,
            "pathway_slug": None,
            "status": None,
            "completed_steps": 0,
            "total_steps": 0,
            "completion_percentage": 0,
            "next_step": None,
            "journeys": [],
            "journey_count": 0,
        }

    @staticmethod
    async def _build_readiness_section(
        db: AsyncSession,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Build an independent document-readiness summary for each active
        immigration journey.
        """
        summaries = await UserRoadmapService.get_all_roadmap_summaries(
            db,
            user_id,
        )

        readiness_by_pathway = []

        for summary in summaries:
            pathway_id = summary.get("pathway_id")

            if not pathway_id:
                continue

            try:
                readiness = await DocumentService.get_readiness_summary(
                    db,
                    user_id,
                    pathway_id,
                )

                readiness_by_pathway.append({
                    "has_checklist": True,
                    "pathway_id": readiness.get("pathway_id"),
                    "pathway_name": readiness.get("pathway_name"),
                    "pathway_slug": readiness.get("pathway_slug"),
                    "completion_percentage": readiness.get(
                        "completion_percentage", 0
                    ),
                    "total_required": readiness.get("total_required", 0),
                    "completed_required": readiness.get(
                        "completed_required", 0
                    ),
                    "missing_required": readiness.get("missing_required", 0),
                    "missing_documents": readiness.get(
                        "missing_documents", []
                    ),
                })

            except (NotFoundException, BadRequestException):
                continue

        # Preserve the legacy single-checklist fields temporarily.
        if readiness_by_pathway:
            primary = readiness_by_pathway[0]

            return {
                **primary,
                "readiness_by_pathway": readiness_by_pathway,
            }

        return {
            "has_checklist": False,
            "pathway_id": None,
            "pathway_name": None,
            "pathway_slug": None,
            "completion_percentage": 0,
            "total_required": 0,
            "completed_required": 0,
            "missing_required": 0,
            "missing_documents": [],
            "readiness_by_pathway": [],
        }

    @staticmethod
    async def _build_sop_section(db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
        """
        Get user's SOP/LOE documents with progress and draft state.
        Gracefully handles no documents.
        """
        try:
            documents = await SOPService.get_user_documents(db, user_id)

            result = []
            for doc in documents:
                doc_id = str(doc.id)

                # Get progress
                try:
                    progress = await SOPService.get_document_progress(db, doc_id, user_id)
                    progress_percentage = progress.get("progress_percentage", 0)
                    answered_questions = progress.get("answered_questions", 0)
                    total_questions = progress.get("total_questions", 0)
                except Exception:
                    progress_percentage = 0
                    answered_questions = 0
                    total_questions = 0

                # Get latest current draft
                latest_draft = None
                try:
                    drafts = await SOPService.get_current_drafts(db, doc_id, user_id)
                    if drafts:
                        latest = max(
                            drafts,
                            key=lambda draft: draft.version or 0,
                        )  
                        latest_draft = {
                            "draft_id": str(latest.id),
                            "version": latest.version,
                            "generation_status": latest.generation_status.value if latest.generation_status else None,
                            "warnings_count": len(latest.warnings) if latest.warnings else 0,
                            "missing_information_count": len(latest.missing_information) if latest.missing_information else 0,
                        }
                except Exception:
                    latest_draft = None

                result.append({
                    "document_id": doc_id,
                    "document_type": doc.document_type.value,
                    "title": doc.title,
                    "status": doc.status.value,
                    "progress_percentage": progress_percentage,
                    "answered_questions": answered_questions,
                    "total_questions": total_questions,
                    "latest_draft": latest_draft,
                })

            return result
        except NotFoundException:
            return []

    # ========== Next Action Logic ==========


    @staticmethod
    def _determine_next_action(
        journey_section: Dict[str, Any],
        readiness_section: Dict[str, Any],
        sop_documents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Determine the next action from existing application state.

        Priority:
        needs_clarification > continue_sop > review_draft >
        complete_readiness > continue_roadmap > start_roadmap > no_action
        """

        # 1. Resolve missing information in any SOP/LOE draft.
        for doc in sop_documents:
            latest_draft = doc.get("latest_draft")

            if latest_draft and (
                latest_draft.get("generation_status") == "needs_clarification"
                or latest_draft.get("missing_information_count", 0) > 0
            ):
                return {
                    "type": "needs_clarification",
                    "title": "Resolve missing information",
                    "description": (
                        f"Your {doc.get('document_type', 'document').upper()} "
                        "has missing information that needs your attention."
                    ),
                    "priority": "high",
                }

        # 2. Continue questionnaires with unanswered questions.
        for doc in sop_documents:
            answered = doc.get("answered_questions", 0)
            total = doc.get("total_questions", 0)

            if answered < total:
                remaining = total - answered
                document_type = doc.get("document_type", "SOP").upper()

                return {
                    "type": "continue_sop",
                    "title": f"Continue your {document_type}",
                    "description": (
                        f"You have {remaining} unanswered question(s) "
                        f"in your {document_type}."
                    ),
                    "priority": "high",
                }

        # 3. Review a generated draft that has not been finalized.
        for doc in sop_documents:
            if doc.get("status") == "generated" and doc.get("latest_draft"):
                return {
                    "type": "review_draft",
                    "title": "Review your generated draft",
                    "description": (
                        f"Your {doc.get('document_type', 'SOP').upper()} "
                        "draft is ready for review."
                    ),
                    "priority": "normal",
                }

        # 4. Check readiness across every active pathway.
        readiness_items = readiness_section.get("readiness_by_pathway", [])

        incomplete_readiness = next(
            (
                item
                for item in readiness_items
                if item.get("has_checklist")
                and item.get("missing_required", 0) > 0
            ),
            None,
        )

        # Backward-compatible fallback for the legacy single-checklist shape.
        if incomplete_readiness is None and not readiness_items:
            if (
                readiness_section.get("has_checklist")
                and readiness_section.get("missing_required", 0) > 0
            ):
                incomplete_readiness = readiness_section

        if incomplete_readiness:
            pathway_name = incomplete_readiness.get(
                "pathway_name", "your immigration pathway"
            )
            missing = incomplete_readiness.get("missing_required", 0)

            return {
                "type": "complete_readiness",
                "title": "Complete document checklist",
                "description": (
                    f"Your {pathway_name} checklist has "
                    f"{missing} missing required document(s)."
                ),
                "priority": "normal",
            }

        # 5. Continue any active journey that has incomplete steps.
        journeys = journey_section.get("journeys", [])

        incomplete_journey = next(
            (
                item
                for item in journeys
                if item.get("has_roadmap")
                and item.get("completion_percentage", 0) < 100
            ),
            None,
        )

        # Backward-compatible fallback for the legacy single-journey shape.
        if incomplete_journey is None and not journeys:
            if (
                journey_section.get("has_roadmap")
                and journey_section.get("completion_percentage", 0) < 100
            ):
                incomplete_journey = journey_section

        if incomplete_journey:
            pathway_name = incomplete_journey.get(
                "pathway_name", "your immigration journey"
            )
            percentage = incomplete_journey.get("completion_percentage", 0)

            return {
                "type": "continue_roadmap",
                "title": "Continue your journey",
                "description": (
                    f"Your {pathway_name} is {percentage}% complete."
                ),
                "priority": "normal",
            }

        # 6. Start a journey if the applicant has none.
        if not journey_section.get("has_roadmap"):
            return {
                "type": "start_roadmap",
                "title": "Start your immigration journey",
                "description": (
                    "Choose a pathway to begin your personalized roadmap."
                ),
                "priority": "high",
            }

        # 7. All currently evaluated actions are complete.
        return {
            "type": "no_action",
            "title": "You're all caught up",
            "description": (
                "No pending actions. Review your journeys or prepare "
                "for next steps."
            ),
            "priority": "low",
        }
