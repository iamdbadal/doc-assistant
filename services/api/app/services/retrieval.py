import asyncio
from typing import List

from app.models.rag import SourceCitation
from app.services.embeddings import embedding_client
from app.services.vector_store import vector_store


class RetrievalService:
    def __init__(self):
        # We rely on your existing lazy-loaded properties!
        self.cohere_client = embedding_client.client
        self.pinecone_index = vector_store.index

    async def get_query_embedding(self, query: str) -> List[float]:
        """Embeds query using Cohere v3 with search_query input_type."""

        def _embed():
            response = self.cohere_client.embed(
                texts=[query],
                model="embed-english-v3.0",
                input_type="search_query",
            )
            return response.embeddings[0]

        return await asyncio.to_thread(_embed)

    async def retrieve_chunks(
        self, query: str, tenant_id: str, top_k: int = 5
    ) -> List[SourceCitation]:
        """Retrieves top-k chunks from Pinecone within the tenant namespace."""
        query_vector = await self.get_query_embedding(query)

        def _query_vector_db():
            return self.pinecone_index.query(
                vector=query_vector,
                namespace=tenant_id,
                top_k=top_k,
                include_metadata=True,
            )

        result = await asyncio.to_thread(_query_vector_db)

        sources: List[SourceCitation] = []
        for match in result.get("matches", []):
            metadata = match.get("metadata", {})
            sources.append(
                SourceCitation(
                    chunk_id=match.get("id", ""),
                    doc_id=metadata.get("doc_id", "unknown"),
                    score=float(match.get("score", 0.0)),
                    text=metadata.get("text", ""),
                )
            )
        return sources
