# app/api/v1/admin_sop.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.api.deps import get_db, get_admin_user
from app.models.user import User
from app.services.sop import SOPService
from app.services.audit import AuditService
from app.schemas.sop import (
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
    DocumentTemplateResponse,
    DocumentTemplateDetailResponse,
    DocumentTemplateSectionCreate,
    DocumentTemplateSectionUpdate,
    DocumentTemplateSectionResponse,
    DocumentTemplateSectionDetailResponse,
    DocumentTemplateQuestionCreate,
    DocumentTemplateQuestionUpdate,
    DocumentTemplateQuestionResponse
)

router = APIRouter()

# ========== Document Template Endpoints ==========

@router.get("/sop/templates", response_model=List[DocumentTemplateResponse])
async def list_templates(
    pathway_id: Optional[str] = None,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List all document templates with filters"""
    templates = await SOPService.get_all_templates(
        db, pathway_id=pathway_id, document_type=document_type,
        status=status, include_inactive=include_inactive
    )
    
    result = []
    for template in templates:
        sections = await SOPService.get_template_sections(db, str(template.id))
        template.sections_count = len(sections)
        result.append(template)
    
    return result

@router.get("/sop/templates/{template_id}", response_model=DocumentTemplateDetailResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Get template with all sections and questions"""
    template = await SOPService.get_template(db, template_id)
    sections = await SOPService.get_template_sections(db, template_id)
    
    section_responses = []
    for section in sections:
        questions = await SOPService.get_section_questions(db, str(section.id))
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
                questions=[DocumentTemplateQuestionResponse(
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
                    order_index=q.order_index
                ) for q in questions]
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
        sections=section_responses
    )

@router.post("/sop/templates", response_model=DocumentTemplateResponse, status_code=201)
async def create_template(
    data: DocumentTemplateCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Create new document template"""
    template = await SOPService.create_template(db, data.model_dump(), str(admin.id))
    
    await AuditService.log_action(
        db, str(admin.id), "create", "document_template",
        str(template.id), {"name": template.name, "type": template.document_type.value}
    )
    
    return template

@router.put("/sop/templates/{template_id}", response_model=DocumentTemplateResponse)
async def update_template(
    template_id: str,
    data: DocumentTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update document template"""
    template = await SOPService.update_template(
        db, template_id, data.model_dump(exclude_none=True), str(admin.id)
    )
    return template

@router.put("/sop/templates/{template_id}/status")
async def change_template_status(
    template_id: str,
    status: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Change template status (draft, published, archived)"""
    template = await SOPService.change_template_status(
        db, template_id, status, str(admin.id)
    )
    
    await AuditService.log_action(
        db, str(admin.id), status, "document_template",
        str(template_id), {"name": template.name}
    )
    
    return {"id": str(template.id), "status": template.status.value, "version": template.version}

@router.delete("/sop/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Soft delete document template"""
    await SOPService.delete_template(db, template_id, str(admin.id))

# ========== Section Endpoints ==========

@router.post("/sop/templates/{template_id}/sections", response_model=DocumentTemplateSectionResponse, status_code=201)
async def create_section(
    template_id: str,
    data: DocumentTemplateSectionCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Add section to template"""
    section = await SOPService.create_section(
        db, template_id, data.model_dump(), str(admin.id)
    )
    
    await AuditService.log_action(
        db, str(admin.id), "create", "document_template_section",
        str(section.id), {"name": section.name, "template_id": template_id}
    )
    
    return section

@router.put("/sop/sections/{section_id}", response_model=DocumentTemplateSectionResponse)
async def update_section(
    section_id: str,
    data: DocumentTemplateSectionUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update section"""
    section = await SOPService.update_section(
        db, section_id, data.model_dump(exclude_none=True), str(admin.id)
    )
    return section

@router.delete("/sop/sections/{section_id}", status_code=204)
async def delete_section(
    section_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Soft delete section"""
    await SOPService.delete_section(db, section_id, str(admin.id))

# ========== Question Endpoints ==========

@router.post("/sop/sections/{section_id}/questions", response_model=DocumentTemplateQuestionResponse, status_code=201)
async def create_question(
    section_id: str,
    data: DocumentTemplateQuestionCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Add question to section"""
    question = await SOPService.create_question(
        db, section_id, data.model_dump(), str(admin.id)
    )
    
    await AuditService.log_action(
        db, str(admin.id), "create", "document_template_question",
        str(question.id), {"question": question.question_text[:100]}
    )
    
    return question

@router.put("/sop/questions/{question_id}", response_model=DocumentTemplateQuestionResponse)
async def update_question(
    question_id: str,
    data: DocumentTemplateQuestionUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update question"""
    question = await SOPService.update_question(
        db, question_id, data.model_dump(exclude_none=True), str(admin.id)
    )
    return question

@router.delete("/sop/questions/{question_id}", status_code=204)
async def delete_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Soft delete question"""
    await SOPService.delete_question(db, question_id, str(admin.id))