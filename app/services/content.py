from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import (
    ContentCategory,
    ContentArticle,
    ContentVersion,
    ContentStatus,
)
from app.services.pathway import PathwayService
from app.core.exceptions import NotFoundException, BadRequestException


class ContentService:

    # ============================================================
    # CONTENT CATEGORY
    # ============================================================

    @staticmethod
    async def create_category(
        db: AsyncSession,
        data: dict,
        user_id: str,
    ) -> ContentCategory:

        result = await db.execute(
            select(ContentCategory).where(
                ContentCategory.slug == data["slug"],
                ContentCategory.is_deleted.is_(False),
            )
        )

        if result.scalar_one_or_none():
            raise BadRequestException(
                "Content category with this slug already exists"
            )

        category = ContentCategory(
            **data,
            created_by=user_id,
            updated_by=user_id,
        )

        db.add(category)
        await db.flush()
        await db.commit()
        await db.refresh(category)

        return category

    @staticmethod
    async def get_category(
        db: AsyncSession,
        category_id: str,
    ) -> ContentCategory:

        result = await db.execute(
            select(ContentCategory).where(
                ContentCategory.id == category_id,
                ContentCategory.is_deleted.is_(False),
            )
        )

        category = result.scalar_one_or_none()

        if not category:
            raise NotFoundException("Content category")

        return category

    @staticmethod
    async def get_category_by_slug(
        db: AsyncSession,
        slug: str,
    ) -> ContentCategory:

        result = await db.execute(
            select(ContentCategory).where(
                ContentCategory.slug == slug,
                ContentCategory.is_deleted.is_(False),
            )
        )

        category = result.scalar_one_or_none()

        if not category:
            raise NotFoundException("Content category")

        return category

    @staticmethod
    async def get_all_categories(
        db: AsyncSession,
        status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[ContentCategory]:

        query = select(ContentCategory).where(
            ContentCategory.is_deleted.is_(False)
        )

        if status:
            try:
                content_status = ContentStatus(status)
            except ValueError:
                raise BadRequestException(
                    "Invalid content status"
                )

            query = query.where(
                ContentCategory.status == content_status
            )

        if not include_inactive:
            query = query.where(
                ContentCategory.is_active.is_(True)
            )

        query = query.order_by(ContentCategory.name)

        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def update_category(
        db: AsyncSession,
        category_id: str,
        data: dict,
        user_id: str,
    ) -> ContentCategory:

        category = await ContentService.get_category(
            db,
            category_id,
        )

        if "slug" in data and data["slug"] != category.slug:

            result = await db.execute(
                select(ContentCategory).where(
                    ContentCategory.slug == data["slug"],
                    ContentCategory.id != category_id,
                    ContentCategory.is_deleted.is_(False),
                )
            )

            if result.scalar_one_or_none():
                raise BadRequestException(
                    "Content category with this slug already exists"
                )

        for key, value in data.items():
            setattr(category, key, value)

        category.updated_by = user_id

        await db.flush()

        return category

    @staticmethod
    async def change_category_status(
        db: AsyncSession,
        category_id: str,
        status: str,
        user_id: str,
    ) -> ContentCategory:

        category = await ContentService.get_category(
            db,
            category_id,
        )

        try:
            new_status = ContentStatus(status)
        except ValueError:
            raise BadRequestException(
                "Invalid content status. Use draft, published, or archived."
            )

        category.status = new_status
        category.updated_by = user_id

        if new_status == ContentStatus.PUBLISHED:
            category.version += 1

        await db.flush()

        return category

    @staticmethod
    async def delete_category(
        db: AsyncSession,
        category_id: str,
        user_id: str,
    ) -> None:

        category = await ContentService.get_category(
            db,
            category_id,
        )

        category.soft_delete(user_id)

        await db.flush()

    # ============================================================
    # CONTENT ARTICLE
    # ============================================================

    @staticmethod
    async def create_article(
        db: AsyncSession,
        data: dict,
        user_id: str,
    ) -> ContentArticle:

        # Validate category
        await ContentService.get_category(
            db,
            data["category_id"],
        )

        # Validate pathway
        await PathwayService.get_pathway_by_id(
            db,
            data["pathway_id"],
        )

        # Check slug uniqueness
        result = await db.execute(
            select(ContentArticle).where(
                ContentArticle.slug == data["slug"],
                ContentArticle.is_deleted.is_(False),
            )
        )

        if result.scalar_one_or_none():
            raise BadRequestException(
                "Content article with this slug already exists"
            )

        article = ContentArticle(
            **data,
            created_by=user_id,
            updated_by=user_id,
        )

        db.add(article)

        await db.flush()

        # Create initial version
        initial_version = ContentVersion(
            article_id=article.id,
            version=1,
            title=article.title,
            summary=article.summary,
            content=article.content,
            status=ContentStatus.DRAFT,
            created_by=user_id,
        )

        db.add(initial_version)

        await db.flush()
        await db.commit()
        await db.refresh(article)
        return article

    @staticmethod
    async def get_article(
        db: AsyncSession,
        article_id: str,
    ) -> ContentArticle:

        result = await db.execute(
            select(ContentArticle).where(
                ContentArticle.id == article_id,
                ContentArticle.is_deleted.is_(False),
            )
        )

        article = result.scalar_one_or_none()

        if not article:
            raise NotFoundException("Content article")

        return article

    @staticmethod
    async def get_article_by_slug(
        db: AsyncSession,
        slug: str,
    ) -> ContentArticle:

        result = await db.execute(
            select(ContentArticle).where(
                ContentArticle.slug == slug,
                ContentArticle.is_deleted.is_(False),
            )
        )

        article = result.scalar_one_or_none()

        if not article:
            raise NotFoundException("Content article")

        return article

    @staticmethod
    async def get_all_articles(
        db: AsyncSession,
        pathway_id: Optional[str] = None,
        category_id: Optional[str] = None,
        status: Optional[str] = None,
        include_inactive: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ContentArticle]:

        if limit < 1 or limit > 100:
            raise BadRequestException(
                "Limit must be between 1 and 100"
            )

        if offset < 0:
            raise BadRequestException(
                "Offset cannot be negative"
            )

        query = select(ContentArticle).where(
            ContentArticle.is_deleted.is_(False)
        )

        if pathway_id:
            query = query.where(
                ContentArticle.pathway_id == pathway_id
            )

        if category_id:
            query = query.where(
                ContentArticle.category_id == category_id
            )

        if status:
            try:
                content_status = ContentStatus(status)
            except ValueError:
                raise BadRequestException(
                    "Invalid content status"
                )

            query = query.where(
                ContentArticle.status == content_status
            )

        if not include_inactive:
            query = query.where(
                ContentArticle.is_active.is_(True)
            )

        query = (
            query
            .order_by(ContentArticle.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def update_article(
        db: AsyncSession,
        article_id: str,
        data: dict,
        user_id: str,
    ) -> ContentArticle:

        article = await ContentService.get_article(
            db,
            article_id,
        )

        # Validate slug if changed
        if "slug" in data and data["slug"] != article.slug:

            result = await db.execute(
                select(ContentArticle).where(
                    ContentArticle.slug == data["slug"],
                    ContentArticle.id != article_id,
                    ContentArticle.is_deleted.is_(False),
                )
            )

            if result.scalar_one_or_none():
                raise BadRequestException(
                    "Content article with this slug already exists"
                )

        # Update article
        for key, value in data.items():
            setattr(article, key, value)

        article.updated_by = user_id

        await db.flush()

        # --------------------------------------------------------
        # IMPORTANT:
        # Every meaningful edit creates a new draft version.
        # This preserves the publishing history.
        # --------------------------------------------------------

        result = await db.execute(
            select(ContentVersion)
            .where(
                ContentVersion.article_id == article_id,
                ContentVersion.is_deleted.is_(False),
            )
            .order_by(ContentVersion.version.desc())
            .limit(1)
        )

        latest_version = result.scalar_one_or_none()

        next_version_number = (
            latest_version.version + 1
            if latest_version
            else 1
        )

        new_version = ContentVersion(
            article_id=article.id,
            version=next_version_number,
            title=article.title,
            summary=article.summary,
            content=article.content,
            status=ContentStatus.DRAFT,
            created_by=user_id,
        )

        db.add(new_version)

        # The article remains a draft until explicitly published.
        article.status = ContentStatus.DRAFT

        await db.flush()

        return article

    @staticmethod
    async def change_article_status(
        db: AsyncSession,
        article_id: str,
        status: str,
        user_id: str,
    ) -> ContentArticle:

        article = await ContentService.get_article(
            db,
            article_id,
        )

        try:
            new_status = ContentStatus(status)
        except ValueError:
            raise BadRequestException(
                "Invalid content status. Use draft, published, or archived."
            )

        # --------------------------------------------------------
        # Publishing
        # --------------------------------------------------------

        if new_status == ContentStatus.PUBLISHED:

            result = await db.execute(
                select(ContentVersion)
                .where(
                    ContentVersion.article_id == article_id,
                    ContentVersion.is_deleted.is_(False),
                )
                .order_by(ContentVersion.version.desc())
                .limit(1)
            )

            latest_version = result.scalar_one_or_none()

            if not latest_version:
                raise BadRequestException(
                    "Cannot publish an article without a content version"
                )

            # Archive previous published versions
            previous_versions_result = await db.execute(
                select(ContentVersion).where(
                    ContentVersion.article_id == article_id,
                    ContentVersion.status == ContentStatus.PUBLISHED,
                    ContentVersion.is_deleted.is_(False),
                )
            )

            previous_versions = previous_versions_result.scalars().all()

            for version in previous_versions:
                version.status = ContentStatus.ARCHIVED

            # Publish latest version
            latest_version.status = ContentStatus.PUBLISHED

            article.version = latest_version.version

        # --------------------------------------------------------
        # Archiving article
        # --------------------------------------------------------

        elif new_status == ContentStatus.ARCHIVED:

            result = await db.execute(
                select(ContentVersion).where(
                    ContentVersion.article_id == article_id,
                    ContentVersion.status == ContentStatus.PUBLISHED,
                    ContentVersion.is_deleted.is_(False),
                )
            )

            published_versions = result.scalars().all()

            for version in published_versions:
                version.status = ContentStatus.ARCHIVED

        # --------------------------------------------------------
        # Draft
        # --------------------------------------------------------

        elif new_status == ContentStatus.DRAFT:

            # Drafting an article does not destroy previous
            # published versions.
            pass

        article.status = new_status
        article.updated_by = user_id

        await db.flush()

        return article

    @staticmethod
    async def delete_article(
        db: AsyncSession,
        article_id: str,
        user_id: str,
    ) -> None:

        article = await ContentService.get_article(
            db,
            article_id,
        )

        article.soft_delete(user_id)

        await db.flush()

    # ============================================================
    # VERSION MANAGEMENT
    # ============================================================

    @staticmethod
    async def get_article_versions(
        db: AsyncSession,
        article_id: str,
    ) -> List[ContentVersion]:

        await ContentService.get_article(
            db,
            article_id,
        )

        result = await db.execute(
            select(ContentVersion)
            .where(
                ContentVersion.article_id == article_id,
                ContentVersion.is_deleted.is_(False),
            )
            .order_by(ContentVersion.version.desc())
        )

        return list(result.scalars().all())

    @staticmethod
    async def get_published_version(
        db: AsyncSession,
        article_id: str,
    ) -> ContentVersion:

        await ContentService.get_article(
            db,
            article_id,
        )

        result = await db.execute(
            select(ContentVersion)
            .where(
                ContentVersion.article_id == article_id,
                ContentVersion.status == ContentStatus.PUBLISHED,
                ContentVersion.is_deleted.is_(False),
            )
            .order_by(ContentVersion.version.desc())
            .limit(1)
        )

        version = result.scalar_one_or_none()

        if not version:
            raise NotFoundException(
                "Published content version"
            )

        return version

    # ============================================================
    # FUTURE AI CONSUMPTION
    # ============================================================

    @staticmethod
    async def get_published_articles_by_pathway(
        db: AsyncSession,
        pathway_id: str,
    ) -> List[ContentArticle]:

        result = await db.execute(
            select(ContentArticle).where(
                ContentArticle.pathway_id == pathway_id,
                ContentArticle.status == ContentStatus.PUBLISHED,
                ContentArticle.is_deleted.is_(False),
                ContentArticle.is_active.is_(True),
            )
            .order_by(ContentArticle.created_at.desc())
        )

        return list(result.scalars().all())

    @staticmethod
    async def get_published_articles_by_category(
        db: AsyncSession,
        category_id: str,
    ) -> List[ContentArticle]:

        result = await db.execute(
            select(ContentArticle).where(
                ContentArticle.category_id == category_id,
                ContentArticle.status == ContentStatus.PUBLISHED,
                ContentArticle.is_deleted.is_(False),
                ContentArticle.is_active.is_(True),
            )
            .order_by(ContentArticle.created_at.desc())
        )

        return list(result.scalars().all())

    @staticmethod
    async def get_published_article_by_slug(
        db: AsyncSession,
        slug: str,
    ) -> ContentArticle:

        result = await db.execute(
            select(ContentArticle).where(
                ContentArticle.slug == slug,
                ContentArticle.status == ContentStatus.PUBLISHED,
                ContentArticle.is_deleted.is_(False),
                ContentArticle.is_active.is_(True),
            )
        )

        article = result.scalar_one_or_none()

        if not article:
            raise NotFoundException(
                "Published content"
            )

        return article

    @staticmethod
    async def get_published_content_for_ai(
        db: AsyncSession,
        pathway_id: str,
    ) -> List[dict]:
        """
        Return published Content Engine information in a
        simple structure that future AI services can consume.

        This method does NOT call an AI provider.

        It simply retrieves trusted, published content.
        """

        articles = await ContentService.get_published_articles_by_pathway(
            db,
            pathway_id,
        )

        return [
            {
                "article_id": str(article.id),
                "category_id": str(article.category_id),
                "pathway_id": str(article.pathway_id),
                "title": article.title,
                "slug": article.slug,
                "summary": article.summary,
                "content": article.content,
                "version": article.version,
            }
            for article in articles
        ]