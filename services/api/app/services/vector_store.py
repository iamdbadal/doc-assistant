from app.db.models import Chunk
from app.settings import settings
from pinecone import Pinecone  # type: ignore


class VectorStoreService:
    def __init__(self):
        if not settings.pinecone_api_key or not settings.pinecone_index:
            raise ValueError(
                "Pinecone configuration (API key or Index name) is missing."
            )

        # Initialize the Pinecone SDK V3 client
        self.pc = Pinecone(api_key=settings.pinecone_api_key.get_secret_value())

        # Connect to your specific index
        self.index = self.pc.Index(settings.pinecone_index)

    def upsert_chunks(
        self, tenant_id: str, chunks: list[Chunk], embeddings: list[list[float]]
    ) -> int:
        """
        Pairs database chunks with their embeddings and uploads them to Pinecone.
        Uses the tenant_id as the namespace for strict data isolation.
        """
        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings"
            )

        # Format the data exactly how Pinecone expects it
        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            vectors.append(
                {
                    "id": str(chunk.id),
                    "values": embedding,
                    "metadata": {
                        "doc_id": str(chunk.document_id),
                        "chunk_id": str(chunk.id),
                        "page_number": (
                            chunk.page_number if chunk.page_number is not None else 0
                        ),
                        "chunk_index": chunk.chunk_index,
                        # We store the text directly in Pinecone metadata!
                        # This allows the AI to fetch the text instantly without doing
                        # a second lookup to PostgreSQL later.
                        "text": chunk.text_content,
                    },
                }
            )

        # Pinecone recommends sending vectors in batches (e.g., 100 at a time)
        batch_size = 100
        upserted_count = 0

        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]

            # The 'namespace' parameter is crucial here for Multi-Tenant architecture
            self.index.upsert(vectors=batch, namespace=tenant_id)
            upserted_count += len(batch)

        return upserted_count


vector_store = VectorStoreService()
