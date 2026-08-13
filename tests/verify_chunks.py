import asyncio
import os
import sys

# Tell Python to look inside the services/api folder for the 'app' module
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "services", "api"))

from app.db.models import AsyncSessionLocal, Chunk
from sqlalchemy import select


async def verify_chunks():
    print("🔍 Fetching extracted chunks from PostgreSQL...\n")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Chunk))
        chunks = result.scalars().all()

        if not chunks:
            print("⚠️ No chunks found in the database.")
            return

        for idx, chunk in enumerate(chunks, 1):
            print(f"--- Chunk {idx} ---")
            print(f"📄 Document ID: {chunk.document_id}")
            print(f"📑 Page Number: {chunk.page_number}")
            print(f"🔢 Token Count: {chunk.token_count}")
            print(f"📝 Extracted Text: {chunk.text_content}")
            print("-" * 40 + "\n")


if __name__ == "__main__":
    asyncio.run(verify_chunks())
