import asyncio
from sqlalchemy import text
from app.db.session import engine


async def add_columns():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                ALTER TABLE applicant_document_drafts
                ADD COLUMN IF NOT EXISTS generation_status VARCHAR(50)
                DEFAULT 'generated'
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE applicant_document_drafts
                ADD COLUMN IF NOT EXISTS missing_information JSONB
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE applicant_document_drafts
                ADD COLUMN IF NOT EXISTS warnings JSONB
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE applicant_document_drafts
                ADD COLUMN IF NOT EXISTS knowledge_sources JSONB
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE applicant_document_drafts
                ADD COLUMN IF NOT EXISTS source_draft_id UUID
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE applicant_document_drafts
                ADD COLUMN IF NOT EXISTS generation_metadata JSONB
                """
            )
        )

    print("Sprint 6 database columns added successfully.")


if __name__ == "__main__":
    asyncio.run(add_columns())