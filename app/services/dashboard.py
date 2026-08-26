# app/services/dashboard.py
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.user_roadmap import UserRoadmapService
from app.services.document import DocumentService
from app.services.sop import SOPService
from app.core.exceptions import NotFoundException


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
    async def _build_journey_section(db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """
        Get user's active roadmap state.
        Gracefully handles no roadmap.
        """
        try:
            summary = await UserRoadmapService.get_roadmap_summary(db, user_id)

            if summary.get("status") == "no_roadmap":
                return {
                    "has_roadmap": False,
                    "pathway_name": None,
                    "pathway_slug": None,
                    "status": None,
                    "completed_steps": 0,
                    "total_steps": 0,
                    "completion_percentage": 0,
                    "next_step": None,
                }

            return {
                "has_roadmap": True,
                "pathway_name": summary.get("pathway_name"),
                "pathway_slug": summary.get("pathway_slug"),
                "status": summary.get("status"),
                "completed_steps": summary.get("completed_steps", 0),
                "total_steps": summary.get("total_steps", 0),
                "completion_percentage": summary.get("completion_percentage", 0),
                "next_step": summary.get("next_step"),
            }
        except NotFoundException:
            return {
                "has_roadmap": False,
                "pathway_name": None,
                "pathway_slug": None,
                "status": None,
                "completed_steps": 0,
                "total_steps": 0,
                "completion_percentage": 0,
                "next_step": None,
            }

    @staticmethod
    async def _build_readiness_section(db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """
        Get user's document readiness state.
        Gracefully handles no checklist.
        """
        try:
            # Get active roadmap first to find pathway
            summary = await UserRoadmapService.get_roadmap_summary(db, user_id)

            if summary.get("status") == "no_roadmap":
                return {
                    "has_checklist": False,
                    "pathway_name": None,
                    "completion_percentage": 0,
                    "total_required": 0,
                    "completed_required": 0,
                    "missing_required": 0,
                    "missing_documents": [],
                }

            # Get pathway ID from roadmap
            roadmap = await UserRoadmapService.get_user_roadmap(db, user_id)
            pathway_id = str(roadmap.pathway_id)

            readiness = await DocumentService.get_readiness_summary(
                db, user_id, pathway_id
            )

            return {
                "has_checklist": True,
                "pathway_name": readiness.get("pathway_name"),
                "completion_percentage": readiness.get("completion_percentage", 0),
                "total_required": readiness.get("total_required", 0),
                "completed_required": readiness.get("completed_required", 0),
                "missing_required": readiness.get("missing_required", 0),
                "missing_documents": readiness.get("missing_documents", []),
            }
        except NotFoundException:
            return {
                "has_checklist": False,
                "pathway_name": None,
                "completion_percentage": 0,
                "total_required": 0,
                "completed_required": 0,
                "missing_required": 0,
                "missing_documents": [],
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
        Deterministic next-action strategy based ONLY on existing application state.
        Priority: needs_clarification > continue_sop > review_draft > complete_readiness > continue_roadmap > start_roadmap > no_action
        """

        # 1. needs_clarification — any draft with missing information
        for doc in sop_documents:
            latest_draft = doc.get("latest_draft")
            if latest_draft and latest_draft.get("generation_status") == "needs_clarification":
                return {
                    "type": "needs_clarification",
                    "title": "Resolve missing information",
                    "description": f"Your {doc.get('document_type', 'document').upper()} has missing information that needs your attention.",
                    "priority": "high",
                }
            if latest_draft and latest_draft.get("missing_information_count", 0) > 0:
                return {
                    "type": "needs_clarification",
                    "title": "Resolve missing information",
                    "description": f"Your {doc.get('document_type', 'document').upper()} has {latest_draft['missing_information_count']} missing item(s).",
                    "priority": "high",
                }

        # 2. continue_sop — SOP with unanswered questions
        for doc in sop_documents:
            if doc.get("answered_questions", 0) < doc.get("total_questions", 0):
                remaining = doc["total_questions"] - doc["answered_questions"]
                return {
                    "type": "continue_sop",
                    "title": f"Continue your {doc.get('document_type', 'SOP').upper()}",
                    "description": f"You have {remaining} unanswered question(s) in your {doc.get('document_type', 'SOP').upper()}.",
                    "priority": "high",
                }

        # 3. review_draft — generated draft not yet finalized
        for doc in sop_documents:
            if doc.get("status") == "generated" and doc.get("latest_draft"):
                return {
                    "type": "review_draft",
                    "title": "Review your generated draft",
                    "description": f"Your {doc.get('document_type', 'SOP').upper()} draft is ready for review.",
                    "priority": "normal",
                }

        # 4. complete_readiness — missing required documents
        if readiness_section.get("has_checklist") and readiness_section.get("missing_required", 0) > 0:
            return {
                "type": "complete_readiness",
                "title": "Complete document checklist",
                "description": f"You have {readiness_section['missing_required']} missing required document(s).",
                "priority": "normal",
            }

        # 5. continue_roadmap — active roadmap with incomplete steps
        if journey_section.get("has_roadmap") and journey_section.get("completion_percentage", 0) < 100:
            return {
                "type": "continue_roadmap",
                "title": "Continue your journey",
                "description": f"Your {journey_section.get('pathway_name', 'roadmap')} is {journey_section.get('completion_percentage', 0)}% complete.",
                "priority": "normal",
            }

        # 6. start_roadmap — no roadmap
        if not journey_section.get("has_roadmap"):
            return {
                "type": "start_roadmap",
                "title": "Start your immigration journey",
                "description": "Choose a pathway to begin your personalized roadmap.",
                "priority": "high",
            }

        # 7. no_action — everything complete
        return {
            "type": "no_action",
            "title": "You're all caught up",
            "description": "No pending actions. Review your journey or prepare for next steps.",
            "priority": "low",
        }