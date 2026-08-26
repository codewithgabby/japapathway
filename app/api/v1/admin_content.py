# app/api/v1/admin_content.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_db, get_admin_user
from app.models.user import User
from app.services.content import ContentService
from app.services.pathway import PathwayService
from app.services.audit import AuditService
from app.schemas.content import (
    ContentCategoryCreate,
    ContentCategoryUpdate,
    ContentCategoryResponse,
    ContentArticleCreate,
    ContentArticleUpdate,
    ContentArticleResponse,
    ContentVersionResponse,
    ContentStatusUpdate,
)


router = APIRouter()


# ============================================================
# CONTENT CATEGORY ENDPOINTS
# ============================================================

@router.get(
    "/content/categories",
    response_model=List[ContentCategoryResponse],
)
async def list_categories(
    status: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    List content categories.

    Workspace/admin endpoint.
    """
    categories = await ContentService.get_all_categories(
        db,
        status=status,
        include_inactive=include_inactive,
    )

    result = []

    for category in categories:
        articles = await ContentService.get_all_articles(
            db,
            category_id=str(category.id),
            limit=100,
        )

        category.articles_count = len(articles)
        result.append(category)

    return result


@router.post(
    "/content/categories",
    response_model=ContentCategoryResponse,
    status_code=201,
)
async def create_category(
    data: ContentCategoryCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Create a new content category.
    """
    category = await ContentService.create_category(
        db,
        data.model_dump(),
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "create",
        "content_category",
        str(category.id),
        {
            "name": category.name,
            "slug": category.slug,
        },
    )

    return category


@router.put(
    "/content/categories/{category_id}",
    response_model=ContentCategoryResponse,
)
async def update_category(
    category_id: str,
    data: ContentCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Update a content category.
    """
    category = await ContentService.update_category(
        db,
        category_id,
        data.model_dump(exclude_none=True),
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "update",
        "content_category",
        str(category_id),
        {
            "name": category.name,
            "slug": category.slug,
        },
    )

    return category


@router.put(
    "/content/categories/{category_id}/status",
)
async def change_category_status(
    category_id: str,
    data: ContentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Change category status.

    Supported statuses:
    draft
    published
    archived
    """
    category = await ContentService.change_category_status(
        db,
        category_id,
        data.status,
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        data.status,
        "content_category",
        str(category_id),
        {
            "name": category.name,
        },
    )

    return {
        "id": str(category.id),
        "status": category.status.value,
        "version": category.version,
    }


@router.delete(
    "/content/categories/{category_id}",
    status_code=204,
)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Soft delete a content category.
    """
    await ContentService.delete_category(
        db,
        category_id,
        str(admin.id),
    )


# ============================================================
# CONTENT ARTICLE ENDPOINTS
# ============================================================

@router.get(
    "/content/articles",
    response_model=List[ContentArticleResponse],
)
async def list_articles(
    pathway_id: Optional[str] = None,
    category_id: Optional[str] = None,
    status: Optional[str] = None,
    include_inactive: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    List content articles with optional filters.
    """
    articles = await ContentService.get_all_articles(
        db,
        pathway_id=pathway_id,
        category_id=category_id,
        status=status,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
    )

    result = []

    for article in articles:
        category = await ContentService.get_category(
            db,
            str(article.category_id),
        )

        pathway = await PathwayService.get_pathway_by_id(
            db,
            str(article.pathway_id),
        )

        article.category_name = category.name
        article.pathway_name = pathway.name

        result.append(article)

    return result


@router.post(
    "/content/articles",
    response_model=ContentArticleResponse,
    status_code=201,
)
async def create_article(
    data: ContentArticleCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Create a new content article.
    """
    article = await ContentService.create_article(
        db,
        data.model_dump(),
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "create",
        "content_article",
        str(article.id),
        {
            "title": article.title,
            "slug": article.slug,
        },
    )

    return article


@router.put(
    "/content/articles/{article_id}",
    response_model=ContentArticleResponse,
)
async def update_article(
    article_id: str,
    data: ContentArticleUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Update a content article.
    """
    article = await ContentService.update_article(
        db,
        article_id,
        data.model_dump(exclude_none=True),
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        "update",
        "content_article",
        str(article_id),
        {
            "title": article.title,
        },
    )

    return article


@router.put(
    "/content/articles/{article_id}/status",
)
async def change_article_status(
    article_id: str,
    data: ContentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Change article status.

    Supported statuses:
    draft
    published
    archived
    """
    article = await ContentService.change_article_status(
        db,
        article_id,
        data.status,
        str(admin.id),
    )

    await AuditService.log_action(
        db,
        str(admin.id),
        data.status,
        "content_article",
        str(article_id),
        {
            "title": article.title,
        },
    )

    return {
        "id": str(article.id),
        "status": article.status.value,
        "version": article.version,
    }


@router.delete(
    "/content/articles/{article_id}",
    status_code=204,
)
async def delete_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Soft delete a content article.
    """
    await ContentService.delete_article(
        db,
        article_id,
        str(admin.id),
    )


# ============================================================
# VERSION ENDPOINTS
# ============================================================

@router.get(
    "/content/articles/{article_id}/versions",
    response_model=List[ContentVersionResponse],
)
async def get_article_versions(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Get all versions of an article.
    """
    versions = await ContentService.get_article_versions(
        db,
        article_id,
    )

    return versions


@router.get(
    "/content/articles/{article_id}/versions/published",
    response_model=ContentVersionResponse,
)
async def get_published_version(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Get the currently published version of an article.
    """
    version = await ContentService.get_published_version(
        db,
        article_id,
    )

    return version