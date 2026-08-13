import tiktoken
from app.db.models import AsyncSessionLocal, Chunk, Document, DocumentStatus
from app.services.ingestion import chunk_document, extract_pages_from_pdf
from app.services.storage import storage_service
from sqlalchemy import select

tokenizer = tiktoken.get_encoding("cl100k_base")


async def process_document_ingestion(document_id: str) -> int:
    """
    Background task: Downloads file from MinIO, extracts text, creates chunks,
    and saves them in PostgreSQL.
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

            # 5. Mark document as COMPLETED
            document.status = DocumentStatus.COMPLETED
            await db.commit()

            return len(db_chunks)

        except Exception as e:
            await db.rollback()
            document.status = DocumentStatus.FAILED
            await db.commit()
            raise e
