from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any

from app.models.sop import (
    DocumentTemplate,
    DocumentTemplateSection,
    DocumentTemplateQuestion,
    ApplicantDocument,
    ApplicantDocumentResponse,
    ApplicantDocumentDraft,
    ApplicantDocumentRelationship,
    DocumentTemplateStatus,
    DocumentType,
    ApplicantDocumentStatus,
    GenerationStatus,
)
from app.services.pathway import PathwayService
from app.core.exceptions import NotFoundException, BadRequestException


class SOPService:

    # ============================================================
    # ADMIN: DOCUMENT TEMPLATE CRUD
    # ============================================================

    @staticmethod
    async def create_template(
        db: AsyncSession,
        data: dict,
        user_id: str,
    ) -> DocumentTemplate:
        await PathwayService.get_pathway_by_id(db, data["pathway_id"])

        result = await db.execute(
            select(DocumentTemplate).where(
                DocumentTemplate.slug == data["slug"],
                DocumentTemplate.is_deleted.is_(False),
            )
        )

        if result.scalar_one_or_none():
            raise BadRequestException(
                "Template with this slug already exists"
            )

        template = DocumentTemplate(
            **data,
            created_by=user_id,
            updated_by=user_id,
        )

        db.add(template)
        await db.flush()

        return template

    @staticmethod
    async def get_template(
        db: AsyncSession,
        template_id: str,
    ) -> DocumentTemplate:
        result = await db.execute(
            select(DocumentTemplate).where(
                DocumentTemplate.id == template_id,
                DocumentTemplate.is_deleted.is_(False),
            )
        )

        template = result.scalar_one_or_none()

        if not template:
            raise NotFoundException("Document template")

        return template

    @staticmethod
    async def get_template_by_slug(
        db: AsyncSession,
        slug: str,
    ) -> DocumentTemplate:
        result = await db.execute(
            select(DocumentTemplate).where(
                DocumentTemplate.slug == slug,
                DocumentTemplate.is_deleted.is_(False),
            )
        )

        template = result.scalar_one_or_none()

        if not template:
            raise NotFoundException("Document template")

        return template

    @staticmethod
    async def get_all_templates(
        db: AsyncSession,
        pathway_id: Optional[str] = None,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[DocumentTemplate]:

        query = select(DocumentTemplate).where(
            DocumentTemplate.is_deleted.is_(False)
        )

        if pathway_id:
            query = query.where(
                DocumentTemplate.pathway_id == pathway_id
            )

        if document_type:
            query = query.where(
                DocumentTemplate.document_type
                == DocumentType(document_type)
            )

        if status:
            query = query.where(
                DocumentTemplate.status
                == DocumentTemplateStatus(status)
            )

        if not include_inactive:
            query = query.where(
                DocumentTemplate.is_active.is_(True)
            )

        query = query.order_by(DocumentTemplate.created_at)

        result = await db.execute(query)

        return result.scalars().all()

    @staticmethod
    async def update_template(
        db: AsyncSession,
        template_id: str,
        data: dict,
        user_id: str,
    ) -> DocumentTemplate:

        template = await SOPService.get_template(
            db,
            template_id,
        )

        if "slug" in data and data["slug"] != template.slug:

            result = await db.execute(
                select(DocumentTemplate).where(
                    DocumentTemplate.slug == data["slug"],
                    DocumentTemplate.id != template_id,
                    DocumentTemplate.is_deleted.is_(False),
                )
            )

            if result.scalar_one_or_none():
                raise BadRequestException(
                    "Template with this slug already exists"
                )

        for key, value in data.items():
            setattr(template, key, value)

        template.updated_by = user_id

        await db.flush()

        return template

    @staticmethod
    async def change_template_status(
        db: AsyncSession,
        template_id: str,
        status: str,
        user_id: str,
    ) -> DocumentTemplate:

        template = await SOPService.get_template(
            db,
            template_id,
        )

        template.status = DocumentTemplateStatus(status)
        template.updated_by = user_id

        if status == "published":
            template.version += 1

        await db.flush()

        return template

    @staticmethod
    async def delete_template(
        db: AsyncSession,
        template_id: str,
        user_id: str,
    ) -> None:

        template = await SOPService.get_template(
            db,
            template_id,
        )

        template.soft_delete(user_id)

        await db.flush()

    # ============================================================
    # ADMIN: SECTION CRUD
    # ============================================================

    @staticmethod
    async def create_section(
        db: AsyncSession,
        template_id: str,
        data: dict,
        user_id: str,
    ) -> DocumentTemplateSection:

        await SOPService.get_template(
            db,
            template_id,
        )

        section = DocumentTemplateSection(
            template_id=template_id,
            created_by=user_id,
            updated_by=user_id,
            **data,
        )

        db.add(section)

        await db.flush()

        return section

    @staticmethod
    async def get_section(
        db: AsyncSession,
        section_id: str,
    ) -> DocumentTemplateSection:

        result = await db.execute(
            select(DocumentTemplateSection).where(
                DocumentTemplateSection.id == section_id,
                DocumentTemplateSection.is_deleted.is_(False),
            )
        )

        section = result.scalar_one_or_none()

        if not section:
            raise NotFoundException("Section")

        return section

    @staticmethod
    async def get_template_sections(
        db: AsyncSession,
        template_id: str,
    ) -> List[DocumentTemplateSection]:

        await SOPService.get_template(
            db,
            template_id,
        )

        result = await db.execute(
            select(DocumentTemplateSection).where(
                DocumentTemplateSection.template_id == template_id,
                DocumentTemplateSection.is_deleted.is_(False),
                DocumentTemplateSection.is_active.is_(True),
            ).order_by(
                DocumentTemplateSection.order_index
            )
        )

        return result.scalars().all()

    @staticmethod
    async def update_section(
        db: AsyncSession,
        section_id: str,
        data: dict,
        user_id: str,
    ) -> DocumentTemplateSection:

        section = await SOPService.get_section(
            db,
            section_id,
        )

        for key, value in data.items():
            setattr(section, key, value)

        section.updated_by = user_id

        await db.flush()

        return section

    @staticmethod
    async def delete_section(
        db: AsyncSession,
        section_id: str,
        user_id: str,
    ) -> None:

        section = await SOPService.get_section(
            db,
            section_id,
        )

        section.soft_delete(user_id)

        await db.flush()

    # ============================================================
    # ADMIN: QUESTION CRUD
    # ============================================================

    @staticmethod
    async def create_question(
        db: AsyncSession,
        section_id: str,
        data: dict,
        user_id: str,
    ) -> DocumentTemplateQuestion:

        await SOPService.get_section(
            db,
            section_id,
        )

        question = DocumentTemplateQuestion(
            section_id=section_id,
            created_by=user_id,
            updated_by=user_id,
            **data,
        )

        db.add(question)

        await db.flush()

        return question

    @staticmethod
    async def get_question(
        db: AsyncSession,
        question_id: str,
    ) -> DocumentTemplateQuestion:

        result = await db.execute(
            select(DocumentTemplateQuestion).where(
                DocumentTemplateQuestion.id == question_id,
                DocumentTemplateQuestion.is_deleted.is_(False),
            )
        )

        question = result.scalar_one_or_none()

        if not question:
            raise NotFoundException("Question")

        return question

    @staticmethod
    async def get_section_questions(
        db: AsyncSession,
        section_id: str,
    ) -> List[DocumentTemplateQuestion]:

        await SOPService.get_section(
            db,
            section_id,
        )

        result = await db.execute(
            select(DocumentTemplateQuestion).where(
                DocumentTemplateQuestion.section_id == section_id,
                DocumentTemplateQuestion.is_deleted.is_(False),
                DocumentTemplateQuestion.is_active.is_(True),
            ).order_by(
                DocumentTemplateQuestion.order_index
            )
        )

        return result.scalars().all()

    @staticmethod
    async def update_question(
        db: AsyncSession,
        question_id: str,
        data: dict,
        user_id: str,
    ) -> DocumentTemplateQuestion:

        question = await SOPService.get_question(
            db,
            question_id,
        )

        for key, value in data.items():
            setattr(question, key, value)

        question.updated_by = user_id

        await db.flush()

        return question

    @staticmethod
    async def delete_question(
        db: AsyncSession,
        question_id: str,
        user_id: str,
    ) -> None:

        question = await SOPService.get_question(
            db,
            question_id,
        )

        question.soft_delete(user_id)

        await db.flush()

    # ============================================================
    # APPLICANT: DOCUMENT MANAGEMENT
    # ============================================================

    @staticmethod
    async def create_applicant_document(
        db: AsyncSession,
        user_id: str,
        data: dict,
    ) -> ApplicantDocument:

        template = await SOPService.get_template(
            db,
            data["template_id"],
        )

        if template.status != DocumentTemplateStatus.PUBLISHED:
            raise BadRequestException(
                "Template is not available"
            )

        if str(template.pathway_id) != str(data["pathway_id"]):
            raise BadRequestException(
                "Template does not belong to this pathway"
            )

        if data["document_type"] == DocumentType.SOP:

            result = await db.execute(
                select(ApplicantDocument).where(
                    ApplicantDocument.user_id == user_id,
                    ApplicantDocument.pathway_id
                    == data["pathway_id"],
                    ApplicantDocument.document_type
                    == DocumentType.SOP,
                    ApplicantDocument.is_deleted.is_(False),
                    ApplicantDocument.status
                    != ApplicantDocumentStatus.FINAL,
                )
            )

            existing = result.scalar_one_or_none()

            if existing:
                raise BadRequestException(
                    "You already have an active SOP for this pathway"
                )

        applicant_document = ApplicantDocument(
            user_id=user_id,
            **data,
        )

        db.add(applicant_document)

        await db.flush()

        return applicant_document


    @staticmethod
    async def get_applicant_document(
        db: AsyncSession,
        document_id: str,
        user_id: Optional[str] = None,
    ) -> ApplicantDocument:

        query = select(ApplicantDocument).where(
            ApplicantDocument.id == document_id,
            ApplicantDocument.is_deleted.is_(False),
        )

        if user_id:
            query = query.where(
                ApplicantDocument.user_id == user_id
            )

        result = await db.execute(query)

        document = result.scalar_one_or_none()

        if not document:
            raise NotFoundException(
                "Applicant document"
            )

        return document

    @staticmethod
    async def get_user_documents(
        db: AsyncSession,
        user_id: str,
        document_type: Optional[str] = None,
    ) -> List[ApplicantDocument]:

        query = select(ApplicantDocument).where(
            ApplicantDocument.user_id == user_id,
            ApplicantDocument.is_deleted.is_(False),
        )

        if document_type:
            query = query.where(
                ApplicantDocument.document_type
                == DocumentType(document_type)
            )

        query = query.order_by(
            ApplicantDocument.created_at.desc()
        )

        result = await db.execute(query)

        return result.scalars().all()

    @staticmethod
    async def update_applicant_document_status(
        db: AsyncSession,
        document_id: str,
        status: str,
        user_id: str,
    ) -> ApplicantDocument:

        document = await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        document.status = ApplicantDocumentStatus(status)

        await db.flush()

        return document

    # ============================================================
    # APPLICANT: RESPONSE MANAGEMENT
    # ============================================================

    @staticmethod
    async def save_response(
        db: AsyncSession,
        document_id: str,
        question_id: str,
        answer_text: str,
        user_id: str,
    ) -> ApplicantDocumentResponse:

        document = await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        question = await SOPService.get_question(
            db,
            question_id,
        )

        section = await SOPService.get_section(
            db,
            str(question.section_id),
        )

        if str(section.template_id) != str(document.template_id):
            raise BadRequestException(
               "Question does not belong to this document template"
            )

        result = await db.execute(
            select(ApplicantDocumentResponse).where(
                ApplicantDocumentResponse.applicant_document_id
                == document_id,
                ApplicantDocumentResponse.question_id
                == question_id,
                ApplicantDocumentResponse.is_deleted.is_(False),
            )
        )

        response = result.scalar_one_or_none()

        if response:

            response.answer_text = answer_text
            response.updated_by = user_id

        else:

            response = ApplicantDocumentResponse(
                applicant_document_id=document_id,
                question_id=question_id,
                answer_text=answer_text,
                created_by=user_id,
                updated_by=user_id,
            )

            db.add(response)

        await db.flush()

        return response

    @staticmethod
    async def save_batch_responses(
        db: AsyncSession,
        document_id: str,
        answers: List[dict],
        user_id: str,
    ) -> List[ApplicantDocumentResponse]:

        responses = []

        for answer in answers:

            response = await SOPService.save_response(
                db,
                document_id,
                answer["question_id"],
                answer["answer_text"],
                user_id,
            )

            responses.append(response)

        return responses

    @staticmethod
    async def get_document_responses(
        db: AsyncSession,
        document_id: str,
        user_id: str,
    ) -> List[Dict[str, Any]]:

        document = await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        sections = await SOPService.get_template_sections(
            db,
            str(document.template_id),
        )

        enriched = []

        for section in sections:

            questions = await SOPService.get_section_questions(
                db,
                str(section.id),
            )

            for question in questions:

                result = await db.execute(
                    select(ApplicantDocumentResponse).where(
                        ApplicantDocumentResponse.applicant_document_id
                        == document_id,
                        ApplicantDocumentResponse.question_id
                        == question.id,
                        ApplicantDocumentResponse.is_deleted.is_(False),
                    )
                )

                response = result.scalar_one_or_none()

                enriched.append(
                    {
                        "id": (
                            str(response.id)
                            if response
                            else None
                        ),
                        "question_id": str(question.id),
                        "question_text": question.question_text,
                        "answer_text": (
                            response.answer_text
                            if response
                            else None
                        ),
                        "is_required": question.is_required,
                        "is_answered": bool(
                            response and response.answer_text
                        ),
                        "section_id": str(section.id),
                        "section_name": section.name,
                        "order_index": question.order_index,
                    }
                )

        return enriched

    @staticmethod
    async def get_document_progress(
        db: AsyncSession,
        document_id: str,
        user_id: str,
    ) -> Dict[str, Any]:

        document = await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        responses = await SOPService.get_document_responses(
            db,
            document_id,
            user_id,
        )

        sections = await SOPService.get_template_sections(
            db,
            str(document.template_id),
        )

        total_questions = len(responses)

        answered_questions = len(
            [
                response
                for response in responses
                if response["is_answered"]
            ]
        )

        section_map = {}

        for response in responses:

            section_id = response["section_id"]

            if section_id not in section_map:
                section_map[section_id] = {
                    "total": 0,
                    "answered": 0,
                }

            section_map[section_id]["total"] += 1

            if response["is_answered"]:
                section_map[section_id]["answered"] += 1

        completed_sections = 0

        for counts in section_map.values():

            if (
                counts["total"] > 0
                and counts["answered"] == counts["total"]
            ):
                completed_sections += 1

        progress_percentage = (
            int(
                (answered_questions / total_questions)
                * 100
            )
            if total_questions > 0
            else 0
        )

        return {
            "document_id": str(document.id),
            "document_type": document.document_type.value,
            "status": document.status.value,
            "total_sections": len(sections),
            "completed_sections": completed_sections,
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "progress_percentage": progress_percentage,
            "current_section_order": (
                document.current_section_order
            ),
        }

    # ============================================================
    # APPLICANT: DRAFT MANAGEMENT
    # ============================================================

    @staticmethod
    async def save_draft(
        db: AsyncSession,
        document_id: str,
        section_id: str,
        content: str,
        ai_provider: Optional[str] = None,
        ai_model: Optional[str] = None,
        user_id: Optional[str] = None,
        generation_status: GenerationStatus = GenerationStatus.GENERATED,
        missing_information: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        knowledge_sources: Optional[List[Dict[str, Any]]] = None,
        source_draft_id: Optional[str] = None,
        generation_metadata: Optional[Dict[str, Any]] = None,
    ) -> ApplicantDocumentDraft:

        document = await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        section = await SOPService.get_section(
            db,
            section_id,
        )

        if str(section.template_id) != str(document.template_id):
            raise BadRequestException(
                "Section does not belong to this template"
            )

        result = await db.execute(
            select(ApplicantDocumentDraft).where(
                ApplicantDocumentDraft.applicant_document_id
                == document_id,
                ApplicantDocumentDraft.section_id
                == section_id,
                ApplicantDocumentDraft.is_deleted.is_(False),
            )
        )

        previous_drafts = result.scalars().all()

        for previous_draft in previous_drafts:
            previous_draft.is_current = False

        latest_version = (
            max(
                [
                    draft.version
                    for draft in previous_drafts
                ],
                default=0,
            )
            + 1
        )

        draft = ApplicantDocumentDraft(
            applicant_document_id=document_id,
            section_id=section_id,
            content=content,
            ai_provider=ai_provider,
            ai_model=ai_model,
            version=latest_version,
            is_current=True,
            generation_status=generation_status,
            missing_information=missing_information,
            warnings=warnings,
            knowledge_sources=knowledge_sources,
            source_draft_id=source_draft_id,
            generation_metadata=generation_metadata,
        )

        db.add(draft)

        await db.flush()

        return draft

    @staticmethod
    async def get_current_drafts(
        db: AsyncSession,
        document_id: str,
        user_id: str,
    ) -> List[ApplicantDocumentDraft]:

        await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        result = await db.execute(
            select(ApplicantDocumentDraft).where(
                ApplicantDocumentDraft.applicant_document_id
                == document_id,
                ApplicantDocumentDraft.is_current.is_(True),
                ApplicantDocumentDraft.is_deleted.is_(False),
            ).order_by(
                ApplicantDocumentDraft.created_at
            )
        )

        return result.scalars().all()

    @staticmethod
    async def get_draft_history(
        db: AsyncSession,
        document_id: str,
        section_id: str,
        user_id: str,
    ) -> List[ApplicantDocumentDraft]:

        await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        result = await db.execute(
            select(ApplicantDocumentDraft).where(
                ApplicantDocumentDraft.applicant_document_id
                == document_id,
                ApplicantDocumentDraft.section_id
                == section_id,
                ApplicantDocumentDraft.is_deleted.is_(False),
            ).order_by(
                ApplicantDocumentDraft.version.desc()
            )
        )

        return result.scalars().all()

    # ============================================================
    # APPLICANT: DOCUMENT RELATIONSHIPS
    # ============================================================

    @staticmethod
    async def create_relationship(
        db: AsyncSession,
        source_document_id: str,
        related_document_id: str,
        relationship_type: str,
        user_id: str,
    ) -> ApplicantDocumentRelationship:

        await SOPService.get_applicant_document(
            db,
            source_document_id,
            user_id,
        )

        await SOPService.get_applicant_document(
            db,
            related_document_id,
            user_id,
        )

        relationship = ApplicantDocumentRelationship(
            source_document_id=source_document_id,
            related_document_id=related_document_id,
            relationship_type=relationship_type,
        )

        db.add(relationship)

        await db.flush()

        return relationship

    @staticmethod
    async def get_document_relationships(
        db: AsyncSession,
        document_id: str,
        user_id: str,
    ) -> List[ApplicantDocumentRelationship]:

        await SOPService.get_applicant_document(
            db,
            document_id,
            user_id,
        )

        result = await db.execute(
            select(ApplicantDocumentRelationship).where(
                ApplicantDocumentRelationship.source_document_id
                == document_id,
                ApplicantDocumentRelationship.is_deleted.is_(False),
            )
        )

        return result.scalars().all()