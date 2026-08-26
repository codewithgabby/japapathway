# app/services/pathway.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.pathway import (
    ImmigrationPathway,
    RoadmapStep,
    UserRoadmap,
    UserRoadmapStep,
    PathwayStatus,
    StepStatus,
)

from app.core.exceptions import NotFoundException, BadRequestException


class PathwayService:

    # ============================================================
    # Admin: Pathway CRUD
    # ============================================================

    @staticmethod
    async def create_pathway(
        db: AsyncSession,
        data: dict,
        user_id: str,
    ) -> ImmigrationPathway:

        # Check slug uniqueness
        result = await db.execute(
            select(ImmigrationPathway).where(
                ImmigrationPathway.slug == data["slug"],
                ImmigrationPathway.is_deleted.is_(False),
            )
        )

        if result.scalar_one_or_none():
            raise BadRequestException(
                "Pathway with this slug already exists"
            )

        steps_data = data.get("steps", [])

        pathway_data = {
            key: value
            for key, value in data.items()
            if key != "steps"
        }

        pathway = ImmigrationPathway(
            **pathway_data,
            created_by=user_id,
            updated_by=user_id,
        )

        db.add(pathway)

        await db.flush()

        # Create steps if provided
        for step_data in steps_data:
            step = RoadmapStep(
                pathway_id=pathway.id,
                created_by=user_id,
                updated_by=user_id,
                **step_data,
            )

            db.add(step)

        await db.flush()

        return pathway

    @staticmethod
    async def get_pathway_by_id(
        db: AsyncSession,
        pathway_id: str,
    ) -> ImmigrationPathway:

        result = await db.execute(
            select(ImmigrationPathway).where(
                ImmigrationPathway.id == pathway_id,
                ImmigrationPathway.is_deleted.is_(False),
            )
        )

        pathway = result.scalar_one_or_none()

        if not pathway:
            raise NotFoundException("Pathway")

        return pathway

    @staticmethod
    async def get_pathway_by_slug(
        db: AsyncSession,
        slug: str,
    ) -> ImmigrationPathway:

        result = await db.execute(
            select(ImmigrationPathway).where(
                ImmigrationPathway.slug == slug,
                ImmigrationPathway.is_deleted.is_(False),
            )
        )

        pathway = result.scalar_one_or_none()

        if not pathway:
            raise NotFoundException("Pathway")

        return pathway

    @staticmethod
    async def get_all_pathways(
        db: AsyncSession,
        country: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[ImmigrationPathway]:

        query = select(ImmigrationPathway).where(
            ImmigrationPathway.is_deleted.is_(False)
        )

        if country:
            query = query.where(
                ImmigrationPathway.country == country
            )

        if category:
            query = query.where(
                ImmigrationPathway.category == category
            )

        if status:
            query = query.where(
                ImmigrationPathway.status == status
            )

        if not include_inactive:
            query = query.where(
                ImmigrationPathway.is_active.is_(True)
            )

        query = query.order_by(
            ImmigrationPathway.sort_order
        )

        result = await db.execute(query)

        return result.scalars().all()

    @staticmethod
    async def update_pathway(
        db: AsyncSession,
        pathway_id: str,
        data: dict,
        user_id: str,
    ) -> ImmigrationPathway:

        pathway = await PathwayService.get_pathway_by_id(
            db,
            pathway_id,
        )

        # Check slug uniqueness if changing
        if "slug" in data and data["slug"] != pathway.slug:

            result = await db.execute(
                select(ImmigrationPathway).where(
                    ImmigrationPathway.slug == data["slug"],
                    ImmigrationPathway.id != pathway_id,
                    ImmigrationPathway.is_deleted.is_(False),
                )
            )

            if result.scalar_one_or_none():
                raise BadRequestException(
                    "Pathway with this slug already exists"
                )

        for key, value in data.items():
            setattr(pathway, key, value)

        pathway.updated_by = user_id
        pathway.version += 1

        await db.flush()

        return pathway

    @staticmethod
    async def change_pathway_status(
        db: AsyncSession,
        pathway_id: str,
        status: str,
        user_id: str,
    ) -> ImmigrationPathway:

        pathway = await PathwayService.get_pathway_by_id(
            db,
            pathway_id,
        )

        try:
            pathway.status = PathwayStatus(status)

        except ValueError:
            raise BadRequestException(
                f"Invalid pathway status: {status}"
            )

        pathway.updated_by = user_id

        await db.flush()

        return pathway

    @staticmethod
    async def delete_pathway(
        db: AsyncSession,
        pathway_id: str,
        user_id: str,
    ) -> None:

        pathway = await PathwayService.get_pathway_by_id(
            db,
            pathway_id,
        )

        pathway.soft_delete(user_id)

        await db.flush()

    @staticmethod
    async def get_pathways_count(
        db: AsyncSession,
    ) -> int:

        from sqlalchemy import func

        result = await db.execute(
            select(
                func.count(ImmigrationPathway.id)
            ).where(
                ImmigrationPathway.is_deleted.is_(False)
            )
        )

        return result.scalar_one()

    # ============================================================
    # Admin: Step CRUD
    # ============================================================

    @staticmethod
    async def add_step(
        db: AsyncSession,
        pathway_id: str,
        data: dict,
        user_id: str,
    ) -> RoadmapStep:

        # Validate pathway exists
        await PathwayService.get_pathway_by_id(
            db,
            pathway_id,
        )

        # Get current highest step order
        result = await db.execute(
            select(RoadmapStep)
            .where(
                RoadmapStep.pathway_id == pathway_id,
                RoadmapStep.is_deleted.is_(False),
            )
            .order_by(
                RoadmapStep.step_order.desc()
            )
            .limit(1)
        )

        last_step = result.scalar_one_or_none()

        next_order = (
            last_step.step_order + 1
            if last_step
            else 1
        )

        step = RoadmapStep(
            pathway_id=pathway_id,
            step_order=data.get(
                "step_order",
                next_order,
            ),
            created_by=user_id,
            updated_by=user_id,
            **{
                key: value
                for key, value in data.items()
                if key not in {
                    "step_order",
                    "pathway_id",
                }
            },
        )

        db.add(step)

        await db.flush()

        return step

    @staticmethod
    async def get_step(
        db: AsyncSession,
        step_id: str,
    ) -> RoadmapStep:

        result = await db.execute(
            select(RoadmapStep).where(
                RoadmapStep.id == step_id,
                RoadmapStep.is_deleted.is_(False),
            )
        )

        step = result.scalar_one_or_none()

        if not step:
            raise NotFoundException("Step")

        return step

    @staticmethod
    async def get_pathway_steps(
        db: AsyncSession,
        pathway_id: str,
    ) -> List[RoadmapStep]:

        # Validate pathway exists
        await PathwayService.get_pathway_by_id(
            db,
            pathway_id,
        )

        result = await db.execute(
            select(RoadmapStep)
            .where(
                RoadmapStep.pathway_id == pathway_id,
                RoadmapStep.is_deleted.is_(False),
            )
            .order_by(
                RoadmapStep.step_order
            )
        )

        return result.scalars().all()

    @staticmethod
    async def update_step(
        db: AsyncSession,
        step_id: str,
        data: dict,
        user_id: str,
    ) -> RoadmapStep:

        step = await PathwayService.get_step(
            db,
            step_id,
        )

        for key, value in data.items():
            setattr(step, key, value)

        step.updated_by = user_id

        await db.flush()

        return step

    @staticmethod
    async def delete_step(
        db: AsyncSession,
        step_id: str,
        user_id: str,
    ) -> None:

        step = await PathwayService.get_step(
            db,
            step_id,
        )

        step.soft_delete(user_id)

        await db.flush()

    @staticmethod
    async def reorder_steps(
        db: AsyncSession,
        pathway_id: str,
        steps_order: List[dict],
        user_id: str,
    ) -> List[RoadmapStep]:

        # Make sure the pathway exists
        pathway = await PathwayService.get_pathway_by_id(
            db,
            pathway_id,
        )

        # Normalize pathway ID to string.
        # FastAPI receives the path parameter as a string,
        # while SQLAlchemy/PostgreSQL may return UUID objects.
        pathway_id_str = str(pathway.id)

        for item in steps_order:

            step = await PathwayService.get_step(
                db,
                item["step_id"],
            )

            # Normalize both IDs before comparing.
            # This prevents UUID-vs-string comparison failures.
            step_pathway_id_str = str(step.pathway_id)

            if step_pathway_id_str != pathway_id_str:
                raise BadRequestException(
                    "Step does not belong to this pathway"
                )

            step.step_order = item["new_order"]
            step.updated_by = user_id

        await db.flush()

        return await PathwayService.get_pathway_steps(
            db,
            pathway_id,
        )