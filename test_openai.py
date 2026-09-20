import asyncio

from openai import AsyncOpenAI
from app.core.config import settings


async def main():
    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY
    )

    response = await client.responses.create(
        model=settings.OPENAI_MODEL,
        input="Reply with exactly: JapaPathway API test successful",
    )

    print(response.output_text)


if __name__ == "__main__":
    asyncio.run(main())