import asyncio

import tiktoken
from app.db.models import AsyncSessionLocal, Chunk, Document, DocumentStatus
from app.services.embeddings import embedding_client
from app.services.ingestion import chunk_document, extract_pages_from_pdf
from app.services.storage import storage_service
from app.services.vector_store import vector_store
from sqlalchemy import select

tokenizer = tiktoken.get_encoding("cl100k_base")


async def process_document_ingestion(document_id: str) -> int:
    """
    Background task: Downloads file, extracts text, chunks it,
    saves to PostgreSQL, generates embeddings, and stores them in Pinecone.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            return 0

        try:
            # 1. Update status to PROCESSING
            document.status = DocumentStatus.PROCESSING
            await db.commit()

            # 2. Download file bytes from MinIO
            file_bytes = storage_service.get_file_bytes(document.object_name)

            # 3. Extract pages & split into token chunks
            pages = extract_pages_from_pdf(file_bytes)
            chunks = chunk_document(pages)

            # 4. Create Chunk database entities
            db_chunks = []
            for idx, chunk in enumerate(chunks):
                token_count = len(tokenizer.encode(chunk.page_content))
                page_num = chunk.metadata.get("page_number")

                db_chunk = Chunk(
                    document_id=document.id,
                    tenant_id=document.tenant_id,
                    text_content=chunk.page_content,
                    page_number=page_num,
                    chunk_index=idx,
                    token_count=token_count,
                )
                db_chunks.append(db_chunk)

            db.add_all(db_chunks)

            # Flush sends the insert statements to Postgres to generate the UUIDs
            # for each chunk, but DOES NOT commit the transaction yet.
            await db.flush()

            if db_chunks:
                # 5. Generate AI Embeddings
                texts_to_embed = [chunk.text_content for chunk in db_chunks]

                # We use asyncio.to_thread to run synchronous network calls without
                # blocking the main FastAPI asynchronous event loop!
                embeddings = await asyncio.to_thread(
                    embedding_client.embed_texts, texts_to_embed
                )

                # 6. Store Vectors in Pinecone
                await asyncio.to_thread(
                    vector_store.upsert_chunks,
                    str(document.tenant_id),
                    db_chunks,
                    embeddings,
                )

            # 7. Finalize and mark document as COMPLETED
            document.status = DocumentStatus.COMPLETED
            await db.commit()

            return len(db_chunks)

        except Exception as e:
            await db.rollback()
            document.status = DocumentStatus.FAILED
            await db.commit()
            raise e
