from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.sop import SOPService
from app.services.ai_generation import AIGenerationService

from app.schemas.sop import (
    DocumentTemplateResponse,
    DocumentTemplateDetailResponse,
    DocumentTemplateSectionResponse,
    DocumentTemplateSectionDetailResponse,
    DocumentTemplateQuestionResponse,
    ApplicantDocumentCreate,
    ApplicantDocumentResponseSchema,
    ApplicantDocumentDetailResponse,
    ApplicantAnswerCreate,
    ApplicantAnswersBatchCreate,
    ApplicantAnswerUpdate,
    ApplicantAnswerResponse,
    ApplicantDraftResponse,
    ApplicantDocumentProgressResponse,
    DocumentRelationshipCreate,
    DocumentRelationshipResponse,
    GenerateDraftRequest,
    RegenerateDraftRequest,
    GenerateDraftResponse,
    FinalizeDraftRequest,
    FinalizeDraftResponse,
)

router = APIRouter()


# ============================================================
# PUBLIC TEMPLATE ENDPOINTS
# ============================================================

@router.get(
    "/sop/templates",
    response_model=List[DocumentTemplateResponse],
)
async def list_available_templates(
    pathway_id: Optional[str] = None,
    document_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List available published document templates for applicants.
    Only returns published and active templates.
    """

    templates = await SOPService.get_all_templates(
        db,
        pathway_id=pathway_id,
        document_type=document_type,
        status="published",
        include_inactive=False,
    )

    result = []

    for template in templates:
        sections = await SOPService.get_template_sections(
            db,
            str(template.id),
        )

        template.sections_count = len(sections)
        result.append(template)

    return result


@router.get(
    "/sop/templates/slug/{template_slug}",
    response_model=DocumentTemplateDetailResponse,
)
async def get_template_details(
    template_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get published template details with all sections and questions.
    """

    template = await SOPService.get_template_by_slug(
        db,
        template_slug,
    )

    if template.status.value != "published":
        from app.core.exceptions import BadRequestException

        raise BadRequestException(
            "Template is not available"
        )

    sections = await SOPService.get_template_sections(
        db,
        str(template.id),
    )

    section_responses = []

    for section in sections:
        questions = await SOPService.get_section_questions(
            db,
            str(section.id),
        )

        section_responses.append(
            DocumentTemplateSectionDetailResponse(
                id=str(section.id),
                template_id=str(section.template_id),
                name=section.name,
                slug=section.slug,
                description=section.description,
                purpose=section.purpose,
                order_index=section.order_index,
                admin_guidance=section.admin_guidance,
                ai_guidance=section.ai_guidance,
                is_active=section.is_active,
                questions_count=len(questions),
                questions=[
                    DocumentTemplateQuestionResponse(
                        id=str(q.id),
                        section_id=str(q.section_id),
                        question_text=q.question_text,
                        question_type=q.question_type.value,
                        help_text=q.help_text,
                        placeholder=q.placeholder,
                        admin_guidance=q.admin_guidance,
                        ai_guidance=q.ai_guidance,
                        is_required=q.is_required,
                        is_active=q.is_active,
                        order_index=q.order_index,
                    )
                    for q in questions
                ],
            )
        )

    return DocumentTemplateDetailResponse(
        id=str(template.id),
        pathway_id=str(template.pathway_id),
        document_type=template.document_type.value,
        name=template.name,
        slug=template.slug,
        description=template.description,
        status=template.status.value,
        version=template.version,
        admin_guidance=template.admin_guidance,
        ai_guidance=template.ai_guidance,
        is_active=template.is_active,
        sections_count=len(sections),
        created_at=template.created_at,
        updated_at=template.updated_at,
        sections=section_responses,
    )


# ============================================================
# APPLICANT DOCUMENT ENDPOINTS
# ============================================================

@router.get(
    "/sop/my-documents",
    response_model=List[ApplicantDocumentResponseSchema],
)
async def get_my_documents(
    document_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all documents (SOPs and LOEs) for the current user.
    Optional filter by document_type.
    """

    documents = await SOPService.get_user_documents(
        db,
        str(current_user.id),
        document_type,
    )

    return documents


@router.post(
    "/sop/my-documents",
    response_model=ApplicantDocumentResponseSchema,
    status_code=201,
)
async def create_document(
    data: ApplicantDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new applicant document (SOP or LOE).
    """

    document = await SOPService.create_applicant_document(
        db,
        str(current_user.id),
        data.model_dump(),
    )

    await db.commit()

    return document


@router.get(
    "/sop/my-documents/{document_id}",
    response_model=ApplicantDocumentDetailResponse,
)
async def get_document_detail(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get document details with all responses and drafts.
    """

    document = await SOPService.get_applicant_document(
        db,
        document_id,
        str(current_user.id),
    )

    responses = await SOPService.get_document_responses(
        db,
        document_id,
        str(current_user.id),
    )

    drafts = await SOPService.get_current_drafts(
        db,
        document_id,
        str(current_user.id),
    )

    # --------------------------------------------------------
    # Build draft responses safely
    # --------------------------------------------------------

    draft_responses = []

    for draft in drafts:
        section = await SOPService.get_section(
            db,
            str(draft.section_id),
        )

        # generation_status may be an enum or a string,
        # depending on how the model is configured.
        generation_status = draft.generation_status

        if generation_status is not None and hasattr(
            generation_status,
            "value",
        ):
            generation_status = generation_status.value

        draft_responses.append(
            ApplicantDraftResponse(
                id=str(draft.id),
                section_id=str(draft.section_id),
                section_name=section.name,
                content=draft.content,
                ai_provider=draft.ai_provider,
                ai_model=draft.ai_model,
                version=draft.version,
                is_current=draft.is_current,
                generation_status=generation_status,
                missing_information=draft.missing_information,
                warnings=draft.warnings,
                knowledge_sources=draft.knowledge_sources,
                source_draft_id=(
                    str(draft.source_draft_id)
                    if draft.source_draft_id
                    else None
                ),
                created_at=draft.created_at,
            )
        )

    # --------------------------------------------------------
    # Build answer responses
    # --------------------------------------------------------

    answer_responses = []

    for r in responses:
        answer_responses.append(
            ApplicantAnswerResponse(
                id=str(r["id"]) if r["id"] else "",
                question_id=str(r["question_id"]),
                question_text=r["question_text"],
                answer_text=r["answer_text"],
                is_required=r["is_required"],
                is_answered=r["is_answered"],
            )
        )

    # --------------------------------------------------------
    # Return complete document
    # --------------------------------------------------------

    return ApplicantDocumentDetailResponse(
        id=str(document.id),
        user_id=str(document.user_id),
        pathway_id=str(document.pathway_id),
        template_id=str(document.template_id),
        document_type=document.document_type.value,
        status=document.status.value,
        version=document.version,
        current_section_order=document.current_section_order,
        title=document.title,
        reason=document.reason,
        created_at=document.created_at,
        updated_at=document.updated_at,
        responses=answer_responses,
        drafts=draft_responses,
    )


# ============================================================
# RESPONSE ENDPOINTS
# ============================================================

@router.get(
    "/sop/my-documents/{document_id}/responses",
    response_model=List[ApplicantAnswerResponse],
)
async def get_document_responses(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all responses for a document.
    """

    responses = await SOPService.get_document_responses(
        db,
        document_id,
        str(current_user.id),
    )

    return [
        ApplicantAnswerResponse(
            id=str(r["id"]) if r["id"] else "",
            question_id=str(r["question_id"]),
            question_text=r["question_text"],
            answer_text=r["answer_text"],
            is_required=r["is_required"],
            is_answered=r["is_answered"],
        )
        for r in responses
    ]


@router.post(
    "/sop/my-documents/{document_id}/responses",
    response_model=List[ApplicantAnswerResponse],
    status_code=201,
)
async def save_responses(
    document_id: str,
    data: ApplicantAnswersBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Save multiple responses at once.
    """

    answers = [
        a.model_dump()
        for a in data.answers
    ]

    responses = await SOPService.save_batch_responses(
        db,
        document_id,
        answers,
        str(current_user.id),
    )

    result = []

    for response in responses:
        question = await SOPService.get_question(
            db,
            str(response.question_id),
        )

        result.append(
            ApplicantAnswerResponse(
                id=str(response.id),
                question_id=str(response.question_id),
                question_text=question.question_text,
                answer_text=response.answer_text,
                is_required=question.is_required,
                is_answered=bool(response.answer_text),
            )
        )

    await db.commit()    

    return result


@router.put(
    "/sop/my-documents/{document_id}/responses/{question_id}",
    response_model=ApplicantAnswerResponse,
)
async def update_response(
    document_id: str,
    question_id: str,
    data: ApplicantAnswerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a single response.
    """

    response = await SOPService.save_response(
        db,
        document_id,
        question_id,
        data.answer_text,
        str(current_user.id),
    )

    question = await SOPService.get_question(
        db,
        question_id,
    )

    await db.commit()

    return ApplicantAnswerResponse(
        id=str(response.id),
        question_id=str(response.question_id),
        question_text=question.question_text,
        answer_text=response.answer_text,
        is_required=question.is_required,
        is_answered=bool(response.answer_text),
    )


# ============================================================
# PROGRESS ENDPOINT
# ============================================================

@router.get(
    "/sop/my-documents/{document_id}/progress",
    response_model=ApplicantDocumentProgressResponse,
)
async def get_document_progress(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get progress summary for a document.
    """

    progress = await SOPService.get_document_progress(
        db,
        document_id,
        str(current_user.id),
    )

    return progress


# ============================================================
# DRAFT ENDPOINTS
# ============================================================

@router.get(
    "/sop/my-documents/{document_id}/drafts",
    response_model=List[ApplicantDraftResponse],
)
async def get_document_drafts(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all current drafts for a document.
    """

    drafts = await SOPService.get_current_drafts(
        db,
        document_id,
        str(current_user.id),
    )

    result = []

    for draft in drafts:
        section = await SOPService.get_section(
            db,
            str(draft.section_id),
        )

        generation_status = draft.generation_status

        if generation_status is not None and hasattr(
            generation_status,
            "value",
        ):
            generation_status = generation_status.value

        result.append(
            ApplicantDraftResponse(
                id=str(draft.id),
                section_id=str(draft.section_id),
                section_name=section.name,
                content=draft.content,
                ai_provider=draft.ai_provider,
                ai_model=draft.ai_model,
                version=draft.version,
                is_current=draft.is_current,
                generation_status=generation_status,
                missing_information=draft.missing_information,
                warnings=draft.warnings,
                knowledge_sources=draft.knowledge_sources,
                source_draft_id=(
                    str(draft.source_draft_id)
                    if draft.source_draft_id
                    else None
                ),
                created_at=draft.created_at,
            )
        )

    return result


# ============================================================
# RELATIONSHIP ENDPOINTS
# ============================================================

@router.post(
    "/sop/my-documents/{document_id}/relationships",
    response_model=DocumentRelationshipResponse,
    status_code=201,
)
async def create_relationship(
    document_id: str,
    data: DocumentRelationshipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Link a related document (e.g., LOE to SOP).
    """

    relationship = await SOPService.create_relationship(
        db,
        document_id,
        data.related_document_id,
        data.relationship_type,
        str(current_user.id),
    )

    await db.commit()

    return relationship


@router.get(
    "/sop/my-documents/{document_id}/relationships",
    response_model=List[DocumentRelationshipResponse],
)
async def get_relationships(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all relationships for a document.
    """

    relationships = await SOPService.get_document_relationships(
        db,
        document_id,
        str(current_user.id),
    )

    return relationships


# ============================================================
# SPRINT 6 — AI GENERATION ENDPOINTS
# ============================================================

@router.post(
    "/sop/my-documents/{document_id}/generate",
    response_model=GenerateDraftResponse,
)
async def generate_draft(
    document_id: str,
    data: GenerateDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate an AI draft for a specific section.
    """

    generation_service = AIGenerationService()

    result = await generation_service.generate_section_draft(
        db=db,
        document_id=document_id,
        section_id=data.section_id,
        user_id=str(current_user.id),
    )

    await db.commit()

    return GenerateDraftResponse(
        status=result["status"],
        content=result.get("content"),
        missing_information=result.get(
            "missing_information"
        ),
        warnings=result.get("warnings"),
        knowledge_sources=result.get(
            "knowledge_sources"
        ),
        provider=result.get("provider"),
        model=result.get("model"),
        draft_id=result.get("draft_id"),
        draft_version=result.get(
            "draft_version"
        ),
    )


@router.post(
    "/sop/my-documents/{document_id}/regenerate",
    response_model=GenerateDraftResponse,
)
async def regenerate_draft(
    document_id: str,
    data: RegenerateDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Regenerate a section draft with an optional
    improvement instruction.
    """

    generation_service = AIGenerationService()

    result = await generation_service.regenerate_section_draft(
        db=db,
        document_id=document_id,
        section_id=data.section_id,
        user_id=str(current_user.id),
        instruction=data.instruction,
    )

    await db.commit()

    return GenerateDraftResponse(
        status=result["status"],
        content=result.get("content"),
        missing_information=result.get(
            "missing_information"
        ),
        warnings=result.get("warnings"),
        knowledge_sources=result.get(
            "knowledge_sources"
        ),
        provider=result.get("provider"),
        model=result.get("model"),
        draft_id=result.get("draft_id"),
        draft_version=result.get(
            "draft_version"
        ),
    )


@router.post(
    "/sop/my-documents/{document_id}/finalize",
    response_model=FinalizeDraftResponse,
)
async def finalize_draft(
    document_id: str,
    data: FinalizeDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Finalize a draft.
    """

    generation_service = AIGenerationService()

    result = await generation_service.finalize_draft(
        db=db,
        document_id=document_id,
        draft_id=data.draft_id,
        user_id=str(current_user.id),
    )

    await db.commit()

    return FinalizeDraftResponse(
        status=result["status"],
        document_status=result["document_status"],
        message=result["message"],
    )