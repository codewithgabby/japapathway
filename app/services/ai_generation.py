from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.sop import (
    ApplicantDocumentDraft,
    ApplicantDocumentResponse,
    GenerationStatus,
    ApplicantDocumentStatus,
)

from app.services.sop import SOPService
from app.services.content import ContentService
from app.services.ai_provider import (
    AIDocumentService,
    AIProviderFactory,
)
from app.services.audit import AuditService

from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
)


class AIGenerationService:
    """Core AI document generation orchestration service."""

    def __init__(self, provider_name: Optional[str] = None):
        self.provider = AIProviderFactory.get_provider(provider_name)
        self.ai_document_service = AIDocumentService(self.provider)

    # ============================================================
    # GENERATION CONTEXT
    # ============================================================

    async def build_generation_context(
        self,
        db: AsyncSession,
        document_id: str,
        section_id: str,
        user_id: str,
        previous_draft: Optional[ApplicantDocumentDraft] = None,
    ) -> Dict[str, Any]:
        """
        Assemble the complete context required for AI generation.

        Information is kept separated into:

        1. Applicant facts
        2. Template/framework
        3. Admin guidance
        4. AI guidance
        5. Published Content Engine knowledge
        6. Previous draft
        """

        # --------------------------------------------------------
        # Verify document ownership
        # --------------------------------------------------------

        document = await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        # --------------------------------------------------------
        # Load section
        # --------------------------------------------------------

        section = await SOPService.get_section(
            db,
            section_id,
        )

        # --------------------------------------------------------
        # Verify section belongs to document template
        # --------------------------------------------------------

        if str(section.template_id) != str(document.template_id):
            raise BadRequestException(
                "Section does not belong to this document's template"
            )

        # --------------------------------------------------------
        # Load template
        # --------------------------------------------------------

        template = await SOPService.get_template(
            db,
            str(document.template_id),
        )

        # --------------------------------------------------------
        # Load questions
        # --------------------------------------------------------

        questions = await SOPService.get_section_questions(
            db,
            section_id,
        )

        # --------------------------------------------------------
        # Load applicant answers
        # --------------------------------------------------------

        responses = []

        for question in questions:

            result = await db.execute(
                select(ApplicantDocumentResponse).where(
                    ApplicantDocumentResponse.applicant_document_id
                    == document_id,
                    ApplicantDocumentResponse.question_id
                    == question.id,
                    ApplicantDocumentResponse.is_deleted
                    == False,
                )
            )

            response = result.scalar_one_or_none()

            responses.append(
                {
                    "question_id": str(question.id),
                    "question_text": question.question_text,
                    "question_type": question.question_type.value,
                    "answer_text": (
                        response.answer_text
                        if response
                        else None
                    ),
                    "is_required": question.is_required,
                    "is_answered": bool(
                        response
                        and response.answer_text
                        and response.answer_text.strip()
                    ),
                    "admin_guidance": question.admin_guidance,
                    "ai_guidance": question.ai_guidance,
                }
            )

        # --------------------------------------------------------
        # Load published Content Engine knowledge
        # --------------------------------------------------------

        published_articles = (
            await ContentService.get_published_articles_by_pathway(
                db,
                str(document.pathway_id),
            )
        )

        knowledge_sources = []

        for article in published_articles:

            knowledge_sources.append(
                {
                    "article_id": str(article.id),
                    "article_version": article.version,
                    "title": article.title,
                    "category_id": str(article.category_id),
                    "summary": article.summary,
                    "content": article.content,
                }
            )

        # --------------------------------------------------------
        # Detect missing required information
        # --------------------------------------------------------

        missing_information = []

        for response in responses:

            if (
                response["is_required"]
                and not response["is_answered"]
            ):
                missing_information.append(
                    f"Missing answer for: "
                    f"{response['question_text']}"
                )

        # --------------------------------------------------------
        # Return complete context
        # --------------------------------------------------------

        return {
            "document_id": str(document.id),
            "document_type": document.document_type.value,
            "pathway_id": str(document.pathway_id),

            "template_id": str(template.id),
            "template_name": template.name,
            "template_admin_guidance": (
                template.admin_guidance
            ),
            "template_ai_guidance": (
                template.ai_guidance
            ),

            "section_id": str(section.id),
            "section_name": section.name,
            "section_purpose": section.purpose,
            "section_admin_guidance": (
                section.admin_guidance
            ),
            "section_ai_guidance": (
                section.ai_guidance
            ),

            "applicant_responses": responses,

            "published_knowledge": knowledge_sources,

            "previous_draft": (
                previous_draft.content
                if previous_draft
                else None
            ),

            "missing_information": missing_information,
        }

    # ============================================================
    # GENERATE
    # ============================================================

    async def generate_section_draft(
        self,
        db: AsyncSession,
        document_id: str,
        section_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Generate a draft for a single document section.
        """

        context = await self.build_generation_context(
            db=db,
            document_id=document_id,
            section_id=section_id,
            user_id=user_id,
        )

        # --------------------------------------------------------
        # Missing information
        # --------------------------------------------------------

        if context["missing_information"]:

            return {
                "status": GenerationStatus.NEEDS_CLARIFICATION.value,
                "content": None,
                "missing_information": (
                    context["missing_information"]
                ),
                "warnings": [],
                "knowledge_sources": (
                    context["published_knowledge"]
                ),
                "provider": self.provider.provider_name,
                "model": self.provider.model_name,
            }

        # --------------------------------------------------------
        # Prepare applicant answers
        # --------------------------------------------------------

        applicant_answers = [
            {
                "question_text": response["question_text"],
                "answer_text": response["answer_text"],
                "ai_guidance": response["ai_guidance"],
            }
            for response in context["applicant_responses"]
            if response["is_answered"]
        ]

        # --------------------------------------------------------
        # Generate content
        # --------------------------------------------------------

        try:

            generated_content = (
                await self.ai_document_service.generate_section(
                    section_data={
                        "name": context["section_name"],
                        "purpose": context["section_purpose"],
                    },
                    applicant_answers=applicant_answers,
                    template_guidance=(
                        context["template_admin_guidance"]
                    ),
                    section_guidance=(
                        context["section_ai_guidance"]
                    ),
                    admin_guidance=(
                        context["section_admin_guidance"]
                    ),
                    published_knowledge=(
                        context["published_knowledge"]
                    ),
                )
            )

        except Exception as e:

            return {
                "status": GenerationStatus.FAILED.value,
                "content": None,
                "missing_information": [],
                "warnings": [
                    f"Generation failed: {str(e)}"
                ],
                "knowledge_sources": (
                    context["published_knowledge"]
                ),
                "provider": self.provider.provider_name,
                "model": self.provider.model_name,
            }

        # --------------------------------------------------------
        # Validate generated content
        # --------------------------------------------------------

        warnings = self._validate_generated_content(
            generated_content,
            applicant_answers,
        )

        # --------------------------------------------------------
        # Save draft
        # --------------------------------------------------------

        draft = await SOPService.save_draft(
            db=db,
            document_id=document_id,
            section_id=section_id,
            content=generated_content,
            ai_provider=self.provider.provider_name,
            ai_model=self.provider.model_name,
            user_id=user_id,
        )

        # --------------------------------------------------------
        # Store Sprint 6 metadata
        # --------------------------------------------------------

        draft.generation_status = (
            GenerationStatus.GENERATED
        )

        draft.warnings = warnings or None

        draft.knowledge_sources = (
            context["published_knowledge"]
        )

        draft.generation_metadata = {
            "template_id": context["template_id"],
            "pathway_id": context["pathway_id"],
            "section_name": context["section_name"],
        }

        await db.flush()

        # --------------------------------------------------------
        # Update document status
        # --------------------------------------------------------

        document = await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        document.status = (
            ApplicantDocumentStatus.GENERATED
        )

        document.updated_by = user_id

        # --------------------------------------------------------
        # Audit
        # --------------------------------------------------------

        await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="ai_draft_generated",
            entity_type="applicant_document_draft",
            entity_id=str(draft.id),
            changes={
                "document_id": document_id,
                "section_id": section_id,
                "provider": self.provider.provider_name,
                "model": self.provider.model_name,
                "status": "generated",
                "warnings_count": len(warnings),
            },
        )

        return {
            "status": GenerationStatus.GENERATED.value,
            "content": generated_content,
            "missing_information": [],
            "warnings": warnings,
            "knowledge_sources": (
                context["published_knowledge"]
            ),
            "provider": self.provider.provider_name,
            "model": self.provider.model_name,
            "draft_id": str(draft.id),
            "draft_version": draft.version,
        }

    # ============================================================
    # REGENERATE
    # ============================================================

    async def regenerate_section_draft(
        self,
        db: AsyncSession,
        document_id: str,
        section_id: str,
        user_id: str,
        instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Regenerate the current section draft.

        Previous versions are preserved.
        """

        # --------------------------------------------------------
        # Find current draft
        # --------------------------------------------------------

        result = await db.execute(
            select(ApplicantDocumentDraft).where(
                ApplicantDocumentDraft.applicant_document_id
                == document_id,
                ApplicantDocumentDraft.section_id
                == section_id,
                ApplicantDocumentDraft.is_current
                == True,
                ApplicantDocumentDraft.is_deleted
                == False,
            )
        )

        previous_draft = result.scalar_one_or_none()

        # --------------------------------------------------------
        # Build context
        # --------------------------------------------------------

        context = await self.build_generation_context(
            db=db,
            document_id=document_id,
            section_id=section_id,
            user_id=user_id,
            previous_draft=previous_draft,
        )

        # --------------------------------------------------------
        # Missing information
        # --------------------------------------------------------

        if context["missing_information"]:

            return {
                "status": GenerationStatus.NEEDS_CLARIFICATION.value,
                "content": None,
                "missing_information": (
                    context["missing_information"]
                ),
                "warnings": [],
                "knowledge_sources": (
                    context["published_knowledge"]
                ),
                "provider": self.provider.provider_name,
                "model": self.provider.model_name,
            }

        # --------------------------------------------------------
        # Applicant answers
        # --------------------------------------------------------

        applicant_answers = [
            {
                "question_text": response["question_text"],
                "answer_text": response["answer_text"],
                "ai_guidance": response["ai_guidance"],
            }
            for response in context["applicant_responses"]
            if response["is_answered"]
        ]

        # --------------------------------------------------------
        # Regenerate
        # --------------------------------------------------------

        try:

            regenerated_content = (
                await self.ai_document_service.regenerate_section(
                    section_data={
                        "name": context["section_name"],
                        "purpose": context["section_purpose"],
                    },
                    applicant_answers=applicant_answers,
                    previous_draft=context["previous_draft"],
                    instruction=instruction,
                    template_guidance=(
                        context["template_admin_guidance"]
                    ),
                    section_guidance=(
                        context["section_ai_guidance"]
                    ),
                    admin_guidance=(
                        context["section_admin_guidance"]
                    ),
                    published_knowledge=(
                        context["published_knowledge"]
                    ),
                )
            )

        except Exception as e:

            return {
                "status": GenerationStatus.FAILED.value,
                "content": None,
                "missing_information": [],
                "warnings": [
                    f"Regeneration failed: {str(e)}"
                ],
                "knowledge_sources": (
                    context["published_knowledge"]
                ),
                "provider": self.provider.provider_name,
                "model": self.provider.model_name,
            }

        # --------------------------------------------------------
        # Validate
        # --------------------------------------------------------

        warnings = self._validate_generated_content(
            regenerated_content,
            applicant_answers,
        )

        # --------------------------------------------------------
        # Save new version
        # --------------------------------------------------------

        draft = await SOPService.save_draft(
            db=db,
            document_id=document_id,
            section_id=section_id,
            content=regenerated_content,
            ai_provider=self.provider.provider_name,
            ai_model=self.provider.model_name,
            user_id=user_id,
        )

        draft.generation_status = (
            GenerationStatus.GENERATED
        )

        draft.warnings = warnings or None

        draft.knowledge_sources = (
            context["published_knowledge"]
        )

        draft.source_draft_id = (
            previous_draft.id
            if previous_draft
            else None
        )

        draft.generation_metadata = {
            "template_id": context["template_id"],
            "pathway_id": context["pathway_id"],
            "section_name": context["section_name"],
            "regeneration_instruction": instruction,
        }

        await db.flush()

        # --------------------------------------------------------
        # Audit
        # --------------------------------------------------------

        await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="ai_draft_regenerated",
            entity_type="applicant_document_draft",
            entity_id=str(draft.id),
            changes={
                "document_id": document_id,
                "section_id": section_id,
                "provider": self.provider.provider_name,
                "model": self.provider.model_name,
                "status": "regenerated",
                "instruction": instruction,
                "source_draft_id": (
                    str(previous_draft.id)
                    if previous_draft
                    else None
                ),
            },
        )

        return {
            "status": GenerationStatus.GENERATED.value,
            "content": regenerated_content,
            "missing_information": [],
            "warnings": warnings,
            "knowledge_sources": (
                context["published_knowledge"]
            ),
            "provider": self.provider.provider_name,
            "model": self.provider.model_name,
            "draft_id": str(draft.id),
            "draft_version": draft.version,
        }

    # ============================================================
    # IMPROVE
    # ============================================================

    async def improve_section_draft(
        self,
        db: AsyncSession,
        document_id: str,
        section_id: str,
        user_id: str,
        instruction: str,
    ) -> Dict[str, Any]:
        """
        Improve an existing draft using a required instruction.
        """

        if not instruction or not instruction.strip():
            raise BadRequestException(
                "Instruction is required for improvement"
            )

        return await self.regenerate_section_draft(
            db=db,
            document_id=document_id,
            section_id=section_id,
            user_id=user_id,
            instruction=instruction,
        )

    # ============================================================
    # FINALIZE
    # ============================================================

    async def finalize_draft(
        self,
        db: AsyncSession,
        document_id: str,
        draft_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Finalize a draft.

        Previous versions are preserved.
        """

        # --------------------------------------------------------
        # Verify document ownership
        # --------------------------------------------------------

        document = await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        # --------------------------------------------------------
        # Verify draft
        # --------------------------------------------------------

        result = await db.execute(
            select(ApplicantDocumentDraft).where(
                ApplicantDocumentDraft.id == draft_id,
                ApplicantDocumentDraft.applicant_document_id
                == document_id,
                ApplicantDocumentDraft.is_deleted
                == False,
            )
        )

        draft = result.scalar_one_or_none()

        if not draft:
            raise NotFoundException("Draft")

        # --------------------------------------------------------
        # Finalize draft and document
        # --------------------------------------------------------

        # Make this draft the finalized/current draft
        draft.is_current = True
        draft.generation_status = GenerationStatus.GENERATED


        # Finalize the document
        document.status = ApplicantDocumentStatus.FINAL
        document.updated_by = user_id

        await db.flush()

        # --------------------------------------------------------
        # Audit
        # --------------------------------------------------------

        await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="ai_draft_finalized",
            entity_type="applicant_document",
            entity_id=document_id,
            changes={
                "draft_id": str(draft.id),
                "draft_version": draft.version,
                "document_status": "final",
                "provider": draft.ai_provider,
                "model": draft.ai_model,
            },
        )

        return {
            "status": "finalized",
            "document_status": "final",
            "draft_id": str(draft.id),
            "draft_version": draft.version,
            "message": (
                "Draft finalized successfully. "
                "Previous versions preserved."
            ),
        }

    # ============================================================
    # DRAFT VERSIONS
    # ============================================================

    async def get_draft_versions(
        self,
        db: AsyncSession,
        document_id: str,
        section_id: str,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Return all draft versions for a section.
        """

        # --------------------------------------------------------
        # Verify ownership
        # --------------------------------------------------------

        await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        # --------------------------------------------------------
        # Load drafts
        # --------------------------------------------------------

        result = await db.execute(
            select(ApplicantDocumentDraft)
            .where(
                ApplicantDocumentDraft.applicant_document_id
                == document_id,
                ApplicantDocumentDraft.section_id
                == section_id,
                ApplicantDocumentDraft.is_deleted
                == False,
            )
            .order_by(
                ApplicantDocumentDraft.version.desc()
            )
        )

        drafts = result.scalars().all()

        # --------------------------------------------------------
        # Serialize
        # --------------------------------------------------------

        return [
            {
                "draft_id": str(draft.id),
                "version": draft.version,
                "content": draft.content,
                "ai_provider": draft.ai_provider,
                "ai_model": draft.ai_model,
                "generation_status": (
                    draft.generation_status.value
                    if draft.generation_status
                    else None
                ),
                "warnings": draft.warnings,
                "missing_information": (
                    draft.missing_information
                ),
                "knowledge_sources": (
                    draft.knowledge_sources
                ),
                "source_draft_id": (
                    str(draft.source_draft_id)
                    if draft.source_draft_id
                    else None
                ),
                "generation_metadata": (
                    draft.generation_metadata
                ),
                "is_current": draft.is_current,
                "created_at": (
                    draft.created_at.isoformat()
                    if draft.created_at
                    else None
                ),
            }
            for draft in drafts
        ]

    # ============================================================
    # VALIDATION
    # ============================================================

    def _validate_generated_content(
        self,
        generated_content: str,
        applicant_answers: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Basic post-generation validation.

        Returns warnings rather than hard failures.
        """

        warnings = []

        # --------------------------------------------------------
        # Empty/short content
        # --------------------------------------------------------

        if (
            not generated_content
            or len(generated_content.strip()) < 10
        ):
            warnings.append(
                "Generated content is very short"
            )

        # --------------------------------------------------------
        # Basic fact preservation check
        # --------------------------------------------------------

        for answer in applicant_answers:

            answer_text = answer.get("answer_text")

            if not answer_text:
                continue

            if len(answer_text) <= 20:
                continue

            key_phrases = answer_text.split()[:5]

            found = any(
                phrase.lower()
                in generated_content.lower()
                for phrase in key_phrases
                if len(phrase) > 3
            )

            if not found:
                warnings.append(
                    "Possible fact preservation issue for: "
                    f"{answer['question_text'][:50]}..."
                )

        return warnings