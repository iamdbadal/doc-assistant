from app.db.models import Chunk
from app.settings import settings
from pinecone import Pinecone  # type: ignore


class VectorStoreService:
    def __init__(self):
        self._pc = None
        self._index = None

    @property
    def index(self):
        """Lazy initialization: Only connect to Pinecone when we actually need it."""
        if not self._index:
            if not settings.pinecone_api_key or not settings.pinecone_index:
                raise ValueError("Pinecone configuration is missing.")

            self._pc = Pinecone(api_key=settings.pinecone_api_key.get_secret_value())
            self._index = self._pc.Index(settings.pinecone_index)
        return self._index

    def upsert_chunks(
        self, tenant_id: str, chunks: list[Chunk], embeddings: list[list[float]]
    ) -> int:
        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings"
            )

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
                        "text": chunk.text_content,
                    },
                }
            )

        batch_size = 100
        upserted_count = 0

        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            # Notice we use self.index here!
            self.index.upsert(vectors=batch, namespace=tenant_id)
            upserted_count += len(batch)

        return upserted_count


vector_store = VectorStoreService()
