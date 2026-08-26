import asyncio
from sqlalchemy import text
from app.db.session import engine

async def clean():
    async with engine.begin() as conn:
        await conn.execute(text('DELETE FROM applicant_document_responses'))
        await conn.execute(text('DELETE FROM applicant_document_drafts'))
        await conn.execute(text('DELETE FROM applicant_document_relationships'))
        await conn.execute(text('DELETE FROM applicant_documents'))
    print('Test documents cleared')

asyncio.run(clean())