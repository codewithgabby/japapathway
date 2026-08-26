# app/api/v1/content.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_db
from app.services.content import ContentService
from app.services.pathway import PathwayService
from app.schemas.content import (
    ContentArticleResponse,
    ContentCategoryResponse,
)


router = APIRouter()


@router.get(
    "/categories",
    response_model=List[ContentCategoryResponse],
)
async def list_published_categories(
    db: AsyncSession = Depends(get_db),
):
    """
    List published content categories.

    Public endpoint.
    Only published and active categories are returned.
    """
    categories = await ContentService.get_all_categories(
        db,
        status="published",
        include_inactive=False,
    )

    result = []

    for category in categories:
        articles = await ContentService.get_published_articles_by_category(
            db,
            str(category.id),
        )

        category.articles_count = len(articles)
        result.append(category)

    return result


@router.get(
    "/articles",
    response_model=List[ContentArticleResponse],
)
async def list_published_articles(
    pathway_id: Optional[str] = None,
    category_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List published content articles.

    Public endpoint.
    Only published and active articles are returned.
    """
    articles = await ContentService.get_all_articles(
        db,
        pathway_id=pathway_id,
        category_id=category_id,
        status="published",
        include_inactive=False,
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


@router.get(
    "/articles/{slug}",
    response_model=ContentArticleResponse,
)
async def get_published_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a published content article by slug.

    Public endpoint.
    Only published and active articles are returned.
    """
    article = await ContentService.get_published_article_by_slug(
        db,
        slug,
    )

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

    return article


@router.get(
    "/pathways/{pathway_id}/articles",
    response_model=List[ContentArticleResponse],
)
async def get_published_articles_by_pathway(
    pathway_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all published articles for a specific pathway.

    Public endpoint.
    Only published and active articles are returned.

    This endpoint can later be used by AI services
    for context assembly.
    """
    articles = await ContentService.get_published_articles_by_pathway(
        db,
        pathway_id,
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