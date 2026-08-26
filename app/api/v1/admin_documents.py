# app/api/v1/admin_documents.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_db, get_admin_user
from app.models.user import User
from app.services.document import DocumentService
from app.services.audit import AuditService
from app.core.exceptions import BadRequestException
from app.schemas.document import (
    DocumentCategoryCreate,
    DocumentCategoryUpdate,
    DocumentCategoryResponse,
    DocumentTypeCreate,
    DocumentTypeUpdate,
    DocumentTypeResponse,
    PathwayDocumentRequirementCreate,
    PathwayDocumentRequirementUpdate,
    PathwayDocumentRequirementResponse,
)

router = APIRouter()


# ============================================================
# Document Categories
# ============================================================

@router.get(
    "/document-categories",
    response_model=List[DocumentCategoryResponse],
)
async def list_categories(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """List all document categories."""

    categories = await DocumentService.get_all_categories(
        db,
        include_inactive,
    )

    return [
        DocumentCategoryResponse(
            id=str(category.id),
            name=category.name,
            slug=category.slug,
            description=category.description,
            sort_order=category.sort_order,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )
        for category in categories
    ]


@router.post(
    "/document-categories",
    response_model=DocumentCategoryResponse,
    status_code=201,
)
async def create_category(
    data: DocumentCategoryCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Create new document category."""

    category = await DocumentService.create_category(
        db,
        data.model_dump(),
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "create",
        "document_category",
        str(category.id),
        {
            "name": category.name,
            "slug": category.slug,
        },
    )

    return DocumentCategoryResponse(
        id=str(category.id),
        name=category.name,
        slug=category.slug,
        description=category.description,
        sort_order=category.sort_order,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.put(
    "/document-categories/{category_id}",
    response_model=DocumentCategoryResponse,
)
async def update_category(
    category_id: str,
    data: DocumentCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update document category."""

    category = await DocumentService.update_category(
        db,
        category_id,
        data.model_dump(exclude_none=True),
        str(admin.id),
    )

    return DocumentCategoryResponse(
        id=str(category.id),
        name=category.name,
        slug=category.slug,
        description=category.description,
        sort_order=category.sort_order,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.delete(
    "/document-categories/{category_id}",
    status_code=204,
)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Soft delete document category."""

    await DocumentService.delete_category(
        db,
        category_id,
        str(admin.id),
    )


# ============================================================
# Document Types
# ============================================================

@router.get(
    "/document-types",
    response_model=List[DocumentTypeResponse],
)
async def list_document_types(
    category_id: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """List all document types with optional category filter."""

    types = await DocumentService.get_all_document_types(
        db,
        category_id,
        include_inactive,
    )

    result = []

    for document_type in types:
        category = await DocumentService.get_category(
            db,
            str(document_type.category_id),
        )

        result.append(
            DocumentTypeResponse(
                id=str(document_type.id),
                category_id=str(document_type.category_id),
                category_name=category.name,
                name=document_type.name,
                slug=document_type.slug,
                description=document_type.description,
                is_active=document_type.is_active,
                created_at=document_type.created_at,
                updated_at=document_type.updated_at,
            )
        )

    return result


@router.post(
    "/document-types",
    response_model=DocumentTypeResponse,
    status_code=201,
)
async def create_document_type(
    data: DocumentTypeCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Create new document type."""

    document_type = await DocumentService.create_document_type(
        db,
        data.model_dump(),
        str(admin.id),
    )

    category = await DocumentService.get_category(
        db,
        str(document_type.category_id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "create",
        "document_type",
        str(document_type.id),
        {
            "name": document_type.name,
            "slug": document_type.slug,
        },
    )

    return DocumentTypeResponse(
        id=str(document_type.id),
        category_id=str(document_type.category_id),
        category_name=category.name,
        name=document_type.name,
        slug=document_type.slug,
        description=document_type.description,
        is_active=document_type.is_active,
        created_at=document_type.created_at,
        updated_at=document_type.updated_at,
    )


@router.put(
    "/document-types/{document_type_id}",
    response_model=DocumentTypeResponse,
)
async def update_document_type(
    document_type_id: str,
    data: DocumentTypeUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update document type."""

    document_type = await DocumentService.update_document_type(
        db,
        document_type_id,
        data.model_dump(exclude_none=True),
        str(admin.id),
    )

    category = await DocumentService.get_category(
        db,
        str(document_type.category_id),
    )

    return DocumentTypeResponse(
        id=str(document_type.id),
        category_id=str(document_type.category_id),
        category_name=category.name,
        name=document_type.name,
        slug=document_type.slug,
        description=document_type.description,
        is_active=document_type.is_active,
        created_at=document_type.created_at,
        updated_at=document_type.updated_at,
    )


@router.delete(
    "/document-types/{document_type_id}",
    status_code=204,
)
async def delete_document_type(
    document_type_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Soft delete document type."""

    await DocumentService.delete_document_type(
        db,
        document_type_id,
        str(admin.id),
    )


# ============================================================
# Pathway Document Requirements
# ============================================================

@router.get(
    "/pathways/{pathway_id}/requirements",
    response_model=List[PathwayDocumentRequirementResponse],
)
async def list_pathway_requirements(
    pathway_id: str,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """List all document requirements for a pathway."""

    requirements = await DocumentService.get_pathway_requirements(
        db,
        pathway_id,
        include_inactive,
    )

    result = []

    for requirement in requirements:
        document_type = await DocumentService.get_document_type(
            db,
            str(requirement.document_type_id),
        )

        category = await DocumentService.get_category(
            db,
            str(document_type.category_id),
        )

        result.append(
            PathwayDocumentRequirementResponse(
                id=str(requirement.id),
                pathway_id=str(requirement.pathway_id),
                document_type_id=str(requirement.document_type_id),
                document_name=document_type.name,
                category_name=category.name,
                is_required=requirement.is_required,
                is_active=requirement.is_active,
                instructions=requirement.instructions,
                display_order=requirement.display_order,
                created_at=requirement.created_at,
                updated_at=requirement.updated_at,
            )
        )

    return result


@router.post(
    "/pathways/{pathway_id}/requirements",
    response_model=PathwayDocumentRequirementResponse,
    status_code=201,
)
async def add_pathway_requirement(
    pathway_id: str,
    data: PathwayDocumentRequirementCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Add document requirement to pathway."""

    data_dict = data.model_dump()

    # Always use the pathway from the URL.
    data_dict["pathway_id"] = pathway_id

    requirement = await DocumentService.add_requirement(
        db,
        data_dict,
        str(admin.id),
    )

    document_type = await DocumentService.get_document_type(
        db,
        str(requirement.document_type_id),
    )

    category = await DocumentService.get_category(
        db,
        str(document_type.category_id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "create",
        "pathway_document_requirement",
        str(requirement.id),
        {
            "pathway_id": pathway_id,
            "document_type": document_type.name,
        },
    )

    return PathwayDocumentRequirementResponse(
        id=str(requirement.id),
        pathway_id=str(requirement.pathway_id),
        document_type_id=str(requirement.document_type_id),
        document_name=document_type.name,
        category_name=category.name,
        is_required=requirement.is_required,
        is_active=requirement.is_active,
        instructions=requirement.instructions,
        display_order=requirement.display_order,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
    )


@router.put(
    "/pathways/{pathway_id}/requirements/{requirement_id}",
    response_model=PathwayDocumentRequirementResponse,
)
async def update_pathway_requirement(
    pathway_id: str,
    requirement_id: str,
    data: PathwayDocumentRequirementUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update pathway document requirement."""

    requirement = await DocumentService.get_requirement(
        db,
        requirement_id,
    )

    if str(requirement.pathway_id) != str(pathway_id):
        raise BadRequestException(
            "Document requirement does not belong to this pathway"
        )

    requirement = await DocumentService.update_requirement(
        db,
        requirement_id,
        data.model_dump(exclude_none=True),
        str(admin.id),
    )

    document_type = await DocumentService.get_document_type(
        db,
        str(requirement.document_type_id),
    )

    category = await DocumentService.get_category(
        db,
        str(document_type.category_id),
    )

    return PathwayDocumentRequirementResponse(
        id=str(requirement.id),
        pathway_id=str(requirement.pathway_id),
        document_type_id=str(requirement.document_type_id),
        document_name=document_type.name,
        category_name=category.name,
        is_required=requirement.is_required,
        is_active=requirement.is_active,
        instructions=requirement.instructions,
        display_order=requirement.display_order,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
    )


@router.delete(
    "/pathways/{pathway_id}/requirements/{requirement_id}",
    status_code=204,
)
async def delete_pathway_requirement(
    pathway_id: str,
    requirement_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Soft delete pathway document requirement."""

    requirement = await DocumentService.get_requirement(
        db,
        requirement_id,
    )

    if str(requirement.pathway_id) != str(pathway_id):
        raise BadRequestException(
            "Document requirement does not belong to this pathway"
        )

    await DocumentService.delete_requirement(
        db,
        requirement_id,
        str(admin.id),
    )